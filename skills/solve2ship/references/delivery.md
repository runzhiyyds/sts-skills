# Deliver something the user can use

Freeze the selected artifact and acceptance protocol before opening the final set.
An exposed final set stays exposed even after reordering, relabeling or changing the
goal. Preserve a failed/interrupted final attempt; do not retune or automatically
replay it. If no reliable final-quality gate exists, state “quality review required”
and offer the smallest relevant feedback step. Do not equate startup with quality.

Package a service the user can call without the search agent/controller or internal
experiment DB. Include source/frozen artifact, exact dependencies, input/output
contract, simple start/stop/call instructions, health check, validation evidence
summary and LICENSE/NOTICE/provenance. Do not bundle raw user datasets, secrets,
private development logs, runtime binaries or a positive paid authorization.

If inference needs a model, configure credentials independently in an owner-only
local state outside the bundle. Authorize serving explicitly and persist usage.
Save one request ID per intended paid operation before submission. Successful repeats
should return a cached result; failed/interrupted IDs should be fenced for review.
Deleting state must not be recommended as a budget reset. If the runtime cannot
provide these controls, expose that limitation and do not call it accepted metered
serving. Resource costs beyond token charges need their own authorization.

Copy the deliverable outside the build/search directory and test startup plus real
contract cases in a minimal environment. Keep generated code/model loading in the
reviewed isolated runtime. Test bad inputs, required resource failures and clean stop.
Do not bypass isolation to make an independent test pass. Missing external resources
mean an unverified draft, not “deployment successful.”

Explain in the user's language: what input to give, where the result appears, how
to start/stop, which costs remain and when human review is needed. The final result
may be a local HTTP endpoint, a usable local CLI service or an authorized deployment;
a frontend is optional. Public/production hosting needs appropriate auth/TLS/tenancy
and separate real validation, not just a development HTTP server.
