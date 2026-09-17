#!/usr/bin/env python3
"""
HSH INTELLIGENCE — BUYER VERIFICATION KIT.   python3 verify.py --dir ./download

Four checks against a release you downloaded. Nothing here imports HSH code,
reaches an HSH server, or asks you to trust a document we wrote. Stdlib only,
except pyarrow for check 4 (see README).

WHY A PROGRAM AND NOT INSTRUCTIONS: our published Merkle instructions once
carried four ambiguities — hex vs raw concatenation, the separator, the
ordering, the odd-node rule — each producing a DIFFERENT root. Following that
prose you would have computed a mismatch and concluded we tampered. Prose can
be misread; code cannot. This is the spec.
"""
import argparse, hashlib, json, os, sys

MARK = {True: "PASS", False: "FAIL", None: "NOT CHECKED"}
NUL = "\x00"
V1, V2 = "sha256-carry-v1", "sha256-rfc6962-v2"
BLOCK = 1 << 20          # 1 MiB: a 366 MB file must never be read whole


def sha256_file(path):
    """Block-wise, so memory does not scale with the file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(BLOCK), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(path):
    """Header lines, blank line, then '<record_uid>  <payload_sha>'.
    `file_hashes` is EMPTY for releases predating the file-hash header — not
    a pass: check 1 reports NOT CHECKED rather than OK."""
    meta, files = {}, {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#"):
                break
            parts = line[1:].split()
            if parts and parts[0] == "file" and len(parts) >= 3:
                files[parts[1]] = parts[2].split("=", 1)[-1]
            elif len(parts) >= 2:
                meta[parts[0]] = " ".join(parts[1:])
    return meta, files


# ── 1. FILE INTEGRITY ───────────────────────────────────────────────────────
def check_files(d, files):
    if not files:
        return None, ["this manifest carries NO file hashes, so your bytes "
                      "cannot be checked against it. Nine live releases "
                      "predate the file-hash header; see README."]
    notes, ok = [], True
    for name, want in sorted(files.items()):
        p = os.path.join(d, name)
        if not os.path.exists(p):
            notes.append(f"{name}: NOT DOWNLOADED (manifest expects it)")
            ok = False
            continue
        got = sha256_file(p)
        notes.append(f"{name}: {'ok' if got == want else 'MISMATCH'}")
        if got != want:
            notes.append(f"    manifest {want}")
            notes.append(f"    yours    {got}")
            ok = False
    return ok, notes


# ── 2. MANIFEST INTEGRITY ───────────────────────────────────────────────────
def check_manifest(path, expected):
    """Catches a swapped manifest, which check 1 alone cannot."""
    if not expected:
        return None, ["no expected manifest_sha supplied (--release), so the "
                      "manifest itself is unchecked"]
    got = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if got == expected:
        return True, [f"manifest sha256 matches the published release record"]
    return False, ["MANIFEST MISMATCH — this is not the manifest we published",
                   f"    published {expected}", f"    yours     {got}"]


# ── 3. MERKLE MEMBERSHIP ────────────────────────────────────────────────────
def _v1_join(a, b):
    """v1 joins the 64-char hex STRINGS and hashes the UTF-8 of that."""
    return hashlib.sha256((a + b).encode("utf-8")).hexdigest()


def _v2_join(a, b):
    """v2 is RFC 6962: 0x01 then the two hashes as RAW BYTES."""
    return hashlib.sha256(b"\x01" + bytes.fromhex(a) + bytes.fromhex(b)).hexdigest()


def leaf_of(algo, identity, content_hash, bronze_key):
    payload = identity + NUL + content_hash + NUL + bronze_key
    if algo == V1:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return hashlib.sha256(b"\x00" + payload.encode("utf-8")).hexdigest()


def load_roots(path):
    """
    The published roots, as JSONL, from the PUBLIC log.

    LAW 509. This kit used to fold a proof and compare the result against
    `published_root` INSIDE THE PROOF — a number served by the same API that
    served the proof. That establishes that we are internally consistent and
    nothing else: you would be trusting us twice, once for the data and once
    for the value you check it against.

    The roots now come from a separate, public, append-only repository whose
    commit dates are recorded by GitHub:

        https://raw.githubusercontent.com/hshintelligence/hsh-transparency/main/ROOTS.jsonl

    Fetch it yourself, pass it with --roots, and check 3 becomes a statement
    about our data rather than about our consistency.
    """
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("root") and e.get("day"):
                out[str(e["day"])] = {"root": e["root"],
                                      "algo": e.get("algo")}
    return out


def check_merkle(proof, roots=None):
    """
    Fold the record's own leaf to the published root.

    THE LEAF IS RECOMPUTED, NOT TAKEN FROM THE PROOF. Folding the `leaf`
    field would prove SOME leaf is in the tree and say nothing about YOUR
    record. Recomputing it binds the two together.
    """
    algo = proof.get("algo")
    if algo not in (V1, V2):
        return False, [f"unknown algorithm {algo!r} — refusing to guess. Ask "
                       f"for GET /v1/merkle/instructions?algo={algo}"]
    join = _v1_join if algo == V1 else _v2_join
    leaf = leaf_of(algo, proof["identity"], proof["content_hash"],
                   proof["bronze_key"])
    notes = [f"algorithm {algo}", f"leaf recomputed from the record: {leaf[:16]}…"]
    if proof.get("leaf") and proof["leaf"] != leaf:
        # Likeliest cause is the WRONG ALGORITHM, not a bad record — saying
        # "your record is wrong" would send you to investigate the data.
        return False, notes + [
            "THE LEAF WE COMPUTED IS NOT THE LEAF IN THE PROOF.",
            f"    proof says {proof['leaf'][:32]}…    we get {leaf[:32]}…",
            "    Most likely the `algo` field is wrong — v1 and v2 hash the "
            "same payload differently. Check `algo` before suspecting the "
            "record."]
    h = leaf
    for step in proof.get("proof", []):
        side = step["side"]                      # the side the SIBLING is on
        if side == "left":
            h = join(step["hash"], h)
        elif side == "right":
            h = join(h, step["hash"])
        else:
            return False, notes + [f"unknown side {side!r}"]
    notes.append(f"folded {len(proof.get('proof', []))} steps to {h[:16]}…")

    # THE ROOT, AND WHERE IT CAME FROM. An independently fetched root is the
    # only version of this check worth running; the proof's own copy is kept
    # as a fallback and the difference is stated in the output, never hidden.
    day = str(proof.get("day", ""))
    independent = (roots or {}).get(day)
    if independent:
        published = independent["root"]
        source = ("the PUBLIC log (roots.jsonl) — independent of the API that "
                  "served this proof")
        if (independent.get("algo") and proof.get("algo")
                and independent["algo"] != proof["algo"]):
            return False, notes + [
                f"ALGORITHM DISAGREEMENT for {day}: the proof says "
                f"{proof['algo']!r} and the public log says "
                f"{independent['algo']!r}. Do not guess — the two hash the "
                f"same payload differently. Ask which is correct before "
                f"concluding anything about the data."]
        if proof.get("published_root") and proof["published_root"] != published:
            return False, notes + [
                f"THE PUBLIC LOG AND THE PROOF DISAGREE about the root for "
                f"{day}.",
                f"    public log  {published[:32]}…",
                f"    this proof  {proof['published_root'][:32]}…",
                "    That is the disagreement this check exists to find. "
                "Trust the public log: its commit date is recorded by a "
                "third party."]
    elif roots is not None:
        # RULE 7. You asked for an independent check and the log you supplied
        # does not cover this day. Falling back to the root inside the proof
        # would print PASS for a check that established only that we are
        # internally consistent — which is the circularity --roots exists to
        # remove. UNKNOWN is not compliant.
        return None, notes + [
            f"NOT CHECKED: you supplied a roots file and it has no root for "
            f"{day}, so this proof could not be checked against an "
            f"independent source.",
            "    Either the public log has not caught up with that day yet — "
            "a day is only rooted once it has closed — or you fetched a "
            "stale copy. Re-fetch:",
            "    https://raw.githubusercontent.com/hshintelligence/"
            "hsh-transparency/main/ROOTS.jsonl",
            "    Running without --roots would compare this proof against a "
            "root we served you in the same file. That is not nothing, but "
            "it is not this check."]
    else:
        # ══════════════════════════════════════════════════════════════
        # LAW 1109 — THE VERDICT SAID PASS AND THE PROSE SAID OTHERWISE.
        #
        # Without --roots this took `published` from INSIDE THE PROOF —
        # a number we served in the same file — folded the path to it,
        # and returned True. The note beside it said plainly that this
        # establishes only internal consistency; the VERDICT, the
        # "All four checks passed" line and the EXIT CODE all said the
        # check passed.
        #
        # The branch directly above does the right thing for a roots
        # file that misses the day: it returns None, NOT CHECKED, and
        # says "falling back to the root inside the proof would print
        # PASS for a check that established only that we are internally
        # consistent". The no-roots case is the same circularity and was
        # the DEFAULT — the one a stranger hits running the documented
        # command.
        #
        # The fold is still performed and still reported, because it is
        # real evidence about the proof's internal shape. What it is not
        # is this check.
        # ══════════════════════════════════════════════════════════════
        published = proof.get("published_root") or ""
        folded = (h == published) if published else None
        return None, notes + [
            "NOT CHECKED: you did not supply --roots, so there is no "
            "independent root to compare against.",
            f"    The proof's own path "
            f"{'DOES' if folded else 'DOES NOT'} fold to the "
            f"`published_root` recorded inside it "
            f"({(published or '—')[:16]}…). That is worth knowing and it "
            f"is not this check: both numbers came from us, in the same "
            f"file, and a seller cannot vouch for a seller.",
            "    Fetch the public log from a host that is not ours and "
            "pass it:",
            "    https://raw.githubusercontent.com/hshintelligence/"
            "hsh-transparency/main/ROOTS.jsonl",
            "    python3 verify.py … --proof <file> --roots ROOTS.jsonl"]
    if not proof.get("root_published") or not published:
        return None, notes + ["NO ROOT IS PUBLISHED FOR THIS DAY: this proof "
                              "cannot be checked and establishes nothing."]
    # Proofs saved before 2026-08-23 name this field `verified`.
    field = ("folds_to_computed_root" if "folds_to_computed_root" in proof
             else "verified" if "verified" in proof else None)
    if field:
        notes.append(f"(proof carries '{field}' — informational; we folded it "
                     f"ourselves above)")
    return h == published, notes + [f"published root {published[:16]}…",
                                    f"root came from {source}"]


# ── 4. SPLIT DISJOINTNESS ───────────────────────────────────────────────────
def check_splits(d, meta):
    """The only guarantee you can establish COMPLETELY from the files alone."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return None, ["pyarrow is not installed, so split disjointness was "
                      "NOT checked. The other three checks do not need it."]
    seen, notes, broken = {}, [], []
    for name in ("train.parquet", "validation.parquet", "test.parquet"):
        p = os.path.join(d, name)
        if not os.path.exists(p):
            continue
        try:
            col = pq.read_table(p, columns=["cik"])["cik"].to_pylist()
        except Exception as e:               # unreadable, truncated, not Parquet
            # REPORT, never raise. A corrupt download is the case this check
            # is most likely to meet, and a traceback here would scroll the
            # results of checks 1-3 off the screen with it.
            broken.append(f"{name}: UNREADABLE as Parquet — {type(e).__name__}")
            continue
        seen[name] = set(col)
        notes.append(f"{name}: {len(col):,} rows, {len(seen[name]):,} companies")
    if broken:
        return False, notes + broken + ["a file that cannot be opened cannot "
            "be shown disjoint; check 1 says whether the bytes are ours"]
    overlaps = []
    names = sorted(seen)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            both = seen[a] & seen[b]
            if both:
                overlaps.append(f"{a} and {b} share {len(both)} CIK(s): "
                                f"{sorted(both)[:5]}")
    if meta.get("as_of"):
        # WHAT THIS WATERMARK IS, AND WHAT IT IS NOT. It used to read "ask
        # for this corpus again with this watermark and you get these same
        # bytes". That is a promise about our source tables, which are
        # corrected in place — a later rebuild at the same watermark can
        # legitimately differ, and on some releases it does. The guarantee
        # that holds is the one you can check here: the signed manifest
        # binds the bytes, and check 1 is what proves you have them.
        notes.append(f"as_of {meta['as_of']} — the watermark this corpus was "
                     f"built at. It identifies the build. It is NOT a "
                     f"promise that rebuilding at it returns these bytes: "
                     f"our source tables are corrected in place. What binds "
                     f"is the signed manifest, and check 1 proves the bytes "
                     f"you hold are the bytes we published.")
    if len(seen) < 2:
        # Disjointness between fewer than two sets is not a property: passing
        # would mean "no overlap found because nothing was opened".
        return None, notes + [f"only {len(seen)} split file(s) present — "
                              f"nothing was established"]
    return (not overlaps), notes + overlaps


