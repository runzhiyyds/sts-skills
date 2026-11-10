# Use STS through your local agent / 通过本地 Agent 使用 STS

[Home](../README.md) · [中文](../README.zh-CN.md) · [FAQ](FAQ.md)

If STS is already installed on your machine, your local agent can use its real
engine without opening Studio. The optional packaged `sts_bridge.py` handles the
local API, task preview/save, explicit exploration/cancel, evidence, user reviews
and download of an already accepted service. It never installs an engine, reads a
model key, increases a budget or executes generated code on the host.

Tell your agent:

> Use Solve2Ship with my local STS engine. Here are my samples and desired outcome.
> Check its resources and budget first. Explain actual results and any reviews I
> need to do. Do not start paid work unless I have authorized it.

The technical command reference lives inside the installed skill at
[references/sts-engine.md](../skills/solve2ship/references/sts-engine.md). Ordinary
users should not need to choose frameworks, edit request IDs or understand APIs.
The agent handles those mechanics, but must preserve your actual goal, budget,
judgments and permission boundaries. There is no forced initial workflow.

The helper defaults to read-only status. New search, edits/reactivation and final
execution require explicit commands; paid-capable operations require an existing
engine budget and `--allow-paid`. A stable owner-only operation journal prevents
silent duplicate HTTP submissions. Unknown/failed submissions remain for review;
an agent must not change operation IDs or erase state to make a retry look new.
Saved successful receipts remain available after the budget is exhausted, without
new HTTP work. Explicit operator-review final execution for a known deterministic
winner does not require a model allowance. Download also requires the final quality
gate to have passed; an archive checksum alone is insufficient.

Quality review is not automatic approval. The agent may show actual input/output
cases and record your accept/reject/unsure feedback, but cannot answer on your behalf
or turn its own model score into human truth. Final review closes one frozen gate;
exposed final inputs cannot be used for further optimization. A review rejection or
“not enough evidence” is useful output, not a reason to invent an accepted service.

The bridge targets the STS v0.14 review/readiness API. Older v0.13 engines can be
inspected read-only; missing readiness means starts fail closed. The client accepts
only HTTP loopback, ignores proxy settings, rejects redirects and keeps data local
to the existing engine. That engine may subsequently send authorized task data to
a configured model provider during exploration. This development API is not public
hosting or production authentication.

## 简体中文

已有本机 STS 时，可以直接对本地 Agent 说：“使用 Solve2Ship，根据这些样本比较方案，
先检查资源和预算，再解释真实结果；需要我复核时，用业务语言逐条展示。未经授权不要
启动付费调用。”无需打开前端，也不需要先选择框架或设计工作流。

技能已附带真实的本机引擎连接工具，可预览/保存任务、明确启动或取消探索、查看证据和
复核材料、下载已经验收的服务包。它不自带或偷偷安装引擎，不读取密钥，不提高预算，
也不执行生成代码。默认仅查看；启动仍受现有模型、预算、价格和隔离运行条件限制。

付费相关操作使用持久编号防止重复提交；不确定/失败时应核对原回执，不能换编号或删
状态重试。Agent 只能记录你真实给出的判断，不能代你填写“认可”或声称已完成质量验收。
成功回执在预算耗尽后仍可恢复，不会重新提交；明确进入人工复核的已知确定性方案无需
模型额度。下载还会检查最终质量门禁已经通过，不能只有源码包校验和。
本机开发接口也不等于公网部署。当前完整桥接需要 STS v0.14；v0.13 可只读查看。
