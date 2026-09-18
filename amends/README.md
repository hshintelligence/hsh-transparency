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
this copy and the proof beside it do not change with it — and a mismatch
between the two copies is itself the alarm.

This repository is public, is independent of whatever served you the data,
and keeps a Git history anyone can inspect. It is NOT append-only by
enforcement: the account is ours and we could rewrite or remove it. Clone
it when you take delivery. What a rewrite cannot reach is the copy in your
hands, and that is the property a trust anchor actually needs — not our
good behaviour, but your ability to check without us.

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
`manifest_sha` to the sha256 of the manifest that came **with the full
release** — the `MANIFEST.txt` beside the Parquet files you were
delivered.

**That is not the `MANIFEST.txt` in `sample/`.** There are two manifests
and they describe different artefacts: one covers the full product, the
other covers the 5,645-row sample. They have different hashes,
they are signed separately, and comparing the sample's manifest to a
release's `manifest_sha` will not match — correctly. Only the product's
manifest is the one `TRUST-ROOTS.json` names.

If you hold only the sample, the section below is the one you want.

## Verify the sample

    cd sample && python3 verify_sample.py . --fingerprint ../KEY-FINGERPRINT.txt

Five of the six checks need only the files in `sample/`. The one that does not — check 5, the signing key against the fingerprint published here, on a host that did not serve you the sample — is the reason `--fingerprint` is on that command line. Without it the script prints NOT CHECKED for that one rather than counting it as a pass.

## Documentation

The datasheet, data dictionary, audit report, release history, schema stability note, product due diligence questionnaire, corrections policy, legal one-pager and errata & release history:

    https://drive.google.com/drive/folders/1c3qzgAFHef1lyTfRYQi5gpqIHXbCyhAn?usp=sharing

## The notebook in `notebook/`

**The notebook is a convenience, and it is worth saying what that means.** It runs the same checks you would run by hand, but it is also the thing telling you they passed. A reader who wants certainty runs them against the two hosts themselves.

`verify_sample.py` does five of the six from the files alone — files against the manifest header; every record's payload against its payload_sha; the manifest signature; SHA256SUMS against this directory, and its signature; and the parquet's rows, which is what load_dataset() returns. The one it cannot do alone is check 5, the key against the fingerprint the ANCHOR publishes: the key shipped beside the sample and the manifest it signs came from the SAME host, so neither vouches for the other. Fetch `KEY-FINGERPRINT.txt` from the transparency repository and pass it — `--fingerprint KEY-FINGERPRINT.txt` — and the script checks it. Without it, check 5 prints NOT CHECKED rather than counting as a pass.

What the script deliberately does NOT do is fetch anything. A tool that downloads both halves of a proof is one host telling you about itself again, which is the thing the second host exists to prevent. No arrangement of hosts fixes that for the notebook either: a notebook on a third host would still be the thing reporting its own result.

What the two hosts DO protect is the data. If the dataset host served you an altered sample, the key and fingerprint published independently would not match it, and you would catch it. That is the claim, and it holds.

---

© 2026 Healing Sun Haven LLC
