# HSH Intelligence — Transparency Log

Every daily Merkle root over the HSH Intelligence SEC EDGAR corpus.
**Append-only. Public. Independent of us.**

## What this is for

A buyer holding one record from our corpus can prove it was in a given day's batch **without trusting us and without holding the rest of the data** — using roughly log2(n) hashes, or 13 for a day of 5,329 records.

Vendors publish datasheets, which are claims. A Merkle root is a proof. If we altered any record after publication, the root would not match, and anyone holding a proof could see it.

**And the root has to come from somewhere you trust more than us.** That is the whole reason this repository is public and separate from ours: each entry is timestamped by its git commit, a date recorded by GitHub rather than asserted by HSH. A root we hand you alongside the data proves nothing you did not already have to take on faith — you would be trusting us twice, once for the data and once for the number you check it against.

## How to verify one record

```
# 1. the proof for your record, from our read API
curl -s https://api.hshintelligence.com/v1/filings/<identity>/proof > proof.json

# 2. the root for that day, from THIS repository — not from us
curl -s https://raw.githubusercontent.com/hshintelligence/hsh-transparency/main/ROOTS.jsonl > roots.jsonl

# 3. fold it yourself
python3 verify_merkle_proof.py --proof proof.json --roots roots.jsonl
```

`verify_merkle_proof.py` is **standard library only** and imports nothing of ours. Read it in two minutes.

    sha256(verify_merkle_proof.py) = 06aa983ea2fbb7344a8dc6a999a1e03f202cf2224f14a59d29afbcd2496bc568

That hash is published here so you can confirm the file you downloaded is the file we published. It is also in `SHA256SUMS`.

## The full verification kit

`verify_merkle_proof.py` above does check 3 — Merkle membership — and nothing else. `verify.py` in this repository is the **complete four-check kit**: file integrity, manifest integrity, Merkle membership and split disjointness.

**Take it from here rather than from the copy inside your release.** The kit uploaded beside every release published before 2026-08-27 predates the `--roots` option, so it can only check a proof against a root we handed you in the same breath — which is the thing this repository exists to stop. Those copies are not being replaced: their `sha256` is recorded in the `MANIFEST.txt` beside them, and rewriting a file a manifest binds is indistinguishable from tampering. The current one lives here.

    sha256(verify.py) = 7f138e812c78b328ae21046493546d73e085ee0fd6183b2ed338fd8e6ab0db05

It is standard library only, except that check 4 reads Parquet and uses `pyarrow` if you have it — reporting NOT CHECKED if you do not. The other three checks never import it.

## THE TWO ALGORITHMS

**Read this before computing anything.** Two algorithms appear in this log. They hash the same payload differently and produce completely different roots. Every entry in `ROOTS.jsonl` and every proof from the API carries an `algo` field, and that field — not the date, not an assumption — selects which of the two applies.

### Both share the same leaf payload

```
payload = identity + NUL + content_hash + NUL + bronze_key
```

where NUL is a single 0x00 byte and the three fields are UTF-8. The leaf binds the record's IDENTITY, not only its content: hashing the payload alone would let a record be moved between days and still verify, against the wrong batch, which is exactly the tampering this exists to detect.

### `sha256-carry-v1`

```
leaf(record)  = sha256(payload).hexdigest()
join(a, b)    = sha256((a + b).encode('utf-8')).hexdigest()
```

* leaves are hashed with **no prefix**
* interior nodes concatenate the **hex strings**, not the raw digests
* the tree is built level by level, pairing left to right
* **an odd node at any level is CARRIED to the next level, never duplicated.** Duplication is the classic Merkle forgery: it lets a different leaf set produce an identical root

### `sha256-rfc6962-v2`

RFC 6962 section 2.1, followed exactly.

```
leaf(record)  = sha256(b'\x00' + payload)
join(a, b)    = sha256(b'\x01' + bytes.fromhex(a) + bytes.fromhex(b))
```

* leaves carry a **0x00** prefix, interior nodes a **0x01** prefix
* concatenation is of **RAW BYTES**, not hex strings
* the tree splits at the **largest power of two strictly below n**, recursively — it is not built level by level
* **there is NO carry rule.** Do not carry an odd node; the split handles it

### Which days use which

| algorithm | days |
|---|---|
| `sha256-carry-v1` | 2026-08-13, 2026-08-14, 2026-08-15, 2026-08-16, 2026-08-20, 2026-08-21 |
| `sha256-rfc6962-v2` | 2026-08-22, 2026-08-25, 2026-08-27, 2026-08-28, 2026-08-29, 2026-09-01, 2026-09-02, 2026-09-03, 2026-09-04, 2026-09-05, 2026-09-06, 2026-09-07, 2026-09-09, 2026-09-10, 2026-09-11 |

`tree_depth` in the table below counts levels **including the leaves**: 23 leaves is depth 6, 5,329 is depth 14. It is informational — the proof path length is what a verifier uses — and it is stated here so it is not one more thing to guess. For `sha256-rfc6962-v2` the tree is not built level by level and the figure is recorded as the recursion depth.

The change was made on 2026-08-23. Roots published before it are `sha256-carry-v1` and are **not** re-computed under the new rule — a published root is never rewritten, so both algorithms remain load-bearing for as long as anyone holds a proof from that period.

## Roots

