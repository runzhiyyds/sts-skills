# Optional headless STS engine bridge

Use this path only when the user has an installed, trusted STS engine running on
this machine. The skill does not install/start the engine, grant a budget or bring
its own model/runtime. Without that resource, continue with other approved local
capabilities or explain what is missing. No frontend is required for this bridge.
The current API compatibility target is STS v0.14+; v0.13 supports read-only status
but lacks the safe model-readiness/review routes. Verify the actual engine response.

Run `scripts/sts_bridge.py --help` from this installed skill directory. It uses only
Python 3.10+ stdlib. URLs are restricted to HTTP loopback, localhost is normalized to
127.0.0.1, proxies/redirects are disabled, response sizes are bounded. It never reads
model-profile files, executes candidates, installs packages or changes authorization.
Mutation journals use owner-only local SQLite on reviewed POSIX hosts; keep that
state through restart, outside distributable bundles. It is not a production vault.

## Inspect before acting

    python3 scripts/sts_bridge.py --url http://127.0.0.1:8000 status
    python3 scripts/sts_bridge.py --url http://127.0.0.1:8000 tasks
    python3 scripts/sts_bridge.py --url http://127.0.0.1:8000 searches
    python3 scripts/sts_bridge.py --url http://127.0.0.1:8000 show --search-id SEARCH_ID

English is the helper default; use `--language zh-CN` before the command for Chinese
messages. Give the business user the result in their own language. Summaries omit
raw samples, generated program text and observed outputs. Explicit `show
--evidence-file /private/search.json` saves bounded, defensively redacted evidence
owner-only without overwriting existing files. Treat this as private user data,
not automatically safe public material. Redaction is not a complete secret audit.

Model readiness means configured, not a successful network connection or current
price review. STS enforces its actual provider/date/budget/runtime gates. Docker is
required only by appropriate code/ML/workflow/tool families, not every simple route.

## Save a reviewed task without launching paid work

Prepare a STS task-definition JSON file from the actual user's samples and desired
outcome. Use task inputs as data, never include keys. Preview does not start search:

    python3 scripts/sts_bridge.py preview --definition /private/task.json
    python3 scripts/sts_bridge.py save --definition /private/task.json --reviewed-sha256 HASH_FROM_PREVIEW --operation-id save-task-1

Check the user's intended goal/counts/budget before saving the reviewed hash. A
changed file fails closed. The saved task summary is not proof of exploration.
Do not create a new task to reuse final inputs already consumed by an earlier task.

Task-definition shape (illustrative inputs, not evaluated business evidence):

```json
{
  "title": "Route customer requests",
  "samples": [
    "Where is my parcel?",
    "Please change my delivery address",
    "The package has not arrived",
    "Can you check tomorrow's delivery?",
    "I would like a refund",
    "My returned item reached your warehouse",
    "Please explain the return procedure",
    "When will my refund arrive?",
    "Are there discounts for new customers?",
    "What are your opening hours?"
  ],
  "output_specification": "Return JSON with one key, category, whose value is delivery, refund, or other. Route shipment or address questions to delivery; return/refund questions to refund; remaining questions to other.",
  "labels": [],
  "budget": {"mode": "explicit", "max_cost_cny": 1, "max_candidate_executions": 40}
}
```

Replace the sample data and outcome with the actual request. At least ten distinct
input groups are needed for the engine's train/validation/final holdout protocol;
ten rows with duplicates may not qualify. A shorter dataset can be saved, but cannot
be assumed to support independent final acceptance. `samples` contains JSON values
directly, not wrappers with an invented `input` field. Optional labels have shape
`{"sample_index": 0, "expected_output": {"category": "delivery"}}` within the
`labels` list. They are user-provided, unverified labels; never invent them.

The shown CNY1/40-attempt cap is an example, not permission to spend. Set task caps
from the user's existing authorization; zero remains disabled. A user-authorized
existing global work budget may instead be inherited with
`"budget": {"mode": "inherit_work"}`. Inheritance does not create that global
authorization and must not be used to bypass a zero/expired/consumed budget. Empty
engines can preview/save a task but need genuine configured resources and budget
before exploration. Do not silently install or grant those resources.

