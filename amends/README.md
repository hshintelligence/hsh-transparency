# HSH Amends — trust anchor

This directory is the **anchor** for HSH Amends, not a file host. Nothing
large lives here. What lives here is the small set of values that let you
check something you fetched from somewhere else.

    TRUST-ROOTS.json          every published release, with its manifest_sha
    TRUST-ROOTS.json.sig      ed25519 signature over that file
    HSH-SIGNING-KEY.pub       the public key
    KEY-FINGERPRINT.txt       sha256 of the key in DER — the value to compare
    sample/                   a byte-identical mirror of the published sample
    notebook/                 a notebook that runs those checks in order

It sits one level inside the HSH Intelligence transparency log, which
publishes a daily Merkle root over the SEC EDGAR corpus. That is a separate
guarantee about a different artefact and the README above explains it. The
two share a repository because they share the one property either needs:
append-only, public, and not the host that served you the data.

## Why a second copy of the sample is here

The sample is published on a dataset host for reach. It is mirrored here so
the two **cross-attest**: same bytes, same `MANIFEST.txt`, same signature.
If a host changes its terms, goes away, or serves you something altered,
the proof and the sample both survive in Git — and a mismatch between the
two copies is itself the alarm.

This repository is append-only and independent of whatever served you the
data. That is the only property a trust anchor actually needs.

One consequence, stated so it is not mistaken for a choice: the mirror
carries the sample's dataset card verbatim, licence paragraph and all,
because byte-identical means byte-identical — nothing written for this
directory is commercial.

## Verify the key you were handed

    openssl pkey -pubin -in HSH-SIGNING-KEY.pub -outform DER | sha256sum

Compare to `KEY-FINGERPRINT.txt`. If they differ, stop.

## Verify a release

    openssl pkeyutl -verify -pubin -inkey HSH-SIGNING-KEY.pub \
        -rawin -in TRUST-ROOTS.json -sigfile TRUST-ROOTS.json.sig

Then look up your release in `TRUST-ROOTS.json` and compare its
`manifest_sha` to the sha256 of the `MANIFEST.txt` you hold.

## Verify the sample

    cd sample && python3 verify_sample.py .

## Documentation

The data dictionary, release history, schema stability note, datasheet and audit report, in one folder:

    https://drive.google.com/drive/folders/1c3qzgAFHef1lyTfRYQi5gpqIHXbCyhAn?usp=sharing

## The notebook in `notebook/`

**The notebook is a convenience, and it is worth saying what that means.** It runs the same checks you would run by hand, but it is also the thing telling you they passed. A reader who wants certainty should run the four commands themselves — fetch from the dataset host, fetch the key from the anchor, compare the fingerprint, verify the signature — which is what `verify_sample.py` does. No arrangement of hosts fixes this: a notebook on a third host would still be the thing reporting its own result.

What the two hosts DO protect is the data. If the dataset host served you an altered sample, the key and fingerprint published independently would not match it, and you would catch it. That is the claim, and it holds.
