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

**5,645 rows drawn from a 15,326,990-row commercial dataset.** Signed, and verifiable in about two minutes without contacting us.

> **This is a sample of a paid product.** It is published so a data team can evaluate the real thing — the real schema, the real values, the real verification chain — before any conversation about licensing. It is not open data and it is not a free tier. Licence terms are below.

---

| | |
|---|---|
| **Run the checks** | [Colab notebook](https://colab.research.google.com/github/hshintelligence/hsh-transparency/blob/main/amends/notebook/hsh-amends-verify-and-explore.ipynb) — verifies this sample against a second host, then explores it |
| **Trust anchor** | [hshintelligence/hsh-transparency](https://github.com/hshintelligence/hsh-transparency/tree/main/amends) — the signing key, its fingerprint, and the signed record of every release |
| **Documentation** | [Open the folder](https://drive.google.com/drive/folders/1c3qzgAFHef1lyTfRYQi5gpqIHXbCyhAn?usp=sharing) — the datasheet, data dictionary, audit report, release history, schema stability note, product due diligence questionnaire, corrections policy, legal one-pager and errata & release history |
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
| Format | Apache Parquet, 3 parts |
| Size | 1.2 GB |
| Release | `restatements-v1.5.1` (as-of watermark 2026-09-17) |
| Cadence, observed | **6 releases between 2026-09-10 and 2026-09-17** — 7 days |
| Cadence, committed | Stated in the commercial terms, not here. This page reports what has been published; what will be published on what schedule is a contractual commitment and is made there. |
| This sample | 5,645 rows, published free for evaluation |

## What the dataset is

An amendment index over SEC EDGAR at filing grain: one row per (filer, filing). For each filing it states whether the filing is itself an amendment, whether anything known supersedes it, its position in a version chain, and — where the amended filing can be identified — which filing it amends, with the method and a confidence.

**The central limitation is stated first:** the amendment chain resolves for a small minority of amendments. The rest carry a NAMED REASON rather than a blank. An unlinked amendment we can name is worth more than a linked one we guessed.

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

The key fingerprint is published in the [HSH transparency repository](https://github.com/hshintelligence/hsh-transparency/tree/main/amends) — a different host, append-only. Fetch the key from there rather than from here, and the two would have to collude to fool you. That is the whole design: **where you fetch from and where you anchor trust are different questions.**

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
| `source_url` | `VARCHAR` | The SEC EDGAR URL this row was derived from. Every row resolves; the audit checks the template against its own ids |
| `licence` | `VARCHAR` | The licence this row is published under |
| `crawler_version` | `VARCHAR` | Version of the acquisition code |
| `contract_version` | `VARCHAR` | Version of the data contract this row satisfies |
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

**65 amendment chains close inside this sample** (81 amendment rows resolve to an original that is also here; several amendments share an original, which is why the two numbers differ) — both the amendment and the filing it amends are present. That happens in `10-KT` and `10-QT`, which are drawn on base form alone, so the originals arrive with the amendments. Every other stratum draws the amendments only, so their targets sit in the full dataset rather than here. Wherever `link_state` is `linked`, the target exists.

**Verify it.**

```bash
python3 verify_sample.py .
```

## What a sample cannot prove, and what we do about it

A subset establishes nothing about its superset. Coverage, denominators and recall bounds are statements about the whole corpus, so they are published as a **signed attestation** — `COVERAGE-ATTESTATION.json`, signed with the same key — carrying every stratum's population, reachable frame, measured precision and claim type.

You can therefore check our coverage claims without us handing over the data they describe.

| stratum | population | frame reachable | examined | confirmed | contradicted | inconclusive | precision | claim type |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `10-K` | 19,582 | *not stated* | 300 | 295 | 2 | 3 | **99.33%** | sampled — [97.58, 99.82] |
| `10-KT` | 72 | *not stated* | 72 | 65 | 1 | 6 | **98.48%** | census — every member examined |
| `10-Q` | 18,086 | *not stated* | 300 | 295 | 0 | 5 | **100.00%** | sampled — [98.71, 100.00] |
| `10-QT` | 9 | *not stated* | 9 | 8 | 0 | 1 | **100.00%** | census — every member examined |
| `11-K` | 233 | *not stated* | 233 | 219 | 0 | 14 | **100.00%** | census — every member examined |
| `20-F` | 2,112 | *not stated* | 300 | 279 | 0 | 21 | **100.00%** | sampled — [98.64, 100.00] |
| `40-F` | 290 | *not stated* | 290 | 282 | 0 | 8 | **100.00%** | census — every member examined |

`frame reachable` **reads *not stated* for 7 of these strata.** This release's bound accuracy lines record a population and not a separately measured reachable frame, so we cannot tell you here how many of its rows hold a document the verifier can read. That is a gap in what this release bound — it is NOT a claim that population and reachable frame are the same number here. Releases cut after 2026-09-17 bind the frame on every line and this column reports it.

`inconclusive` **is examined and undecided, and it is EXCLUDED from the precision denominator rather than counted against it.** Across these strata that is **58 of 1,504 records examined** (3.9%). A precision of 100% on a stratum with inconclusives means every record that COULD be decided was confirmed — not that every record was. The column is here so you can see the size of what was set aside.

4 of these strata are reported as a **census**: every member examined, so there is no sampling risk and no interval is quoted. Quoting one would imply an inference nobody made. A census can still carry inconclusives: those members were examined and produced no verdict.

### What we withdrew

Strata measured below the floor are **not shipped as linked**. The rows carry a named reason instead.

| link basis | form | population | sampled | confirmed | contradicted | precision | measured | outcome |
|---|---|---:|---:|---:|---:|---:|---|---|
| `index:cik+form` | `10-Q` | 1,377 | 300 | 59 | 102 | **36.65%** | 2026-09-11 | HOLD |
| `index:cik+form` | `10-K` | 1,013 | 300 | 179 | 52 | **77.49%** | 2026-09-11 | HOLD |

These are **historical readings**, and the date matters. They were measured before our sampling draw was made deterministic, and they cannot be re-derived — the links they describe were withdrawn and no longer sit in a state that asserts a link, so the audit no longer examines them. We publish them dated rather than re-deriving something that no longer exists, because what we measured and then withheld is evidence you cannot get anywhere else.

## What is in the sample, and how it was sized

**5,645 rows** across **126 base forms** (**163 form types** once amendment suffixes are counted separately), carrying **1,654 links in 1,554 distinct chains**.

The rule is: **stratified deterministic draw, census strata complete, every other stratum floored to a minimum evaluable mass, every link state represented.**

**The unit is the chain within a stratum, not the row.** Your smallest natural filter is a stratum — *show me 40-F/A* — and a sample becomes a screenshot the moment that filter returns too few chains to judge. So each stratum is drawn to whichever is largest of its target, the N that yields 150 units, and the N at which **every year present in that stratum has appeared**. Ordering is `md5(record_uid)` throughout and the draw is only ever extended, never hand-picked.

**You can run that claim rather than take it.** `reproduce_sample.py` rebuilds this sample from the release and the published rules and tells you whether it got the same rows:

    python3 reproduce_sample.py /path/to/release/parquet/

It reports two verdicts, because they are different claims. **ROW SET** is the draw itself — it depends only on the release and the rules in `SAMPLE-COMPOSITION.json`, and a failure there means the sample is not what this page describes. **BYTE-EXACT** is the row set plus the CSV writer: matching our bytes also needs duckdb 1.5.1, which wrote them. Identical rows with different bytes is a quoting difference, not a data difference, and the script says which one you have.

A uniform percentage would not do this. A 1% draw is ~153,000 rows carrying roughly 404 linked rows across the 7 AUDIT strata (a different cut from the 12 sample strata tabulated below) and 18 years — about 3.2 linked ROWS per stratum-year. (Rows, not chains: this release holds 1,654 links in 1,554 distinct chains in the sample, so the two are not interchangeable.) 27 times the size of this sample and less evaluable, because a percentage is blind to where the information lives.

| stratum | rows | chains | years covered |
|---|---:|---:|---:|
| 10-KT (complete) | 459 | 56 | 18 of 18 |
| 10-QT (complete) | 96 | 9 | 17 of 17 |
| unverifiable_at_release (complete) | 588 | no links | 18 of 18 |
| no_prior_filing_in_corpus | 689 | no links | 18 of 18 |
| unresolved_prior_exists | 250 | no links | 18 of 18 |
| 10-K linked | 350 | 350 | 18 of 18 |
| 10-Q linked | 350 | 350 | 18 of 18 |
| 20-F linked | 350 | 343 | 18 of 18 |
| 40-F linked (complete) | 290 | 259 | 18 of 18 |
| 11-K linked (complete) | 233 | 187 | 18 of 18 |
| unknown_subject | 900 | no links | 18 of 18 |
| not_an_amendment | 1,100 | no links | 18 of 18 |
| **total drawn** | **5,655** | | |

**That column sums to 5,655, and the sample is 5,645 rows.** The strata are not disjoint, and three different counts describe that — so each is named:

- **474 rows in this sample satisfy more than one stratum rule.** The census strata are defined on base form and the state strata on link state, so a 10-KT row that is not an amendment satisfies both.
- **10 of those were DRAWN into two strata**, which is the whole of the difference between the column total and the sample. The draws are unioned, so the sample holds each of them once. The rest satisfy a second rule whose own draw did not reach them.
- The largest overlapping pair is **371 rows** that are both *10-KT, every row* and *not_an_amendment*.

The per-stratum figures are the draw sizes, and changing them to make the column add up would break the reproduction above.

Every stratum covers every year its population covers. That is the half of the rule a row count cannot show, so it is measured here rather than asserted.

It is **not a random sample** — rare states are over-represented on purpose, so you can see the states we disclose rather than only the easy case. Both figures are given so the distortion is visible:

| link_state | in sample | in the full dataset |
|---|---:|---:|
| `linked` | 1,654 | 40,384 |
| `not_an_amendment` | 1,556 | 13,864,746 |
| `unknown_subject` | 900 | 1,417,391 |
| `no_prior_filing_in_corpus` | 695 | 1,273 |
| `unverifiable_at_release` | 588 | 588 |
| `unresolved_prior_exists` | 252 | 2,608 |

**5 strata are included complete** — every row of them: `10-KT`, `10-QT`, `unverifiable_at_release`, `40-F linked` and `11-K linked`. A sample of a complete stratum is a contradiction, so those are not sampled.

That is a different property from the **4 strata the coverage attestation reports as a census** (`10-KT`, `10-QT`, `11-K` and `40-F`), which says the AUDIT examined every reachable row of them.

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

This sample is provided for **evaluation**. It is not redistributable and confers no rights to the full dataset. The pricing sheet ships beside these documents. The Master Data License Agreement and Order Form are held and sent on request from info@healingsunhaven.com. Each is cited by content hash, computed from the file itself at the moment it was registered, so you can confirm the copy you receive is the copy we published: Master Data License Agreement `df68fadbfacba877af9f201f093556b3142254dfaa6b17e2f49edbb13dc2a1ed` (sighted 2026-09-18); Order Form `cf05f9286f1335543910902baaf2c6383e34c6d5e579b45c98a57d1a8ec4a525` (sighted 2026-09-18); pricing sheet `2490c3d160d00c7de0d1baac7566ddb48a4d08f47de4859d7989ce1d294eabe5` (sighted 2026-09-18).

**Contact:** info@healingsunhaven.com

*Sample of `restatements-v1.5.1`, as-of watermark 2026-09-17 15:29:36. Generated 2026-09-19T03:52:10Z.*

---

© 2026 Healing Sun Haven LLC
