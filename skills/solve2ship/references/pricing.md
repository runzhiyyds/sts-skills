# Price review and readiness

Use this reference when the optional STS bridge reports unavailable, expired or
inconsistent pricing. Price readiness, model credentials and a spending budget are
separate checks. An existing API key or balance does not satisfy the other two.

## Inspect without spending

From this installed skill, run:

```sh
python3 scripts/sts_bridge.py status
# Chinese messages; the default language is English:
python3 scripts/sts_bridge.py --language zh-CN status
```

The bridge reads `/api/model-status` from the existing local engine and returns
`pricing.ready`, `reason`, `active_version_id`, `valid_from` and `expires_at`.
It omits credentials, rates and source-document contents. Model configuration is
not a verified provider connection; token estimates are not verified invoices.
New paid actions require STS v0.16+ pricing fields. Older/malformed responses cannot
be treated as ready; inspection, existing receipts and supported free operations
remain available.

## Resolve an unavailable review

Use the installed engine's price-review commands from its repository directory,
with the same private state location it normally uses:

```sh
PYTHONPATH=src python3 -m solve2ship pricing-status
PYTHONPATH=src python3 -m solve2ship pricing-preview --pricing-file /private/price-review.json
PYTHONPATH=src python3 -m solve2ship review-pricing --pricing-file /private/price-review.json --reviewed-sha256 REVIEWED_CANONICAL_HASH
```

These are local commands, not model requests. Replace placeholders only after
checking the actual current official provider source, model, endpoint, currency,
rate units, context limit and UTC validity window. Use the engine's versioned
[configuration instructions](https://github.com/runzhiyyds/solve2ship/blob/main/docs/USAGE.md)
for the document schema and state-directory options. Files remain owner-only and
outside Git. Never include a key in a price document or command argument.

Preview validates the document and computes its canonical hash. The source-page
hash is a review assertion, not automatic proof of an official current rate. Import
explicitly activates that reviewed version within the existing task authorization;
the bridge never imports or renews a review. Do not move expiration dates without
checking the source again. An unreadable source or uncertain price is a reason to
keep paid work paused and continue local implementation or evidence review.

The engine stores immutable price versions and per-call snapshots. The seven-day
maximum validity in v0.16 is a local review policy, not a provider guarantee. New
versions must not rewrite historical charges, unresolved reservations or delegated
service allowances. Never delete state, reauthorize extra money or create a new
ledger to make a price error disappear. Standalone model services use their own
external state and the price commands shipped with that service's runtime version.

After a valid import, inspect bridge status again. A preflight refusal made no POST
and claimed no journal operation, so that still-unsubmitted intent can be attempted
with its original operation ID when genuinely ready. A request already submitted
and refused/uncertain stays fenced; inspect its saved receipt instead of changing
the ID. Successful saved receipts do not require new prices or another model call.

## Explain it in business language

“The recorded model prices need checking before we spend more. Your budget and
previous work are preserved. I can review the current official rates and prepare
the local update; until then I can continue work that does not call the model.”

中文：“记录的模型价格需要重新核对，才能继续花费。你的预算、用量和已有成果都保留。
我可以核对当前官方价格并准备本机更新；这期间可以继续不调用模型的工作。”

Price review does not install or start a runtime. Generated code still requires
accepted isolation: Colima with Docker Engine/CLI on Apple Silicon macOS, or Docker
Engine on Linux, following the engine's actual acceptance procedure. Docker Desktop
is not required. A running Engine or installed Compose plugin alone does not prove
candidate isolation.
