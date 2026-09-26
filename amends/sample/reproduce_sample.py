#!/usr/bin/env python3
"""REBUILD THE HSH AMENDS SAMPLE FROM THE RELEASE.

    python3 reproduce_sample.py /path/to/release/parquet/dir

The sample is a deterministic draw from `restatements-v1.6.0`. This script replays it
from SAMPLE-COMPOSITION.json — the same rules, the same ordering, the
same column list — and compares what it gets to the files in this
directory. It is the executable form of the sentence in README.md.

TWO VERDICTS, AND THEY ARE DIFFERENT CLAIMS.

  ROW SET     the draw itself. Depends only on the release and the
              published rules. If this fails, the sample is not the
              draw we describe.
  BYTE-EXACT  the row set PLUS the CSV writer. Reproducing our bytes
              additionally needs duckdb 1.5.1, which is what
              wrote them. A different duckdb may quote an embedded
              newline differently and still hold identical rows, so a
              row-set PASS with a byte MISMATCH is a writer difference,
              not a data difference.

Requires: duckdb. Nothing else.
"""
import duckdb, hashlib, json, os, sys, tempfile

d = os.path.dirname(os.path.abspath(__file__))
rel = sys.argv[1] if len(sys.argv) > 1 else "."
comp = json.load(open(os.path.join(d, "SAMPLE-COMPOSITION.json")))
# NAME THE SPLIT FILES, DO NOT WILDCARD THE RELEASE ID. A release id can
# be a PREFIX of another release id, so a wildcard on the id also matches
# a neighbouring build sitting in the same directory, and every row is
# read twice. Measured 2026-09-23 on a 15,392,754-row release: a wildcard
# read 30,785,508 rows, because a second build was beside it.
files = [f for f in (os.path.join(rel, "restatements-v1.6.0-%s.parquet" % _s)
                     for _s in ("train", "validation", "test", "reference"))
         if os.path.exists(f)]
assert files, "no parquet files for restatements-v1.6.0 in %s" % rel

con = duckdb.connect()
con.execute("SET memory_limit='5GB'")
con.execute("SET threads=3")
# The column list and its ORDER come from the published composition —
# the same dict the sample was exported with, so it cannot drift.
sel = ", ".join('"%s"' % c for c in comp["col_types"])
assert len(comp["col_types"]) == 19, "column list changed"

con.execute(f"""CREATE VIEW rel AS SELECT *,
            json_extract_string(payload,'$.link_state') AS ls,
            json_extract_string(payload,'$.base_form') AS bf,
            json_extract_string(payload,'$.amends_identity') AS chain,
            CAST(substr(CAST(filed_at AS VARCHAR), 1, 4) AS INT) AS yr
        FROM read_parquet({files})""")

n_rel = con.execute("SELECT count(*) FROM rel").fetchone()[0]
print(f"release      {n_rel:,} rows from {len(files)} file(s)")
if n_rel != comp["release_rows"]:
    print(f"  !! the release holds {n_rel:,} rows; this sample was drawn "
          f"from {comp['release_rows']:,}. Point at the right release.")
    sys.exit(2)

parts = []
for i, st in enumerate(comp["strata"]):
    lim = "" if st["target"] is None else "LIMIT %d" % st["in_sample"]
    con.execute(f"CREATE OR REPLACE TEMP VIEW r{i} AS SELECT * FROM rel "
                f"WHERE {st['rule']} ORDER BY md5(record_uid) {lim}")
    got = con.execute(f"SELECT count(*) FROM r{i}").fetchone()[0]
    flag = "ok" if got == st["in_sample"] else "MISMATCH"
    print(f"  {st['stratum']:44s} {got:>6,} / {st['in_sample']:<6,} {flag}")
    parts.append(f"SELECT * FROM r{i}")

con.execute("CREATE OR REPLACE TEMP TABLE sample AS "
            + " UNION ".join(parts))
# NOT into this directory — SHA256SUMS covers it, and a scratch file
# here would make the seal fail for as long as the script is running.
out = os.path.join(tempfile.mkdtemp(prefix="hsh-repro-"),
                   "reproduced-sample.csv")
con.execute("COPY (SELECT " + sel + " FROM sample ORDER BY md5(record_uid))"
            " TO '" + out + "' (FORMAT CSV, HEADER)")

def fingerprint(path):
    """Every FIELD of every row, not just the key.

    This compared `SELECT record_uid ... ORDER BY record_uid`. So any
    tampering that preserved the uid set — flipping a link_state from
    `linked` to `no_prior_filing_in_corpus`, rewriting a company_name —
    reproduced as ROW SET PASS with exit 0, on the single most
    load-bearing claim in the product.
    """
    cols = ", ".join('"%s"' % c for c in comp["col_types"])
    nulls = ", ".join('coalesce("' + c + '", chr(0))'
                      for c in comp["col_types"])
    return con.execute(
        "SELECT md5(string_agg(h, '' ORDER BY h)) FROM ("
        # duckdb's concat_ws SKIPS NULL ARGUMENTS, and an
        # empty unquoted CSV field reads as NULL, so fields shifted
        # across an empty column hash identically. coalesce() gives every
        # absent field a byte of its own, so position is preserved.
        "  SELECT md5(concat_ws(chr(31), " + nulls + ")) AS h"
        "  FROM read_csv_auto(?, header=true, all_varchar=true))",
        [path]).fetchone()[0]

pub = os.path.join(d, "hsh-amends-sample.csv")
same_rows = fingerprint(out) == fingerprint(pub)
h_new = hashlib.sha256(open(out, "rb").read()).hexdigest()
h_pub = hashlib.sha256(open(pub, "rb").read()).hexdigest()

print()
print(f"ROW SET      {'PASS' if same_rows else 'FAIL'}")
print(f"BYTE-EXACT   {'PASS' if h_new == h_pub else 'MISMATCH'}"
      f"   (yours {h_new[:16]} / ours {h_pub[:16]})")
if same_rows and h_new != h_pub:
    # Only offer the writer explanation when the writer could BE the
    # explanation. With identical duckdb versions it cannot, and the
    # first version of this printed a self-refuting sentence naming the
    # same version on both sides.
    if duckdb.__version__ != "1.5.1":
        print("             identical rows, different bytes — most likely a "
              "CSV writer difference. Your duckdb is", duckdb.__version__,
              "and ours was 1.5.1.")
    else:
        print("             every field of every row matches, but the bytes "
              "differ on the SAME duckdb version (1.5.1).")
        print("             That is not a writer difference. Treat it as "
              "unexplained and tell us what you have.")
os.remove(out); os.rmdir(os.path.dirname(out))
sys.exit(0 if same_rows else 1)
