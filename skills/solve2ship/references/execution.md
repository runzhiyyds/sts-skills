# Resources, permissions and isolation

Inspect the current agent's actual model/tools, network policy and execution runtime.
Do not assume an installed skill grants model access, Docker, cloud rights or money.
Use existing authorization; request only missing resources immediately before they
matter. Keep authorized work moving without asking the user to approve routine edits.

Before chargeable API use, identify provider/model, review current official prices,
set a cumulative ceiling in the user's currency, and reserve conservative headroom.
Include generation, evaluation, optimization and serving; use one persistent budget
or explicit delegated allowances, never silently give each branch a fresh budget.
Keep unknown charges reserved and stop affected work on uncertain submissions.
Free/local checks can continue. No credit-card, subscription or account changes.

Keep keys out of chat, source, command arguments, browser storage, logs and bundles.
Use the host's secret facility when available, otherwise an owner-only local profile
with its plaintext limitation disclosed. Never print it to diagnose connectivity.

Generated code and model loading need an appropriate isolated execution service:
non-root, bounded CPU/memory/time/output, controlled network/files, no controller key
or Docker socket inside the candidate environment. Review actual permissions and
verify the boundary before running. A host process/venv is not a generated-code
sandbox. Docker alone is not proof of hardened public multi-tenant isolation.

Business-facing help when a runtime is absent: “To test the generated program
safely, please start Docker Desktop. I can prepare the alternatives and checks
while you do that.” The agent should inspect/setup permitted details itself; do
not hand the user a long technical checklist unless they request one.

Respect resource-specific approval requirements. Prefer local delivery unless the
user requests and authorizes hosting. A local listener is not a public deployment.
