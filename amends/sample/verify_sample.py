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


def main(d):
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
    try:
        import csv
        n = bad = 0
        with open(os.path.join(d, "hsh-amends-sample.csv"), newline="",
                  encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                n += 1
                if hashlib.sha256(row["payload"].encode()).hexdigest() != row["payload_sha"]:
                    bad += 1
                if row["record_uid"] in records and \
                        records[row["record_uid"]] != row["payload_sha"]:
                    bad += 1
        print(f"    {n:,} records checked, {bad} mismatch(es)")
        if bad:
            fail.append(f"{bad} payload hash mismatch(es)")
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
            der = subprocess.run(["openssl", "pkey", "-pubin", "-in", pub,
                                  "-outform", "DER"], capture_output=True)
            print(f"    key fingerprint sha256: "
                  f"{hashlib.sha256(der.stdout).hexdigest()}")
            print("    compare that against the fingerprint published in the")
            print("    HSH transparency repository, which is a different host.")

    print("\n" + "=" * 62)
    if fail:
        print(f"VERIFICATION FAILED — {len(fail)} problem(s):")
        for f in fail:
            print(f"  - {f}")
        return 1
    print("VERIFIED — files, every record hash, and the signature.")
    print("Coverage is NOT proven by a sample: see COVERAGE-ATTESTATION.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
