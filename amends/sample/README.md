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

**5,079 rows drawn from a 15,326,990-row commercial dataset.** Signed, and verifiable in about two minutes without contacting us.

> **This is a sample of a paid product.** It is published so a data team can evaluate the real thing — the real schema, the real values, the real verification chain — before any conversation about licensing. It is not open data and it is not a free tier. Licence terms are below.

---

| | |
|---|---|
| **Run the checks** | [Colab notebook](https://colab.research.google.com/github/hshintelligence/hsh-transparency/blob/main/amends/notebook/hsh-amends-verify-and-explore.ipynb) — verifies this sample against a second host, then explores it |
| **Trust anchor** | [hshintelligence/hsh-transparency](https://github.com/hshintelligence/hsh-transparency/tree/main/amends) — the signing key, its fingerprint, and the signed record of every release |
| **Documentation** | [Open the folder](https://drive.google.com/drive/folders/1c3qzgAFHef1lyTfRYQi5gpqIHXbCyhAn?usp=sharing) — the data dictionary, release history, schema stability note, datasheet and audit report, in one folder |
| **Who we are** | [hshintelligence.com](https://hshintelligence.com) |
| **Licensing** | [info@healingsunhaven.com](mailto:info@healingsunhaven.com) |

## Why this dataset exists

**The SEC does not record which filing amends which.** An amended filing arrives as a new submission with a new accession number and an `/A` suffix, and nothing in the index says what it supersedes. Every vendor who offers an amendment chain has inferred it.

So have we. The difference is what happens next: we measure the inference against the filing documents themselves — a channel the matching rule cannot see, because the rule works on index metadata and the measurement reads the text — and we publish the result per stratum, with its denominator, including the strata that failed and were withdrawn.

A precision figure with no denominator is a claim. One with its population, its sample, its interval and its method is a measurement. Everything below is the second kind.

## Who this is for

| | |
|---|---|
| **Quantitative research** | Restatements and amendments are look-ahead traps: the amended figure was not knowable on the original filing date. `first_seen_at` and `version_seq` let a backtest use what was actually visible at the time. |
| **Compliance and audit** | One row per (filer, filing) with an explicit state for every amendment — linked, or a named reason it is not. Unresolved cases are enumerated rather than dropped. |
| **AI and model providers** | Every row carries its provenance: source URL, licence, crawler version, contract version and the pipeline commit that produced it. The manifest is signed and the record hashes are verifiable offline. |
| **Academic research** | A reproducible corpus with a published method, a signed coverage attestation, and an append-only transparency log on a host that is not ours. |

## Dataset summary

| | |
|---|---|
| Records | **15,326,990** — one per (filer, filing) |
| Filings | 10,848,021 distinct accession numbers |
| Companies | 742,056 distinct CIKs |
| Date range | 2009-01-02 to 2026-08-28 |
| Format | Apache Parquet, 3 part(s) |
| Size | 1.2 GB |
| Release | `restatements-v1.5.0` (as-of watermark 2026-09-16) |
| Cadence | quarterly |
| This sample | 5,079 rows, published free for evaluation |

## What the dataset is

An amendment index over SEC EDGAR at filing grain: one row per (filer, filing). For each filing it states whether the filing is itself an amendment, whether anything known supersedes it, its position in a version chain, and — where the amended filing can be identified — which filing it amends, with the method and a confidence.

**The central limitation is stated first:** the amendment chain resolves for a small minority of amendments. The rest carry a NAMED REASON rather than a blank. An unlinked amendment we can name is worth more than a linked one we guessed.

## Verify it before you read it

```bash
python3 verify_sample.py .
```

Three checks, all byte-level and all identical to what applies to the full product:

1. files against the manifest header
2. every record's payload against its payload_sha
3. the manifest signature

The key fingerprint is published in the [HSH transparency repository](https://github.com/hshintelligence/hsh-transparency/tree/main/amends) — a different host, append-only. Fetch the key from there rather than from here, and the two would have to collude to fool you. That is the whole design: **where you fetch from and where you anchor trust are different questions.**

A Colab notebook does all of it in order — verification first, data second: [open the notebook](https://colab.research.google.com/github/hshintelligence/hsh-transparency/blob/main/amends/notebook/hsh-amends-verify-and-explore.ipynb).

**The notebook is a convenience, and it is worth saying what that means.** It runs the same checks you would run by hand, but it is also the thing telling you they passed. A reader who wants certainty should run the four commands themselves — fetch from the dataset host, fetch the key from the anchor, compare the fingerprint, verify the signature — which is what `verify_sample.py` does. No arrangement of hosts fixes this: a notebook on a third host would still be the thing reporting its own result.

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
| `tokens` | `BIGINT` | Token count of the payload, for sizing a language-model workload. Not a quality signal |
| `cik` | `VARCHAR` | SEC's Central Index Key for the filer, unpadded |
| `cik10` | `VARCHAR` | The same CIK zero-padded to ten characters — SEC's own conventional form |
| `accession` | `VARCHAR` | SEC's accession number for the filing, canonical (digits only, no dashes). With `cik` it identifies a filing uniquely |
| `company_name` | `VARCHAR` | The filer's name as SEC recorded it on this filing |
| `filed_at` | `VARCHAR` | The date SEC assigned to the filing. NOT the moment it became public — see `first_seen_at` in the payload |
| `pipeline_sha` | `VARCHAR` | The commit whose code produced this row |
| `source_url` | `VARCHAR` | The SEC EDGAR URL this row was derived from. Every row resolves; the audit checks the template against its own ids |
| `licence` | `VARCHAR` | The licence this row is published under |
| `crawler_version` | `VARCHAR` | Version of the acquisition code |
| `contract_version` | `VARCHAR` | Version of the data contract this row satisfies |
| `jurisdiction` | `VARCHAR` | The jurisdiction of the source filing |
| `quality_flags` | `VARCHAR[]` | Per-row quality markers. An empty list means no flag was raised for this row |

`payload` is a JSON object holding the analytical fields — `link_state`, `amends_accession`, `link_basis`, `link_confidence`, `version_seq`, `is_latest`, `period` and the rest. The flat CSV in this package explodes them into columns as a convenience; the Parquet schema above is the product.

**Full data dictionary — every column, every payload field, measured null rates and the caveats attached to each — is available on request with the licence terms.**

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

**Its verdict is bound into the hashed manifest.** The audit report is part of the release, so recomputing the manifest digest recomputes the accuracy claim along with the data. It is inside the thing being verified rather than beside it, which means it cannot be quietly revised after the fact without the signature failing.

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

**81 chains in this sample close inside it** — both the amendment and the filing it amends are present. That happens in `10-KT` and `10-QT`, which are drawn on base form alone, so the originals arrive with the amendments. Every other stratum draws the amendments only, so their targets sit in the full dataset rather than here. Wherever `link_state` is `linked`, the target exists.

**Verify it.**

```bash
python3 verify_sample.py .
```

## What a sample cannot prove, and what we do about it

A subset establishes nothing about its superset. Coverage, denominators and recall bounds are statements about the whole corpus, so they are published as a **signed attestation** — `COVERAGE-ATTESTATION.json`, signed with the same key — carrying every stratum's population, reachable frame, measured precision and claim type.

You can therefore check our coverage claims without us handing over the data they describe.

| stratum | population | frame reachable | precision | claim type |
|---|---:|---:|---:|---|
| `10-K` | 19,923 | 19,582 (98.29%) | **99.33%** | sampled — [97.58, 99.82] |
| `10-Q` | 18,221 | 18,086 (99.26%) | **100.00%** | sampled — [98.71, 100.00] |
| `20-F` | 2,192 | 2,112 (96.35%) | **100.00%** | sampled — [98.64, 100.00] |
| `40-F` | 310 | 290 (93.55%) | **100.00%** | census — every member examined |
| `11-K` | 241 | 233 (96.68%) | **100.00%** | census — every member examined |
| `10-KT` | 72 | 72 (100.00%) | **98.48%** | census — every member examined |
| `10-QT` | 9 | 9 (100.00%) | **100.00%** | census — every member examined |

4 of these strata are reported as a **census**: every member examined, so there is no sampling risk and no interval is quoted. Quoting one would imply an inference nobody made.

### What we withdrew

Strata measured below the floor are **not shipped as linked**. The rows carry a named reason instead.

| link basis | form | population | sampled | confirmed | contradicted | precision | measured | outcome |
|---|---|---:|---:|---:|---:|---:|---|---|
| `index:cik+form` | `10-Q` | 1,377 | 300 | 59 | 102 | **36.65%** | 2026-09-11 | HOLD |
| `index:cik+form` | `10-K` | 1,013 | 300 | 179 | 52 | **77.49%** | 2026-09-11 | HOLD |

These are **historical readings**, and the date matters. They were measured before our sampling draw was made deterministic, and they cannot be re-derived — the links they describe were withdrawn and no longer sit in a state that asserts a link, so the audit no longer examines them. We publish them dated rather than re-deriving something that no longer exists, because what we measured and then withheld is evidence you cannot get anywhere else.

## What is in the sample, and how it was sized

**5,079 rows** across **126 form types**, carrying **1,672 links in 1,570 distinct chains**.

The rule is: **stratified deterministic draw, census strata complete, every other stratum floored to a minimum evaluable mass, every link state represented.**

**The unit is the chain within a stratum, not the row.** Your smallest natural filter is a stratum — *show me 40-F/A* — and a sample becomes a screenshot the moment that filter returns too few chains to judge. So each stratum is drawn to whichever is largest of its target, the N that yields 150 units, and the N at which **every year present in that stratum has appeared**. Ordering is `md5(record_uid)` throughout and the draw is only ever extended, never hand-picked, so anyone holding the release reproduces it exactly.

A uniform percentage would not do this. A 1% draw is ~153,000 rows carrying roughly 410 linked rows across 7 strata and 18 years — about 3.3 chains per stratum-year. 30 times the size of this sample and less evaluable, because a percentage is blind to where the information lives.

| stratum | rows | chains | years covered |
|---|---:|---:|---:|
| 10-KT (complete) | 459 | 56 | 18 of 18 |
| 10-QT (complete) | 96 | 9 | 17 of 17 |
| unverifiable_at_release (complete) | 4 | no links | 1 of 1 |
| no_prior_filing_in_corpus | 689 | no links | 18 of 18 |
| unresolved_prior_exists | 250 | no links | 18 of 18 |
| 10-K linked | 350 | 350 | 18 of 18 |
| 10-Q linked | 350 | 350 | 18 of 18 |
| 20-F linked | 350 | 344 | 18 of 18 |
| 40-F linked | 300 | 268 | 18 of 18 |
| 11-K linked (complete) | 241 | 193 | 18 of 18 |
| unknown_subject | 900 | no links | 18 of 18 |
| not_an_amendment | 1,100 | no links | 18 of 18 |

Every stratum covers every year its population covers. That is the half of the rule a row count cannot show, so it is measured here rather than asserted.

It is **not a random sample** — rare states are over-represented on purpose, so you can see the states we disclose rather than only the easy case. Both figures are given so the distortion is visible:

| link_state | in sample | in the full dataset |
|---|---:|---:|
| `linked` | 1,672 | 40,968 |
| `not_an_amendment` | 1,556 | 13,864,746 |
| `unknown_subject` | 900 | 1,417,391 |
| `no_prior_filing_in_corpus` | 695 | 1,273 |
| `unresolved_prior_exists` | 252 | 2,608 |
| `unverifiable_at_release` | 4 | 4 |

**4 strata are included complete** — every row of them: `10-KT`, `10-QT`, `unverifiable_at_release` and `11-K linked`. A sample of a complete stratum is a contradiction, so those are not sampled.

That is a different property from the **4 strata the coverage attestation reports as a census** (`40-F`, `11-K`, `10-KT` and `10-QT`), which says the AUDIT examined every reachable row of them. They are not the same list: `40-F` is a census in the audit and sampled here, at 300 of 310.

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
| `verify_sample.py` | the three checks, stdlib only |

## Licence and terms

This sample is provided for **evaluation**. It is not redistributable and confers no rights to the full dataset. The full product is licensed commercially under a Master Data Licence Agreement with a per-deal Order Form; pricing and terms are available on request.

**Contact:** info@healingsunhaven.com

*Sample of `restatements-v1.5.0`, as-of watermark 2026-09-16 10:01:40. Generated 2026-09-17T14:01:48Z.*
