# Select an approach from the task

| Approach | Useful when | Evidence needed |
|---|---|---|
| Rules / small scripts | Stable structure, exact calculation, bounded routing | Real boundary cases; scripts isolated |
| Classical ML / AutoML | Repeated structured inputs and enough relevant labels | Train-only fit, leakage/group checks, held-out comparison |
| Prompt / model+code | Semantic interpretation plus exact postprocessing | Real provider outputs, costs, invalid-output retention |
| LangGraph / Dify workflow | Explicit state, existing integrations or durable multi-step work help | Current deployment/export support; real callable artifact, not a graph screenshot |
| Agent / multi-agent | Dynamic tool choice or complementary roles justify overhead | Stop/tool/budget traces and comparison with simpler approaches |
| Harness | Task genuinely requires bounded files/CLI/long execution | Appropriate isolation, allowed tools, reproducible startup |

These are options to investigate, not preinstalled adapters or a ranking of project
quality. Verify current official project docs/API/version/license before adoption.
Prefer mature projects through a small adapter over recreating their framework.
Record direct/transitive dependencies, source provenance and redistribution duties.
Keep family identifiers extensible; a candidate is an executable solution, not
necessarily an agent. Preserve any technology the user explicitly requires.

The separate [STS engine](https://github.com/runzhiyyds/solve2ship) offers an existing
local competition/evidence path. This skill is not a bundled engine or a claim that
LangGraph/Dify integrations have been implemented. Consult the engine's current
supported scope before using it; v0.12.0 is the initial reference snapshot for this
skill. Do not couple the delivered service to an experiment controller/database.
