# Evidence that can support a decision

Create a task-local private state directory; never publish user data or the ledger.
Keep duplicate/related inputs in one split. Freeze the split before optimizing.
The helper below groups exact canonical duplicates; related-user/time/entity grouping
requires the agent's task-specific protocol. Small samples may lack a useful final
holdout. State that limit instead of manufacturing confidence.

Compare actual common-case outputs, failures, cost ceilings and inference latency.
Keep evaluator cost separate. Deterministic/schema checks establish only what they
check. Provided labels may be wrong; uncalibrated judges cannot establish Accuracy,
F1 or independent truth. Get targeted human feedback when it changes a decision.
Do not invent human review or silently turn model-generated labels into truth.

Use early cheap tests to stop broken candidates. Quality pruning needs comparable
cases, sufficient evidence and uncertainty assessment; judges alone should not
permanently eliminate candidates. Retain artifacts and decisions so candidates can
be reactivated. Each edit is a new version, not an overwrite. Report same-validation
improvements as tuning evidence; a regression is a valid result.

## Persistent helper

Run this trusted stdlib helper with Python 3.10+; it never executes candidate code:

    python3 scripts/evidence.py --state-dir /private/task-state init --inputs /path/inputs.json --goal /path/goal.txt --cny 10
    python3 scripts/evidence.py --state-dir /private/task-state reserve --id UNIQUE_OPERATION_ID --purpose candidate_build --ceiling-cny 2
    python3 scripts/evidence.py --state-dir /private/task-state settle --id UNIQUE_OPERATION_ID --cost-cny 0.01
    python3 scripts/evidence.py --state-dir /private/task-state status

Use script paths relative to the installed skill directory. Reserve before external
submission. Submit only when reserve returns created=true. Reused IDs return
created=false and MUST NOT cause resubmission; reconcile the original operation.
If the request's billing/outcome is uncertain, leave it reserved or record uncertain.
A new ID is a new paid operation, not a safe retry. The helper trusts owner-controlled
state and reported costs; it is not provider billing, a secret vault or a scheduler.

Use candidate to bind an immutable artifact hash, record to save real train/validation
observations, freeze to close all search before one-time final work, and final-record
to retain each final outcome once. See --help for arguments. Freeze does not certify
quality: establish task-specific acceptance first. After freeze no candidate addition
or tuning records are allowed. The helper cannot stop an owner from deleting/cloning
state; retain it, and do not create a new task to reuse exposed final inputs.

Record environment/dependency/model IDs, configuration, artifact/data hashes and
receipt provenance alongside observations. A successful local fixture proves its
protocol only. Research or business claims need a matching public/consented dataset,
method, baseline, sample denominator and independent evidence.
