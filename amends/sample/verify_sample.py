#!/usr/bin/env python3
"""
VERIFY THE HSH AMENDS SAMPLE.  Standard library only.

    python3 verify_sample.py .

Needs nothing from the vendor: no pip install, no virtualenv, no account.
Python 3.8+, the files you downloaded, and `openssl` for the signature.

WHAT IT CHECKS, and why each one matters:

  1. Every file's sha256 matches the MANIFEST header.
     Catches truncation, corruption in transit, and a swapped file.

  2. Every record's payload hashes to its payload_sha.
     This is the row-level claim. It is the SAME check, byte for byte, that
     applies to the full 15.3-million-row product.

  3. The manifest's signature verifies against the published key.
     The host that served you these files cannot forge this. That is the
     point of fetching the key from somewhere else.

  4. SHA256SUMS covers every file here, and is itself signed.
     The manifest covers the DATA files. This covers everything else as
     well — this script, the dataset card, the attestation, the
     signatures. It is what makes "a one-line edit on the host breaks
     the checksums" a true sentence rather than a hopeful one, and it is
     signed so that a host able to edit a file cannot edit the checksums
     beside it.

  5. The key is the key the ANCHOR publishes — only if you give it to me.
     This is the one check that cannot be done from these files alone:
     the key shipped here and the manifest it signs came from the same
     host, so checking one against the other proves nothing about
     substitution. Fetch KEY-FINGERPRINT.txt from the transparency
     repository — a different host — and pass it:

         python3 verify_sample.py . --fingerprint KEY-FINGERPRINT.txt
         python3 verify_sample.py . --fingerprint <64-hex>

     Without it, THIS check reports NOT CHECKED and says what is missing.
     It is not treated as a pass, because "I did not look" and "I looked
     and it matched" are different results.

  6. The parquet's own rows hash to their payload_sha.
     Checks 1 and 2 read the CSV. load_dataset() returns the PARQUET, so
     this is the file most buyers actually hold. Check 4 proves its BYTES
     are the ones the seal covers; this proves its ROWS, and that the
     parquet and the CSV carry the same records. It needs pyarrow — without
     it the check reports NOT CHECKED rather than quietly passing.


A sample cannot prove COVERAGE — that the corpus figures describe the whole
of it. See COVERAGE-ATTESTATION.json, signed with the same key.
"""
import hashlib
import json
import os
import re
import subprocess
import sys


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def key_fingerprint(pub):
    """sha256 of the public key in DER — the value the anchor publishes."""
    der = subprocess.run(["openssl", "pkey", "-pubin", "-in", pub,
                          "-outform", "DER"], capture_output=True)
    if der.returncode != 0:
        return None
    return hashlib.sha256(der.stdout).hexdigest()


def expected_fingerprint(arg):
    """A 64-hex value, or the first one inside a file you were handed."""
    if not arg:
        return None
    if re.fullmatch(r"[0-9a-fA-F]{64}", arg.strip()):
        return arg.strip().lower()
    if os.path.exists(arg):
        m = re.search(r"[0-9a-fA-F]{64}", open(arg).read())
        if m:
            return m.group(0).lower()
    return None