## Explicit exploration and recovery

Only with existing model configuration, positive remaining engine authorization,
a task budget that allows work, and user-authorized API use:

    python3 scripts/sts_bridge.py start --task-id TASK_ID --revision 1 --operation-id explore-1 --allow-paid

`--allow-paid` records an explicit command; it is not a new budget. The existing STS
root/global ceilings, model price review and accepted execution runtime still apply.
Automatic bounded iteration is the engine's policy. Optional explicit `evolve`,
`reactivate` and `restore` also require `--allow-paid` and an operation ID; inspect
actual evidence and budget before choosing them. Cancellation does not undo charges:

    python3 scripts/sts_bridge.py cancel --search-id SEARCH_ID --operation-id cancel-1
    python3 scripts/sts_bridge.py operation --operation-id explore-1

Keep one operation ID per intended action. First submission is claimed locally
before HTTP. Saved success returns its receipt without another POST. Changed
payload/engine conflicts; failed/interrupted/uncertain IDs stay fenced. Do not
change IDs, clone/delete state or automatically retry to bypass a refusal. Inspect
engine searches/evidence and reconcile what actually happened. A queue receipt is
not completed execution. The journal never resets/duplicates the engine budget.

## Quality review from actual user judgments

`reviews --search-id ID` reads a summary. For the actual cases and immutable hashes:

    python3 scripts/sts_bridge.py review-packet --search-id SEARCH_ID --phase validation --output /private/review.json

Present the cases in business language and obtain the user's actual accept/reject/
unsure judgments. The agent must not generate answers from its own model score or
claim that a fixture, schema check or agent opinion is human review. Review identity
is self-attested, not verified ground truth or a calibrated evaluator guarantee.

Only after explicit user judgments, put one answer in a private JSON file with
`execution_id` (validation) or `sample_index` (final), `snapshot_sha256`,
`previous_review_id` (null or the actual latest ID), `verdict`, `reviewer`, `comment`
and `attested`. Do not fill `attested: true` without the user's explicit assertion
that they reviewed those outputs. The helper supplies only a durable request ID:

    python3 scripts/sts_bridge.py review-submit --search-id SEARCH_ID --phase validation --answers /private/user-answer.json --operation-id review-case-1

For an explicitly chosen operator-review final gate, `prepare-final --search-id ID
--operation-id final-1 --operator-review` runs once and seals the data. A known
deterministic winner can do so without model access or a new model allowance. A
model-backed or unknown family additionally requires `--allow-paid` and existing
model/budget readiness; the engine still enforces its exact runtime and price rules.
Never choose this gate merely to bypass missing quality labels.
Use `review-packet --phase final` only after freeze, collect actual user feedback,
then submit those final reviews. Do not optimize against exposed final cases.

Explicit completion uses a fresh final packet's `review_evidence_sha256`, actual
`reviewer`, `comment` and `attested` in a private decision file. The user must intend
to finalize those judgments, not just discuss them. `complete-review --search-id ID
--answers /private/user-decision.json --operation-id final-decision-1` asks the engine
to close the gate; it does not invent a verdict. Missing/unsure/stale feedback and
failed outputs remain subject to the engine's rules. Rejection is a valid retained
outcome. Review feedback does not authorize fresh paid optimization automatically.

## Obtain an already accepted service

    python3 scripts/sts_bridge.py delivery --search-id SEARCH_ID
    python3 scripts/sts_bridge.py download --search-id SEARCH_ID --output /private/service.zip

Download is read-only, requires the final quality gate to be exactly true, an
accepted export receipt and matching archive SHA256, and refuses to overwrite a
file. Archive integrity alone does not establish quality acceptance. It never
extracts or runs code. Startup,
independent runtime/credentials/budget and service acceptance remain as described
in [delivery](delivery.md). A local archive is not a public/cloud deployment.
