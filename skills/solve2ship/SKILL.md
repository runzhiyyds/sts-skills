---
name: solve2ship
description: Turn a business goal and example inputs into competing executable solutions, evaluate and improve them under a budget, then deliver a working local service. Use when a user wants an outcome solved without choosing a workflow or technology first.
---

# Solve2Ship — From Goals to Working AI Solutions

Define the outcome. Let solutions compete. Ship the best supported by the evidence.
Use the user's language and business terms. The user should not need to choose a
framework, write a prompt, label every sample or understand this skill's mechanics.
No frontend is required. This skill guides the current agent; it is not a separate
search engine, an installed model, a sandbox or proof that every task can be solved.

## Start from the outcome

Inspect available inputs/resources first. Translate the request into a short working
contract: input, expected outcome, must-have constraints, acceptable quality/cost/
latency and how the user will call the result. Accept examples plus one natural-
language goal; labels are optional. Ask only for information that changes feasibility
or success. Offer business-language choices when necessary. Never request API keys
in chat. Preserve explicitly chosen tools and the user's authorized scope.

Before paid/external calls or generated-code execution, read
[execution and authorization](references/execution.md). If an essential resource is
missing, explain what the user must do in plain language and continue unaffected
work. A model subscription does not imply permission or funds for new API calls.

## Let approaches compete

Propose several meaningfully different plausible approaches before committing. Start
cheap where appropriate; do not force every task into an agent or workflow. Rules,
a small script, ML, Prompt, hybrid, LangGraph/Dify workflows, agents or a harness are
candidate options, not a mandatory checklist. Use [adapter selection](references/adapters.md)
when choosing frameworks/resources; verify current primary docs and exact versions/
licenses before adoption. A proposed integration is not an implemented adapter.

Build executable candidates behind a common input/output contract. Separate the
agent/controller from execution: model-generated code and model deserialization
run only inside an available, suitable isolated runtime. No host subprocess fallback.
If isolation is unavailable, do not run generated code to produce reassuring results.

## Evaluate, prune and improve

Read [evaluation and evidence](references/evaluation.md) before making quality claims.
Split/group inputs before optimization, keep a final holdout sealed, and compare
candidates on the same cases and evidence source. Record real outputs, errors,
latency, model costs/reservations, versions and artifact hashes. Distinguish trusted
labels, provided unverified labels, deterministic checks, uncalibrated judges and
human feedback. Never present fixtures, judge scores or tuning results as accuracy.

Use failed cases to diagnose whether a change is worth its cost. Make bounded edits,
re-run comparisons and retain older artifacts/results. Pause or prune conservatively;
keep a route to reactivate. Stop when budget/evidence/constraints require it, or when
further work has no supported value. Failed or ambiguous paid operations are never
automatically replayed. Do not invent expected gains or require improvement.

For durable local call authorization, use `scripts/evidence.py` as documented in
[evaluation and evidence](references/evaluation.md). It does not execute candidates,
contact providers, estimate prices or judge quality. The agent must reserve a verified
cost ceiling before each paid submission, then record reported usage or keep the
reservation when uncertain. Do not delete or recreate state to reset a budget.

## Ship a useful service

Read [delivery](references/delivery.md) before final selection/export. Freeze the
chosen artifact before one-time final checks; retain a failure rather than tuning
or retrying against exposed final data. Deliver a working local HTTP/CLI service,
its required environment, configuration, notices and simple business-language usage.
Test the delivered copy independently of the search process. If quality cannot be
accepted, give an explicit review gate and the actual limitation, not a fake winner.

Report briefly: what works, why this approach won, measured evidence and its limits,
how to use/stop it, remaining costs/risks and the next useful step. Do not claim a
cloud deployment, production security, global optimum or scientific novelty without
matching evidence. An artifact with no verified startup remains an unverified draft.