| Day | Records | Depth | Algorithm | Root |
|---|---|---|---|---|
| 2026-08-13 | 23 | 6 | `sha256-carry-v1` | `7cb336e73086977a2276958bd6ce5c85a235fea3c9edd6aecb0f54c916c325cd` |
| 2026-08-14 | 5,329 | 14 | `sha256-carry-v1` | `ace5928cd7f2e6d80779739007e2dbb7c3504e1cb9de220dc0acc93db0b827a4` |
| 2026-08-15 | 616 | 11 | `sha256-carry-v1` | `5f8738aad4a5a01f3a5d9bab03be3e71565e15cf54ae93f5c37e138e067eacd2` |
| 2026-08-16 | 4,955 | 14 | `sha256-carry-v1` | `9e10c01aa1a447fbc22851b64a42fe78098c503ddf70962126b3cc58e2f67084` |
| 2026-08-20 | 4,155 | 14 | `sha256-carry-v1` | `ce4b47a7d705b3b5c9e2e5ba81b2e7e0f02a94bae6ad114150537826b6effe74` |
| 2026-08-21 | 33 | 7 | `sha256-carry-v1` | `82054e35dd2065fd6d29a624c82a3f0f937c64180242944400feef0c5fb6b939` |
| 2026-08-22 | 429 | 10 | `sha256-rfc6962-v2` | `015bb9cb3540fa2befa9aa2826076c24cafdf808aba443b503ac2f60adff3bc3` |
| 2026-08-25 | 154 | 9 | `sha256-rfc6962-v2` | `977aa8bb9b0cdaa6f9d3ba7d83d2c71d9983f695214727b118ebb9ed380cb6da` |
| 2026-08-27 | 382 | 10 | `sha256-rfc6962-v2` | `8ef597d608c10c1ed25d1c5c34860ed030dd1a030debd56fbba40574521cf7cc` |
| 2026-08-28 | 216 | 9 | `sha256-rfc6962-v2` | `88fbd868e656e31f69ee17f337661d383cc4c6af31737832d07357964874710f` |
| 2026-08-29 | 196 | 9 | `sha256-rfc6962-v2` | `18c0ff42dab9407cfe1799f2bb1efa8b3717f6a5863dfe62561055576296e3a6` |
| 2026-09-01 | 199 | 9 | `sha256-rfc6962-v2` | `6fb0574e3b5257c9a21e3f652409f249e9829c8f7e21ed955291da0d160b4b1e` |
| 2026-09-02 | 535,995 | 21 | `sha256-rfc6962-v2` | `3ca9a355f2e1b6917f49a37ddf9fb7e51ba3f5f635b44c3029736829ef7e57f1` |
| 2026-09-03 | 455,998 | 20 | `sha256-rfc6962-v2` | `2dbe81e240f4369d4ebc3f8479528fde05173248ec2e6c8855bac08700d7632e` |
| 2026-09-04 | 574,738 | 21 | `sha256-rfc6962-v2` | `4913c23f68c10e337685665d56ca70afbe9220f4205f9395263002a4278f6d69` |
| 2026-09-05 | 1,726,310 | 22 | `sha256-rfc6962-v2` | `14d039df6ffeda5e1d11ee993ec6e2d9a1067050bca07490fce9063882908afc` |
| 2026-09-06 | 2,907,115 | 23 | `sha256-rfc6962-v2` | `d6fdcb6b4cc6b81d5b3edf98be3f296d0f74e8059ec8bde27dbb1ec6abd5a917` |
| 2026-09-07 | 365,900 | 20 | `sha256-rfc6962-v2` | `639ad4b4cfa044879dad50fa7534655b21139aa8c3b7777750184abec67012cf` |
| 2026-09-09 | 1,869 | 12 | `sha256-rfc6962-v2` | `08cfb4c2a5c6c0e4a599845c3b1e6732244634e3ef5526fbdaa8bb4b27c7e300` |
| 2026-09-10 | 1,578 | 12 | `sha256-rfc6962-v2` | `6173f1fd071d98ab4fdd700411e9b9e5a8237d5da17c27dde7f50feaed148a9e` |
| 2026-09-11 | 1,731 | 12 | `sha256-rfc6962-v2` | `e5358b8b465ec02df93152aaf23dc37665a52bf8d31e96258284d85593839de1` |

## Days with no root

Listed explicitly rather than omitted. A log with unexplained gaps reads as concealment; these are days the factory ingested nothing, measured against the register rather than left blank.

| Day | Records ingested | Reason |
|---|---|---|
| 2026-08-17 | 0 | no records were ingested on this day |
| 2026-08-18 | 0 | no records were ingested on this day |
| 2026-08-19 | 0 | no records were ingested on this day |
| 2026-08-23 | 0 | no records were ingested on this day |
| 2026-08-24 | 0 | no records were ingested on this day |
| 2026-08-26 | 0 | no records were ingested on this day |
| 2026-08-30 | 0 | no records were ingested on this day |
| 2026-08-31 | 0 | no records were ingested on this day |
| 2026-09-08 | 0 | no records were ingested on this day |

A day is only eligible for a root once it has closed. The current day will appear here after it does; a root published over a batch that can still grow would be wrong by the next record admitted.

## What this log does NOT prove

* **It does not prove a record is accurate.** It proves the record was in the batch we committed to on that day and has not changed since. What the filer wrote is a separate question, and our disclosures about it are in the state document that ships with each release.
* **It does not cover records we never ingested.** A day with no root above is a day nothing was admitted, not a day something was hidden.
* **The commits here are not cryptographically signed.** The timestamp is GitHub's, which is a third party, and that is the property this log needs. Signing would upgrade "GitHub says this date" to "HSH attested this date"; it is not in place yet and this sentence will be removed when it is.

_Generated 2026-09-13T09:53:59.428143+00:00_
