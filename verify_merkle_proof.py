#!/usr/bin/env python3
"""
VERIFY AN HSH MERKLE PROOF — the reference implementation.

This file is for YOU, the buyer. It is a complete implementation of the
instructions HSH publishes with every proof, and it is deliberately small
enough to read in a few minutes before you run it.

  * It imports NOTHING from HSH. Standard library only — `hashlib`, `json`,
    `argparse`, `sys`. If it imported our code it would prove nothing: code
    agreeing with itself is a tautology, and that is exactly how the first
    version of our instructions came to be wrong for weeks while every one of
    our own tests passed.
  * It talks to nothing. You give it a proof and a root; it does arithmetic.
  * It answers one question: was this record in that day's batch, and has it
    changed since.

TWO ALGORITHMS (LAW 417)
------------------------
We have published under two, and both remain valid for the days they were
published on. Every proof and every root row names its own in an `algo`
field, and this file implements both:

    sha256-carry-v1     joins hashes as 64-char hex TEXT, no domain
                        separation byte, and CARRIES an odd node up
                        unchanged. Published on 2026-08-13 to 2026-08-21.
    sha256-rfc6962-v2   RFC 6962 section 2.1. Joins RAW BYTES, prefixes
                        0x00 before a leaf and 0x01 before an interior node,
                        and splits at the largest power of two strictly less
                        than the count — no carry rule, because the split is
                        uneven by construction. In use from 2026-08-22.

They produce DIFFERENT leaves and DIFFERENT roots for the same records, and
that is correct — they are different commitments. Running the wrong one
against a day is not a small error: it produces a completely different root,
which reads exactly like tampering. So this file refuses to guess. If it is
handed a proof whose algorithm it does not implement it exits 3 and says so;
it will never report NOT VERIFIED on the strength of arithmetic it knows to
be the wrong arithmetic.

USAGE

  Verify one record, from a saved proof and the published root. The proof's
  own `algo` field selects the arithmetic:

      curl -s https://api.hshintelligence.com/v1/filings/<identity>/proof \
           > proof.json

      # the ROOT comes from the PUBLIC log, not from us — a root we
      # hand you alongside the data is a number you are trusting us
      # for twice:
      curl -s https://raw.githubusercontent.com/hshintelligence/\
hsh-transparency/main/ROOTS.jsonl > roots.jsonl
      python3 verify_merkle_proof.py --proof proof.json --roots roots.json

  Recompute a whole day's root from the records you hold — the only check
  that can detect a forged TREE rather than a changed record:

      python3 verify_merkle_proof.py --records day.jsonl \\
              --expect 7cb336e73086977a2276958bd6ce5c85a235fea3c9edd6aecb0f54c916c325cd

  where day.jsonl has one JSON object per line with `identity`,
  `content_hash` and `bronze_key`. With no --algo it computes the root under
  BOTH algorithms and tells you which one your expected value is, if either.

  Check the arithmetic against both published worked examples, offline:

      python3 verify_merkle_proof.py --selftest

EXIT CODES
  0  verified
  1  NOT verified — the computed value does not match
  2  the input could not be read
  3  the proof names an algorithm this file does not implement. This is NOT
     a verification failure; do not read it as one.

If this file disagrees with HSH's published instructions, the INSTRUCTIONS
are what we are bound by; tell us and we will fix one of the two.
"""
import argparse
import hashlib
import json
import sys

V1 = "sha256-carry-v1"
V2 = "sha256-rfc6962-v2"

# ── v1: the conventions (C1-C5) ─────────────────────────────────────────────
# C1  a hash is the lowercase 64-character hex digest, never raw bytes
# C2  hashes are joined AS TEXT, not as decoded bytes
# C3  text is encoded UTF-8 before hashing
# C5  sha256(x) = hash the UTF-8 bytes of x, write the digest as lowercase hex
NUL = "\x00"                      # C4: ONE byte, value zero