def main(d, want_fp=None):
    fail = []
    man = os.path.join(d, "MANIFEST.txt")
    if not os.path.exists(man):
        print("FAIL: no MANIFEST.txt"); return 2

    print("[1] files against the manifest header")
    claims, records = {}, {}
    for line in open(man):
        if line.startswith("#"):
            m = re.match(r"#\s*file\s+(\S+)\s+sha256=([0-9a-f]{64})", line)
            if m:
                claims[m.group(1)] = m.group(2)
            continue
        parts = line.split()
        if len(parts) == 2:
            records[parts[0]] = parts[1]
    for name, want in sorted(claims.items()):
        p = os.path.join(d, name)
        if not os.path.exists(p):
            fail.append(f"missing {name}"); print(f"    MISSING  {name}"); continue
        got = sha256_file(p)
        ok = got == want
        if not ok:
            fail.append(f"{name}: sha256 mismatch")
        print(f"    {'ok      ' if ok else 'BAD     '} {name}")

    print("\n[2] every record's payload against its payload_sha")
    csv_shas = set()          # kept so check 6 can compare the parquet
    try:
        import csv
        n = bad = 0
        with open(os.path.join(d, "hsh-amends-sample.csv"), newline="",
                  encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                n += 1
                csv_shas.add(row["payload_sha"])
                if hashlib.sha256(row["payload"].encode()).hexdigest() != row["payload_sha"]:
                    bad += 1
                if row["record_uid"] in records and \
                        records[row["record_uid"]] != row["payload_sha"]:
                    bad += 1
        print(f"    {n:,} records checked, {bad:,} "
              f"mismatch{'' if bad == 1 else 'es'}")
        if bad:
            fail.append(f"{bad:,} payload hash "
                        f"mismatch{'' if bad == 1 else 'es'}")
    except Exception as e:
        fail.append(f"payload check could not run: {e}")
        print(f"    could not run: {e}")

    print("\n[3] the manifest signature")
    sig = man + ".sig"
    pub = os.path.join(d, "HSH-SIGNING-KEY.pub")
    if not (os.path.exists(sig) and os.path.exists(pub)):
        fail.append("signature or public key missing")
        print("    MISSING signature or key")
    else:
        r = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin",
                            "-inkey", pub, "-rawin", "-in", man,
                            "-sigfile", sig], capture_output=True)
        out = (r.stdout + r.stderr).decode(errors="replace").strip()
        print(f"    {out}")
        if r.returncode != 0:
            fail.append("signature did NOT verify")
        else:
            got = key_fingerprint(pub)
            print(f"    key fingerprint sha256: {got}")

    print("\n[4] SHA256SUMS against this directory, and its signature")
    sums = os.path.join(d, "SHA256SUMS")
    if not os.path.exists(sums):
        # An absent seal used to print
        # one line and count as nothing: delete SHA256SUMS and its
        # signature and a package with an edited README printed VERIFIED
        # and exited 0. MANIFEST.txt covers only the three DATA files;
        # the card, the attestation, the composition and this script
        # itself are covered ONLY by the seal. So its absence is a
        # RESULT, and it is the one a tampering host would arrange.
        fail.append("SHA256SUMS is absent — the card, the attestation and "
                    "this script are covered by nothing")
        print("    ABSENT — this copy carries no directory seal, so the")
        print("    card, the attestation, SAMPLE-COMPOSITION.json and this")
        print("    script itself are covered by NOTHING. The manifest")
        print("    covers only the three data files. Re-download.")
    else:
        listed = {}
        for line in open(sums):
            h, _, fn = line.strip().partition("  ")
            if fn:
                listed[fn] = h
        here = {fn for fn in os.listdir(d)
                if fn not in ("SHA256SUMS", "SHA256SUMS.sig")}
        probs = []
        probs += [f"{fn}: present here and NOT in SHA256SUMS"
                  for fn in sorted(here - set(listed))]
        probs += [f"{fn}: in SHA256SUMS and missing here"
                  for fn in sorted(set(listed) - here)]
        # A NAME IN THE SEAL THAT IS NOT A READABLE FILE IS A FINDING,
        # NOT A CRASH. Hashing a directory raises IsADirectoryError, so
        # replacing a sealed file with a directory of the same name used
        # to end this script in a traceback — before the remaining checks
        # and the verdict printed. That still fails closed, but it tells
        # you less than naming the file does.
        for fn in sorted(here & set(listed)):
            _fp = os.path.join(d, fn)
            try:
                if sha256_file(_fp) != listed[fn]:
                    probs.append(f"{fn}: CHANGED since the checksums "
                                 f"were written")
            except Exception as _fe:
                probs.append(f"{fn}: listed in SHA256SUMS but cannot be "
                             f"read as a file ({type(_fe).__name__})")
        ssig = sums + ".sig"
        if not os.path.exists(ssig):
            probs.append("SHA256SUMS is not signed")
        elif not os.path.exists(pub):
            # NOT a skip. Making the cryptographic half conditional on a
            # file inside the directory being verified means deleting that
            # file defeats it.
            probs.append("the signing key is missing, so SHA256SUMS.sig "
                         "cannot be checked")
        else:
            rr = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin",
                                 "-inkey", pub, "-rawin", "-in", sums,
                                 "-sigfile", ssig], capture_output=True)
            if rr.returncode != 0:
                probs.append("SHA256SUMS.sig does NOT verify")
        if probs:
            fail.extend(probs)
            for x in probs:
                print(f"    BAD      {x}")
        else:
            print(f"    ok       {len(listed):,} "
                  f"file{'' if len(listed) == 1 else 's'}, "
                  f"signature verifies")

    print("\n[5] the key against the fingerprint the ANCHOR publishes")
    got = key_fingerprint(pub) if os.path.exists(pub) else None
    want = expected_fingerprint(want_fp)
    if got is None:
        fail.append("could not read the public key to fingerprint it")
        print("    could not read the public key")
    elif want is None:
        # NOT A PASS. This is the one check the files cannot answer, and
        # reporting it as satisfied because nothing was supplied is the
        # defect the whole kit exists to avoid.
        print("    NOT CHECKED - no fingerprint supplied.")
        print("    The key here and the manifest it signs arrived from the")
        print("    same host, so they cannot vouch for each other. Fetch")
        print("    KEY-FINGERPRINT.txt from the HSH transparency repository")
        print("    and re-run with --fingerprint to close this.")
    elif got == want:
        # ══════════════════════════════════════════════════════════════
        # "FROM A DIFFERENT HOST" IS SOMETHING THIS SCRIPT CANNOT KNOW.
        #
        # The value of this check is that the fingerprint came from
        # somewhere the dataset host does not control. This script only
        # sees a file path. If you passed the copy of KEY-FINGERPRINT.txt
        # that travelled inside the same download, that is a real
        # integrity check and it is NOT a cross-host one.
        #
        # So the line below reports what it actually did: matched the
        # fingerprint it was given, and names where that came from.
        # Whether that source is independent of the host that served you
        # the sample is yours to know, and yours to decide.
        # ══════════════════════════════════════════════════════════════
        print(f"    ok       matches {want[:16]}... from {want_fp}")
        print("    This is only a CROSS-HOST check if that file came from")
        print("    somewhere the party who sent you the data does not")
        print("    control. Fetched from the transparency repository it is;")
        print("    unpacked from this same download it is not.")
    else:
        fail.append("key fingerprint does NOT match the anchor")
        print(f"    BAD      this key is {got}")
        print(f"             the anchor publishes {want}")
        print("             STOP. Do not trust these files.")

    print("\n" + "=" * 62)
    if fail:
        print(f"VERIFICATION FAILED — {len(fail):,} "
              f"problem{'' if len(fail) == 1 else 's'}:")
        for f in fail:
            print(f"  - {f}")
        return 1
    # ══════════════════════════════════════════════════════════════
    # CHECK 2 READS THE CSV. load_dataset() RETURNS THE PARQUET.
    #
    # The dataset card's `configs: data_files:` points at
    # hsh-amends-sample.parquet, so following the card's first example
    # gives you the PARQUET — while every row-level check above was
    # measured on the CSV. Rewriting parquet rows and leaving their
    # payload_sha alone would still have printed "0 mismatches".
    #
    # The parquet is covered as a whole by SHA256SUMS in check 4, so it
    # cannot be swapped silently. What that does not establish is whether
    # its ROWS say what the CSV's rows say. Comparing them needs pyarrow,
    # which this script does not require you to have — so it is
    # attempted, and when it cannot run it is REPORTED rather than
    # skipped. An unchecked file is not a checked one.
    # ══════════════════════════════════════════════════════════════
    print("\n[6] the parquet's rows, which is what load_dataset() returns")
    pq_path = os.path.join(d, "hsh-amends-sample.parquet")
    if not os.path.exists(pq_path):
        print("    no parquet in this directory")
    else:
        try:
            import pyarrow.parquet as _pq
        except ImportError:
            print("    NOT CHECKED - pyarrow is not installed here.")
            print("    Check 4 proves this file's BYTES are the ones the")
            print("    seal covers. Its ROWS have not been compared to the")
            print("    CSV's, and the dataset card's own example loads this")
            print("    file, not the CSV. `pip install pyarrow` and re-run")
            print("    to close it.")
        else:
            t = _pq.read_table(pq_path, columns=["payload", "payload_sha"])
            pay = t.column("payload").to_pylist()
            shas = t.column("payload_sha").to_pylist()
            bad_rows = sum(
                1 for a, b in zip(pay, shas)
                if hashlib.sha256(a.encode()).hexdigest() != b)
            if bad_rows:
                fail.append(
                    f"{bad_rows:,} parquet "
                    f"row{'' if bad_rows == 1 else 's'} "
                    f"do{'es' if bad_rows == 1 else ''} not match "
                    f"{'its' if bad_rows == 1 else 'their'} own payload_sha")
                print(f"    BAD      {bad_rows:,} of {len(pay):,} rows")
            else:
                print(f"    ok       {len(pay):,} rows, each payload matches "
                      f"its own payload_sha")
            if csv_shas and set(shas) != csv_shas:
                fail.append("the parquet and the CSV do not hold the same "
                            "records")
                print("    BAD      the parquet and the CSV disagree about "
                      "which records are here")
            else:
                print("    ok       the parquet and the CSV hold the same "
                      "records")

    # ══════════════════════════════════════════════════════════════
    # THE PROSE SAID "NOT RUN" AND THE EXIT STATUS SAID PASS.
    #
    # A forged package — attacker's key, edited licence sentence,
    # rewritten payloads with recomputed hashes, everything re-signed —
    # is internally consistent, so every check that asks whether the
    # package agrees with ITSELF passes. Only the fingerprint check
    # catches it, and check 5 needs a fingerprint fetched from the other
    # host. Without one this printed "Check 5 ... was NOT run" and then
    # returned 0. Any CI step or script gating on the exit code accepted
    # the forgery, and UPLOAD-THIS.md's own instruction was the bare
    # `python3 verify_sample.py .`.
    #
    # Three states, because there are three:
    #   0  every check ran and passed
    #   1  a check FAILED - do not trust these files
    #   2  what ran passed, and the check that catches a substituted key
    #      did not run
    #
    # 2 is not a failure of the package. It is a failure to have
    # finished checking it, and a caller that cannot tell those apart
    # from the exit code is a caller that ships the difference.
    # ══════════════════════════════════════════════════════════════
    if expected_fingerprint(want_fp) is None:
        print("INCOMPLETE - files, every record hash and the signature all "
              "verify.")
        print("Check 5 (this key against the fingerprint the anchor "
              "publishes) was NOT run,")
        print("so nothing here rules out a package re-signed under a "
              "substituted key.")
        print("Re-run with --fingerprint to close it. Exit status 2 means "
              "INCOMPLETE, not FAILED.")
        print("Coverage is NOT proven by a sample: see "
              "COVERAGE-ATTESTATION.json.")
        return 2
    print("VERIFIED — files, every record hash, and the signature, "
          "against the anchor's key.")
    print("Coverage is NOT proven by a sample: see COVERAGE-ATTESTATION.json.")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    fp = None
    if "--fingerprint" in args:
        i = args.index("--fingerprint")
        fp = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
    sys.exit(main(args[0] if args else ".", fp))
