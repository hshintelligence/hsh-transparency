---
license: other
license_name: hsh-commercial-sample
pretty_name: HSH Amends — sample
language:
  - en
size_categories:
  - 1K<n<10K
task_categories:
  - tabular-classification
tags:
  - finance
  - sec-edgar
  - sample
configs:
  - config_name: default
    data_files:
      - split: sample
        path: hsh-amends-sample.parquet
---

# HSH Amends — evaluation sample

**5,076 rows drawn from a 18,657,314-row commercial dataset.** Signed, and verifiable in about two minutes without contacting us.

> **This is a sample of a paid product.** It is published so a data team can evaluate the real thing — the real schema, the real values, the real verification chain — before any conversation about licensing. It is not open data and it is not a free tier. Licence terms are below.

---

| | |
|---|---|
| **Run the checks** | [Colab notebook](https://colab.research.google.com/github/hshintelligence/hsh-transparency/blob/main/amends/notebook/hsh-amends-verify-and-explore.ipynb) — verifies this sample against a second host, then explores it |
| **Trust anchor** | [hshintelligence/hsh-transparency](https://github.com/hshintelligence/hsh-transparency/tree/main/amends) — the signing key, its fingerprint, and the signed record of every release |
| **Documentation** | [Open the folder](https://drive.google.com/drive/folders/1c3qzgAFHef1lyTfRYQi5gpqIHXbCyhAn?usp=sharing) — the datasheet, data dictionary, audit report, release history, schema stability note, product due diligence questionnaire, corrections policy, legal one-pager, errata and pricing sheet |
| **Who we are** | [hshintelligence.com](https://hshintelligence.com) |
| **Licensing** | [info@healingsunhaven.com](mailto:info@healingsunhaven.com) |

## Why this dataset exists

**The SEC does not record which filing amends which.** An amended filing arrives as a new submission with a new accession number and an `/A` suffix, and nothing in the index says what it supersedes. Every vendor who offers an amendment chain has inferred it.

So have we. The difference is what happens next: we measure the inference against the filing documents themselves — a channel the matching rule cannot see, because the rule works on index metadata and the measurement reads the text — and we publish the result per stratum, with its denominator, including the strata that failed and were withdrawn.

A precision figure with no denominator is a claim. One with its population, its sample, its interval and its method is a measurement. Everything below is the second kind.

## Who this is for

| | |
|---|---|
| **Quantitative research** | Restatements and amendments are look-ahead traps: the amended figure was not knowable on the original filing date. `superseded_at` lets a backtest rebuild the chain as it stood on any past date, and `first_seen_at` gives SEC's acceptance time where `first_seen_source` is `sec_acceptance`; `version_seq` and `is_latest` describe the chain as it stands now, so do not use them as point-in-time. |
| **Compliance and audit** | One row per (filer, filing) with an explicit state for every amendment — linked, or a named reason it is not. Unresolved cases are enumerated rather than dropped. |
| **AI and model providers** | Every row carries its provenance: source URL, licence, crawler version, contract version and the pipeline commit that produced it. The manifest is signed and the record hashes are verifiable offline. |
| **Academic research** | A reproducible corpus with a published method, a signed coverage attestation, and a public transparency log on a host that is not ours, with a history anyone can inspect. |

## Dataset summary

| | |
|---|---|
| Records | **18,657,314** — one per (filer, filing) |
| Filings | 12,735,840 distinct accession numbers |
| Companies | 745,224 distinct CIKs |
| Date range | 2009-01-02 to 2026-09-23 |
| Format | Apache Parquet, 3 parts |
| Size | 1.5 GB |
| Release | `restatements-v1.6.0` (as-of watermark 2026-09-26) |
| Cadence, observed | **7 releases between 2026-09-10 and 2026-09-26**, this one included — 16 days |
| Cadence, committed | Stated in the commercial terms, not here. This page reports what has been published; what will be published on what schedule is a contractual commitment and is made there. |
| This sample | 5,076 rows, published free for evaluation |

## What the dataset is

An amendment index over SEC EDGAR at filing grain: one row per (filer, filing). For each filing it states whether the filing is itself an amendment, whether anything known supersedes it, its position in a version chain, and — where the amended filing can be identified — which filing it amends, with the method and a confidence.

**The central limitation is stated first:** the amendment chain resolves for a small minority of amendments overall; the datasheet measures it per form class, because a single blended rate would mislead. The rest carry a NAMED REASON rather than a blank. An unlinked amendment we can name is worth more than a linked one we guessed.

## Verify it before you read it

```bash
python3 verify_sample.py .
```

Six checks, and what each of them asks differs. Most compare the files you hold against what the signed manifest binds, and apply to the full product exactly as they do here. One is this directory's own seal, which the full product does not have. One compares the parquet's rows with the CSV's, because they are different files and only the first is what `load_dataset()` returns. And check 5 is the signing key against a host that did not serve you the sample:

1. files against the manifest header
2. every record's payload against its payload_sha
3. the manifest signature
4. SHA256SUMS against this directory, and its signature
5. the key against the fingerprint the ANCHOR publishes
6. the parquet's rows, which is what load_dataset() returns

The key fingerprint is published in the [HSH transparency repository](https://github.com/hshintelligence/hsh-transparency/tree/main/amends) — a different host, with a history anyone can inspect. Fetch the key from there rather than from here, and the two would have to collude to fool you. That is the whole design: **where you fetch from and where you anchor trust are different questions.**

A Colab notebook does all of it in order — verification first, data second: [open the notebook](https://colab.research.google.com/github/hshintelligence/hsh-transparency/blob/main/amends/notebook/hsh-amends-verify-and-explore.ipynb).

**The notebook is a convenience, and it is worth saying what that means.** It runs the same checks you would run by hand, but it is also the thing telling you they passed. A reader who wants certainty runs them against the two hosts themselves.

`verify_sample.py` does five of the six from the files alone — files against the manifest header; every record's payload against its payload_sha; the manifest signature; SHA256SUMS against this directory, and its signature; and the parquet's rows, which is what load_dataset() returns. The one it cannot do alone is check 5, the key against the fingerprint the ANCHOR publishes: the key shipped beside the sample and the manifest it signs came from the SAME host, so neither vouches for the other. Fetch `KEY-FINGERPRINT.txt` from the transparency repository and pass it — `--fingerprint KEY-FINGERPRINT.txt` — and the script checks it. Without it, check 5 prints NOT CHECKED rather than counting as a pass.

What the script deliberately does NOT do is fetch anything. A tool that downloads both halves of a proof is one host telling you about itself again, which is the thing the second host exists to prevent. No arrangement of hosts fixes that for the notebook either: a notebook on a third host would still be the thing reporting its own result.

What the two hosts DO protect is the data. If the dataset host served you an altered sample, the key and fingerprint published independently would not match it, and you would catch it. That is the claim, and it holds.

## The schema

**19 columns.** Types are read from the Parquet in this package; meanings are the ones published in the data dictionary, which also carries null rates, cardinalities and per-field caveats.

| column | type | meaning |
|---|---|---|
| `record_uid` | `VARCHAR` | The primary key. One row per (filer, filing), stable across releases. This is the column to join on |
| `release_id` | `VARCHAR` | Which release this row was published in. Constant within a file; useful after concatenating several releases |
| `product` | `VARCHAR` | The product identifier this release belongs to. Constant within a release |
| `split` | `VARCHAR` | Machine-learning split assignment: train, validation or test |
| `payload` | `VARCHAR` | The amendment verdict for this filing, as a JSON object. Every analytical field lives here — see the payload table below |
| `payload_sha` | `VARCHAR` | SHA-256 of the `payload` string exactly as shipped. The other half of the verification pair |
| `tokens` | `BIGINT` | An estimate of the payload's size in language-model tokens… |
| `cik` | `VARCHAR` | SEC's Central Index Key for the filer, unpadded |
| `cik10` | `VARCHAR` | The same CIK zero-padded to ten characters — SEC's own conventional form |
| `accession` | `VARCHAR` | SEC's accession number for the filing, canonical (digits only, no dashes). With `cik` it identifies a filing uniquely |
| `company_name` | `VARCHAR` | The filer's name as SEC recorded it on this filing |
| `filed_at` | `VARCHAR` | The date SEC assigned to the filing. NOT the moment it became public — see `first_seen_at` in the payload |
| `pipeline_sha` | `VARCHAR` | An opaque identifier for the build that produced this row. Comparable, not resolvable — see below |
| `source_url` | `VARCHAR` | The address SEC's EDGAR archive path scheme gives for this row's `cik` and `accession`… |
| `licence` | `VARCHAR` | The licence this row is published under |
| `crawler_version` | `VARCHAR` | Version of the acquisition code |
| `contract_version` | `VARCHAR` | Version of the source contract — what the acquisition expects to receive from its source… |
| `jurisdiction` | `VARCHAR` | The jurisdiction of the source filing |
| `quality_flags` | `VARCHAR[]` | Per-row quality markers. An empty list means no flag was raised for this row |

`payload` is a JSON object holding the analytical fields — `link_state`, `amends_accession`, `link_basis`, `link_confidence`, `version_seq`, `is_latest`, `period` and the rest. The flat CSV in this package explodes them into columns as a convenience; the Parquet schema above is the product.

**Full data dictionary — every column, every payload field, measured null rates and the caveats attached to each — is in the documentation folder linked under Quick links above, alongside the datasheet, the audit report and the release history. No request needed and no licence required to read it.**

## The audit, and why it is not a QA table

**8 checks**, each with the tool that ran it and the version of that tool. Read from the audit report, not restated here.

| check | tool | version | verdict |
|---|---|---|---|
| format and schema | pyarrow | `23.0.1` | **PASS WITH NOTE** |
| secrets scan | gitleaks | `8.18.4` | **PASS WITH NOTE** |
| pii detection | presidio-analyzer + spacy en_core_web_lg | `presidio-analyzer 2.2.362, spacy 3.7.5, model en_core_web_lg` | **PASS WITH NOTE** |
| length distribution | pyarrow + python statistics | `pyarrow 23.0.1, python 3.12.3` | **PASS WITH NOTE** |
| statistical balance | python (Gini, own implementation) | `python 3.12.3` | **PASS WITH NOTE** |
| near duplicate | pyarrow.compute | `23.0.1` | **PASS WITH NOTE** |
| source attribution | pyarrow + regex (own implementation) | `pyarrow 23.0.1` | **PASS** |
| currency | exact histogram over the shipped Parquet | `—` | **PASS WITH NOTE** |

Two things make this different from a vendor's QA summary.

**It ran against the shipped Parquet**, not against the tables the Parquet was built from. A check that passes on the source and is never re-run on the artefact says nothing about the file you receive.

**What is bound by the signature, and what is not.** The manifest binds the data files, the verification kit and the per-stratum LINK-ACCURACY figures — those cannot be revised after the fact without the manifest's sha256 changing, and that sha256 is what the signed trust roots record — you can check the accuracy figures yourself in the manifest's own `# accuracy` lines. **The 8 quality checks above are NOT bound by it.** The audit report is a separate object and **no signature covers it**: the manifest digest does not, and neither do the release’s file hashes, which bind the three Parquet files, the accuracy lines and the verification kit and nothing else. It travels with a sha256 in the document index it ships beside, and that index is not signed. We would rather say which is which — and say plainly where there is nothing — than let one guarantee stand in for another.

## Usage

Each block stands alone — copy any one of them into a notebook beside the Parquet and it runs. That is deliberate: an example that only works after you have run the ones above it is an example a buyer does not try.

**Load it.**

```python
import pandas as pd
df = pd.read_parquet('hsh-amends-sample.parquet')
print(len(df), 'rows,', df.shape[1], 'columns')
```

**Find the resolved amendments.**

```python
import json, pandas as pd
df = pd.read_parquet('hsh-amends-sample.parquet')

df['link_state'] = df.payload.map(lambda p: json.loads(p)['link_state'])
linked = df[df.link_state == 'linked']
print(len(linked), 'linked')
print(df.link_state.value_counts().to_dict())
```

**Follow one amendment chain end to end.**

```python
import json, pandas as pd
df = pd.read_parquet('hsh-amends-sample.parquet')

p = df.payload.map(json.loads)
df['link_state'] = p.map(lambda x: x['link_state'])
df['amends']     = p.map(lambda x: x['amends_accession'])
df['form']       = p.map(lambda x: x['form_type'])
df['period']     = p.map(lambda x: x['period'])
df['basis']      = p.map(lambda x: x['link_basis'])

# an amendment whose amended filing is also in this sample
both = df[df.link_state.eq('linked') & df.amends.isin(df.accession)]
a = both.iloc[0]
orig = df[df.accession == a.amends].iloc[0]

print(a.company_name or f'CIK {a.cik}')
print(f'  amendment  {a.form:9s} {a.accession}  filed {a.filed_at}')
print(f'  amends     {orig.form:9s} {orig.accession}  filed {orig.filed_at}')
print(f'  period     {a.period}')
print(f'  linked by  {a.basis}')
```

**74 amendment chains close inside this sample** (92 amendment rows resolve to an original that is also here; several amendments share an original, which is why the two numbers differ) — both the amendment and the filing it amends are present. That happens in `10-KT` and `10-QT`, which are drawn on base form alone, so the originals arrive with the amendments. Every other stratum draws the amendments only, so their targets sit in the full dataset rather than here. Wherever `link_state` is `linked`, the target exists.

**Verify it.**

```bash
python3 verify_sample.py .
```

## What a sample cannot prove, and what we do about it

A subset establishes nothing about its superset. Precision, and the populations and reachable frames it was measured over, are statements about the whole corpus, so they are published as a **signed attestation** — `COVERAGE-ATTESTATION.json`, signed with the same key — carrying every stratum's population, reachable frame, measured precision and claim type.

You can therefore check our precision claims without us handing over the data they describe. Coverage against SEC's own list is measured in the datasheet.

| stratum | population | frame reachable | examined | confirmed | contradicted | inconclusive | precision | claim type |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `10-K` | 21,287 | 21,287 (100.00%) | 300 | 297 | 0 | 3 | **100.00%** | sampled — [98.72, 100.00] |
| `10-KT` | 83 | 83 (100.00%) | 83 | 76 | 1 | 6 | **98.70%** | census — every member examined |
| `10-Q` | 19,225 | 19,225 (100.00%) | 300 | 296 | 0 | 4 | **100.00%** | sampled — [98.72, 100.00] |
| `10-QT` | 9 | 9 (100.00%) | 9 | 8 | 0 | 1 | **100.00%** | census — every member examined |
| `11-K` | 320 | 320 (100.00%) | 300 | 280 | 0 | 20 | **100.00%** | sampled — [98.65, 100.00] |
| `20-F` | 2,271 | 2,271 (100.00%) | 300 | 269 | 2 | 29 | **99.26%** | sampled — [97.35, 99.80] |
| `40-F` | 319 | 319 (100.00%) | 300 | 292 | 0 | 8 | **100.00%** | sampled — [98.70, 100.00] |

`inconclusive` **is examined and undecided, and it is EXCLUDED from the precision denominator rather than counted against it.** Across these strata that is **71 of 1,592 records examined** (4.5%). A precision of 100% on a stratum with inconclusives means every record that COULD be decided was confirmed — not that every record was. The column is here so you can see the size of what was set aside.

**2** of these strata are reported as a **census**: every member examined, so there is no sampling risk and no interval is quoted. Quoting one would imply an inference nobody made. A census can still carry inconclusives: those members were examined and produced no verdict.

### What we withdrew

Strata measured below the floor are **not shipped as linked**. The rows carry a named reason instead.

| link basis | form | population | sampled | confirmed | contradicted | precision | measured | outcome |
|---|---|---:|---:|---:|---:|---:|---|---|
| `index:cik+form` | `10-Q` | 1,377 | 300 | 59 | 102 | **36.65%** | 2026-09-11 | HOLD |
| `index:cik+form` | `10-K` | 1,013 | 300 | 179 | 52 | **77.49%** | 2026-09-11 | HOLD |

These are **historical readings**, and the date matters. They were measured before our sampling draw was made deterministic, and they cannot be re-derived — the links they describe were withdrawn and no longer sit in a state that asserts a link, so the audit no longer examines them. We publish them dated rather than re-deriving something that no longer exists, because what we measured and then withheld is evidence you cannot get anywhere else.

## What is in the sample, and how it was sized

**5,076 rows** across **126 base forms** (**161 form types** once amendment suffixes are counted separately), carrying **1,683 links in 1,588 distinct chains**.

The rule is: **stratified deterministic draw, census strata complete, every other stratum floored to a minimum evaluable mass, every link state represented.**

**The unit is the chain within a stratum, not the row.** Your smallest natural filter is a stratum — *show me 40-F/A* — and a sample becomes a screenshot the moment that filter returns too few chains to judge. So each stratum is drawn to whichever is largest of its target, the N that yields 150 units, and the N at which **every year present in that stratum has appeared**. Ordering is `md5(record_uid)` throughout and the draw is only ever extended, never hand-picked.

**You can run that claim rather than take it.** `reproduce_sample.py` rebuilds this sample from the release and the published rules and tells you whether it got the same rows:

    python3 reproduce_sample.py /path/to/release/parquet/

It reports two verdicts, because they are different claims. **ROW SET** is the draw itself — it depends only on the release and the rules in `SAMPLE-COMPOSITION.json`, and a failure there means the sample is not what this page describes. **BYTE-EXACT** is the row set plus the CSV writer: matching our bytes also needs duckdb 1.5.1, which wrote them. Identical rows with different bytes is a quoting difference, not a data difference, and the script says which one you have.

A uniform percentage would not do this. A 1% draw is ~187,000 rows carrying roughly 435 linked rows across the 7 AUDIT strata (a different cut from the 12 sample strata tabulated below) and 18 years — about 3.5 linked ROWS per stratum-year. (Rows, not chains: this release holds 1,683 links in 1,588 distinct chains in the sample, so the two are not interchangeable.) 37 times the size of this sample and less evaluable, because a percentage is blind to where the information lives.

| stratum | rows | chains | years covered |
|---|---:|---:|---:|
| 10-KT (complete) | 486 | 65 | 18 of 18 |
| 10-QT (complete) | 100 | 9 | 17 of 17 |
| unverifiable_at_release (complete) | 0 | no links | 0 of 0 |
| no_prior_filing_in_corpus | 655 | no links | 17 of 17 |
| unresolved_prior_exists | 250 | no links | 18 of 18 |
| 10-K linked | 350 | 350 | 18 of 18 |
| 10-Q linked | 350 | 350 | 18 of 18 |
| 20-F linked | 350 | 345 | 18 of 18 |
| 40-F linked | 300 | 271 | 18 of 18 |
| 11-K linked | 241 | 198 | 18 of 18 |
| unknown_subject | 900 | no links | 18 of 18 |
| not_an_amendment | 1,100 | no links | 18 of 18 |
| **total drawn** | **5,082** | | |

**That column sums to 5,082, and the sample is 5,076 rows.** The strata are not disjoint, and three different counts describe that — so each is named:

- **494 rows in this sample satisfy more than one stratum rule.** The census strata are defined on base form and the state strata on link state, so a 10-KT row that is not an amendment satisfies both.
- **6 of those were DRAWN into two strata**, which is the whole of the difference between the column total and the sample. The draws are unioned, so the sample holds each of them once. The rest satisfy a second rule whose own draw did not reach them.
- The largest overlapping pair is **391 rows** that are both *10-KT, every row* and *not_an_amendment*.

The per-stratum figures are the draw sizes, and changing them to make the column add up would break the reproduction above.

Every stratum covers every year its population covers. That is the half of the rule a row count cannot show, so it is measured here rather than asserted.

It is **not a random sample** — rare states are over-represented on purpose, so you can see the states we disclose rather than only the easy case. Both figures are given so the distortion is visible:

| link_state | in sample | in the full dataset |
|---|---:|---:|
| `linked` | 1,683 | 43,514 |
| `not_an_amendment` | 1,580 | 16,947,902 |
| `unknown_subject` | 900 | 1,661,837 |
| `no_prior_filing_in_corpus` | 661 | 1,248 |
| `unresolved_prior_exists` | 252 | 2,813 |

**3 strata are included complete** — every row of them: `10-KT`, `10-QT` and `unverifiable_at_release`. A sample of a complete stratum is a contradiction, so those are not sampled.

That is a different property from the **2 strata the coverage attestation reports as a census** (`10-KT` and `10-QT`), which says the AUDIT examined every reachable row of them.

## Files

| file | what |
|---|---|
| `hsh-amends-sample.parquet` | the real 19-column schema |
| `hsh-amends-sample.csv` | the same rows as CSV |
| `hsh-amends-sample-flat.csv` | `payload` exploded into columns, a convenience view and not part of the schema |
| `MANIFEST.txt` | sha256 per file and per record |
| `MANIFEST.txt.sig` | ed25519 signature over the manifest |
| `COVERAGE-ATTESTATION.json` | the corpus-level claims, signed |
| `HSH-SIGNING-KEY.pub` | the public key |
| `verify_sample.py` | the six checks, stdlib only |
| `SAMPLE-COMPOSITION.json` | every stratum's rule, target and draw size — the input to the reproducer |
| `reproduce_sample.py` | rebuilds this sample from the release and checks it matches (needs duckdb) |

## Licence and terms

This sample is provided for **evaluation**. It is not redistributable and confers no rights to the full dataset. The pricing sheet ships beside these documents. The Master Data License Agreement and Order Form are held and sent on request from info@healingsunhaven.com. Each is cited by content hash, computed from the file itself at the moment it was registered, so you can confirm the copy you receive is the copy we published: Master Data License Agreement `df68fadbfacba877af9f201f093556b3142254dfaa6b17e2f49edbb13dc2a1ed` (sighted 2026-09-18); Order Form `cf05f9286f1335543910902baaf2c6383e34c6d5e579b45c98a57d1a8ec4a525` (sighted 2026-09-18); pricing sheet `edb57000945d602f037aa1dd43af9d3ce0f90f62287ad00f731811ce103a2348` (sighted 2026-09-26).

**Contact:** info@healingsunhaven.com

*Sample of `restatements-v1.6.0`, as-of watermark 2026-09-26 01:08:51. Generated 2026-09-26T20:01:23Z.*

---

© 2026 Healing Sun Haven LLC