def sha256_text(text):
    """v1 C1 + C2 + C3 + C5, in one place."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def payload_of(identity, content_hash, bronze_key):
    """The leaf payload. Identical text in both algorithms."""
    return identity + NUL + content_hash + NUL + bronze_key


def v1_leaf(identity, content_hash, bronze_key):
    """v1 L1. leaf = sha256(identity + NUL + content_hash + NUL + bronze_key)"""
    return sha256_text(payload_of(identity, content_hash, bronze_key))


def v1_root(records):
    """
    v1 B1-B6. Returns (root, level_sizes).

    B1  sort by identity, ascending, raw text
    B2  level 0 is the leaves in that order
    B3  parent = sha256(left + right), pairs left to right
    B4  an odd last node is CARRIED UP UNCHANGED — never duplicated
    B5  repeat until one node remains
    B6  one record: the root is its leaf
    """
    ordered = sorted(records, key=lambda r: r["identity"])            # B1
    level = [v1_leaf(r["identity"], r["content_hash"], r["bronze_key"])
             for r in ordered]                                        # B2
    if not level:
        raise ValueError("no records: an empty day has no root")
    sizes = [len(level)]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level) - 1, 2):
            nxt.append(sha256_text(level[i] + level[i + 1]))          # B3
        if len(level) % 2:
            nxt.append(level[-1])                                     # B4 CARRY
        level = nxt
        sizes.append(len(level))
    return level[0], sizes                                            # B5


def v1_fold(leaf, proof):
    """
    v1 V2. `side` is the side the SIBLING is on.
    V3. An empty proof means the leaf is already the root.
    V4. A proof may be shorter than log2(n): a carried node has no sibling at
        that level, so that level contributes no step.
    """
    h = leaf
    for step in proof:
        side, sibling = step["side"], step["hash"]
        if side == "left":
            h = sha256_text(sibling + h)
        elif side == "right":
            h = sha256_text(h + sibling)
        else:
            raise ValueError(f"unknown side {side!r}: expected left or right")
    return h


# ── v2: RFC 6962 section 2.1 ────────────────────────────────────────────────
# D1  join RAW BYTES, not hex text          D2  0x00 before a leaf, 0x01 before
# C2  decode the published hex to 32 bytes      an interior node
# D3  split at the largest power of two strictly less than n; NO carry rule


def v2_leaf(identity, content_hash, bronze_key):
    """v2 L1. leaf = sha256(0x00 + payload), as lowercase hex."""
    p = payload_of(identity, content_hash, bronze_key).encode("utf-8")
    return hashlib.sha256(b"\x00" + p).hexdigest()


def _v2_node(left_hex, right_hex):
    """v2 B4/V2. sha256(0x01 + left + right), on the DECODED bytes."""
    return hashlib.sha256(b"\x01" + bytes.fromhex(left_hex)
                          + bytes.fromhex(right_hex)).hexdigest()


def _v2_mth(leaves):
    """v2 B2-B4, recursive exactly as RFC 6962 states it."""
    if not leaves:
        return hashlib.sha256(b"").hexdigest()                        # B2
    if len(leaves) == 1:
        return leaves[0]                                              # B3
    k = 1
    while k * 2 < len(leaves):                                        # B4
        k *= 2
    return _v2_node(_v2_mth(leaves[:k]), _v2_mth(leaves[k:]))


def v2_root(records):
    """v2 B1-B4. Returns (root, [n, k]) — a v2 tree has no level sizes."""
    ordered = sorted(records, key=lambda r: r["identity"])            # B1
    leaves = [v2_leaf(r["identity"], r["content_hash"], r["bronze_key"])
              for r in ordered]
    if not leaves:
        raise ValueError("no records: an empty day has no root")
    k = 1
    while k * 2 < len(leaves):
        k *= 2
    return _v2_mth(leaves), [len(leaves), k if len(leaves) > 1 else 0]


def v2_fold(leaf, proof):
    """v2 V1-V3. Same `side` convention as v1; different arithmetic."""
    h = leaf
    for step in proof:
        side, sibling = step["side"], step["hash"]
        if side == "left":
            h = _v2_node(sibling, h)
        elif side == "right":
            h = _v2_node(h, sibling)
        else:
            raise ValueError(f"unknown side {side!r}: expected left or right")
    return h


ALGOS = {
    V1: {"leaf": v1_leaf, "root": v1_root, "fold": v1_fold},
    V2: {"leaf": v2_leaf, "root": v2_root, "fold": v2_fold},
}


def verify_proof(record, proof, published_root, algo):
    """V1-V5, under the named algorithm. Returns (ok, computed)."""
    impl = ALGOS[algo]
    leaf = impl["leaf"](record["identity"], record["content_hash"],
                        record["bronze_key"])
    if record.get("leaf") and record["leaf"] != leaf:
        # Not fatal — but it means the conventions went wrong and everything
        # after it will be wrong too, so say it here rather than at the root.
        # Under the wrong ALGORITHM this is the first place you see it.
        print(f"  WARNING: our leaf {leaf}\n"
              f"           differs from the one in the proof "
              f"{record['leaf']}\n"
              f"           you may be running {algo} against a proof from "
              f"the other algorithm", file=sys.stderr)
    computed = impl["fold"](leaf, proof)
    return computed == published_root, computed


# ── the published worked examples ───────────────────────────────────────────
# One per algorithm. Both are real records from real published days, and both
# appear in the instructions HSH publishes — if this file and that text ever
# disagree, the text is what we are bound by.
WORKED = {
    V1: {
        "day": "2026-08-13",
        "identity": "sec_edgar:1004724:000119312526346993:8277c96a4e320691",
        "content_hash": "8277c96a4e320691e474082bbb9e361d",
        "bronze_key":
            "bronze/sec_edgar/82/8277c96a4e320691e474082bbb9e361d.zst",
        "leaf":
            "3588593755cbf9da03a5a089533a6ac79d9f0ef0e9440f3ff319817857cd2fe7",
        "second_leaf":
            "1888f5a7d2acfad4e4592a77958f607af2bcf3b13cc8d76a13e18b1a4f72134f",
        "parent_of_first_two":
            "86a3940a64134698a3baa7b78ee55b33d7a6aa85c8ece66a860b256c02a524d8",
    },
    V2: {
        "day": "2026-08-22",
        "identity": "sec_edgar:1000697:000119312526360081:4ae3a19debbd1679",
        "content_hash": "4ae3a19debbd16799e9873d61613109a",
        "bronze_key":
            "bronze/sec_edgar/4a/4ae3a19debbd16799e9873d61613109a.zst",
        "leaf":
            "bd026d3d671f3564da33ba09ed76e7bcbdf8dcde82e33c5616a5994c79111882",
        "second_leaf":
            "f90ffd76e16047e64fd568346dcbf14ac5b14e269df2a3dffec3f3e37c8f3cb1",
        "parent_of_first_two":
            "9ae2f04d6efeff5bf6c3fe6382286cae1810604a67dc72e8f1e30b2353eff1af",
    },
}


def selftest():
    """
    Check this file against the published worked example FOR EACH ALGORITHM.
    Offline, and it takes a millisecond. If either fails, the arithmetic here
    does not match what HSH published and nothing else in this file can be
    trusted for that algorithm.
    """
    ok = True
    for algo in (V1, V2):
        w = WORKED[algo]
        print(f"\n  {algo}  (worked example from {w['day']})")
        leaf = ALGOS[algo]["leaf"](w["identity"], w["content_hash"],
                                   w["bronze_key"])
        print(f"    leaf              {leaf}")
        print(f"    published as      {w['leaf']}")
        if leaf != w["leaf"]:
            ok = False
            print("    LEAF DOES NOT MATCH — check the NUL byte (one byte of "
                  "value zero, not four characters) and, for v2, the 0x00 "
                  "prefix")
        if algo == V1:
            parent = sha256_text(w["leaf"] + w["second_leaf"])
            hint = "check C2 — join the hex TEXT, do not decode it"
        else:
            parent = _v2_node(w["leaf"], w["second_leaf"])
            hint = ("check C2 — DECODE the hex to bytes before joining, and "
                    "prefix 0x01")
        print(f"    parent            {parent}")
        print(f"    published as      {w['parent_of_first_two']}")
        if parent != w["parent_of_first_two"]:
            ok = False
            print(f"    PARENT DOES NOT MATCH — {hint}")

    # The two algorithms must disagree about the same record. If they agree,
    # one of them is not implemented here and the dispatch below is decorative.
    a = v1_leaf("i", "c", "b")
    b = v2_leaf("i", "c", "b")
    print(f"\n  v1 and v2 leaves differ for the same record: {a != b}")
    if a == b:
        ok = False
        print("    THEY MUST DIFFER — v2 prefixes 0x00 and v1 does not")

    # B4, shown rather than described: v1 carries an odd level's last node.
    three = ["a" * 64, "b" * 64, "c" * 64]
    carried = sha256_text(sha256_text(three[0] + three[1]) + three[2])
    duplicated = sha256_text(sha256_text(three[0] + three[1])
                             + sha256_text(three[2] + three[2]))
    print(f"  v1 carry vs duplicate differ: {carried != duplicated}")
    if carried == duplicated:
        ok = False

    # v2 D3: for n=3 the split is 2+1, NOT a carry and NOT 1+2.
    lv = ["a" * 64, "b" * 64, "c" * 64]
    split = _v2_node(_v2_node(lv[0], lv[1]), lv[2])
    print(f"  v2 splits 3 as 2+1: {_v2_mth(lv) == split}")
    if _v2_mth(lv) != split:
        ok = False
    return ok


def _algo_of(doc, override, where):
    """
    Pick the arithmetic, and REFUSE rather than guess. An unrecognised algo
    is exit 3, never a NOT VERIFIED: telling a buyer their records do not
    match when we simply did not implement their algorithm is the worst
    answer this file could give.
    """
    algo = (override or doc.get("algo") or "").strip()
    if not algo:
        # Proofs issued before the field existed are all v1 — there was only
        # one algorithm then.
        print(f"  {where} carries no `algo` field; assuming {V1}, which was "
              f"the only algorithm published before 2026-08-22.",
              file=sys.stderr)
        return V1
    if algo not in ALGOS:
        print(f"NOT CHECKED — {where} names algorithm {algo!r}, which this "
              f"file does not implement. It implements {sorted(ALGOS)}. This "
              f"is NOT a verification failure: obtain a newer copy of this "
              f"file from GET /v1/merkle/instructions, or the procedure "
              f"itself from the same endpoint with ?algo={algo}.",
              file=sys.stderr)
        return None
    return algo


def main():
    ap = argparse.ArgumentParser(
        description="Verify an HSH Merkle proof. Imports nothing from HSH.")
    ap.add_argument("--proof", help="a proof, as returned by "
                                    "/v1/filings/<identity>/proof")
    ap.add_argument("--roots", help="the published roots, from "
                                    "/v1/merkle/roots")
    ap.add_argument("--records", help="JSONL of a day's records, to recompute "
                                      "the whole root")
    ap.add_argument("--expect", help="the published root to compare against")
    ap.add_argument("--algo", choices=sorted(ALGOS),
                    help="force an algorithm. Normally taken from the "
                         "`algo` field of the proof or the roots file.")
    ap.add_argument("--selftest", action="store_true",
                    help="check this file against the published worked "
                         "examples, offline")
    a = ap.parse_args()

    if a.selftest:
        print("SELF-TEST against the published worked examples")
        ok = selftest()
        print("\nOK" if ok else "\nFAILED")
        return 0 if ok else 1

    if a.records:
        try:
            with open(a.records) as fh:
                records = [json.loads(l) for l in fh if l.strip()]
        except Exception as e:
            print(f"could not read {a.records}: {e}", file=sys.stderr)
            return 2
        wanted = [a.algo] if a.algo else sorted(ALGOS)
        print(f"records           {len(records)}")
        hits = []
        for algo in wanted:
            root, sizes = ALGOS[algo]["root"](records)
            mark = ""
            if a.expect and root == a.expect:
                mark, hits = "   <-- matches --expect", hits + [algo]
            shape = ("level sizes " + str(sizes) if algo == V1
                     else f"n={sizes[0]} k={sizes[1]}")
            print(f"  {algo:20} {root}{mark}")
            print(f"  {'':20} {shape}")
        if not a.expect:
            return 0
        print(f"published root    {a.expect}")
        if hits:
            print(f"VERIFIED under {hits[0]} — this set of records produces "
                  f"the published root")
            return 0
        print("NOT VERIFIED — the records you hold do not produce the "
              "published root under " + (a.algo or "EITHER published "
                                                  "algorithm"))
        return 1

    if not a.proof:
        ap.error("give --proof, or --records, or --selftest")
    try:
        with open(a.proof) as fh:
            p = json.load(fh)
    except Exception as e:
        print(f"could not read {a.proof}: {e}", file=sys.stderr)
        return 2

    algo = _algo_of(p, a.algo, "the proof")
    if algo is None:
        return 3

    published = p.get("published_root", "")
    if a.roots:
        try:
            with open(a.roots) as fh:
                doc = json.load(fh)
            for r in doc.get("roots", doc if isinstance(doc, list) else []):
                if r.get("day") == p.get("day"):
                    published = r.get("root", published)
                    # The ROOT ROW is authoritative about its own algorithm:
                    # the proof describes what we would compute today, the
                    # row describes what we committed to on the day.
                    if not a.algo and r.get("algo"):
                        row = _algo_of(r, None, f"the published root for "
                                                f"{r.get('day')}")
                        if row is None:
                            return 3
                        if row != algo:
                            print(f"  note: the proof says {algo} and the "
                                  f"published root row says {row}; using the "
                                  f"root row.", file=sys.stderr)
                        algo = row
        except Exception as e:
            print(f"could not read {a.roots}: {e}", file=sys.stderr)
            return 2
    if not published:
        print("NOT VERIFIED — no PUBLISHED root for "
              f"{p.get('day')!r}. Per T3, a record retrieved today has no "
              f"published root until the day ends, and such a proof "
              f"establishes nothing yet.", file=sys.stderr)
        return 1

    record = {k: p.get(k, "") for k in
              ("identity", "content_hash", "bronze_key")}
    if not all(record.values()):
        print("the proof does not carry identity, content_hash and "
              "bronze_key; fetch them from GET /v1/filings", file=sys.stderr)
        return 2
    ok, computed = verify_proof({**record, "leaf": p.get("leaf", "")},
                                p.get("proof", []), published, algo)
    print(f"identity          {record['identity']}")
    print(f"day               {p.get('day')}")
    print(f"algorithm         {algo}")
    print(f"proof steps       {len(p.get('proof', []))}")
    print(f"computed          {computed}")
    print(f"published root    {published}")
    print("VERIFIED" if ok else "NOT VERIFIED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