def main():
    ap = argparse.ArgumentParser(description="Verify an HSH release yourself.")
    ap.add_argument("--dir", default=".", help="directory you downloaded into")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--release", default=None, help="release.json, for check 2")
    ap.add_argument("--proof", default=None, help="a proof JSON, for check 3")
    ap.add_argument("--roots", default=None,
                    help="ROOTS.jsonl from the PUBLIC transparency log, for "
                         "check 3. Without it check 3 compares against the "
                         "root inside the proof, which is a number we served "
                         "you — fetch it from "
                         "raw.githubusercontent.com/hshintelligence/"
                         "hsh-transparency/main/ROOTS.jsonl instead.")
    a = ap.parse_args()

    man = a.manifest or os.path.join(a.dir, "MANIFEST.txt")
    if not os.path.exists(man):
        sys.exit(f"no manifest at {man} — pass --manifest")
    meta, files = read_manifest(man)
    rel = json.load(open(a.release)) if a.release else {}
    print(f"release {meta.get('release','?')}   records {meta.get('records','?')}"
          f"   as_of {meta.get('as_of','?')}\n")

    failed = skipped = 0
    for label, (ok, notes) in [
            ("1. file integrity    ", check_files(a.dir, files)),
            ("2. manifest integrity", check_manifest(man, rel.get("manifest_sha"))),
            ("3. merkle membership ", check_merkle(
                json.load(open(a.proof)),
                load_roots(a.roots) if a.roots else None)
             if a.proof else (None, ["no --proof supplied"])),
            ("4. split disjointness", check_splits(a.dir, meta))]:
        print(f"{label}  " + MARK[ok])
        for n in notes:
            print(f"      {n}")
        failed += (ok is False)
        skipped += (ok is None)
    # "No check failed" is NOT the same sentence as "everything checked out",
    # and a verifier that blurs them manufactures confidence instead of
    # evidence. A skipped check is reported as loudly as a failed one.
    print()
    if failed:
        print(f"{failed} CHECK(S) FAILED — do not use this data until resolved.")
    if skipped:
        print(f"{skipped} CHECK(S) COULD NOT RUN and established NOTHING. "
              f"Supply what they need (see README) before concluding "
              f"anything. (exit code 2 — incomplete, not passed.)")
    if not failed and not skipped:
        print("All four checks passed. Read the README for what that does "
              "and does not establish.")
    # LAW 1109 — THE EXIT CODE IS READ BY A MACHINE THAT CANNOT READ THE
    # NOTES. `return 1 if failed else 0` gave a buyer's CI a green build
    # for a run in which a check established nothing. A skipped check is
    # its own outcome and gets its own code: 1 FAILED, 2 INCOMPLETE.
    if failed:
        return 1
    return 2 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())
