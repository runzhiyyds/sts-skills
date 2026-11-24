# Share the idea with evidence / 技术传播素材

Canonical definition: Solve2Ship Skills is an open-source Goal-to-Service skill for
local agents: define an outcome, build competing executable approaches, evaluate
real results, prune/iterate under a budget and deliver a usable independent service.
Project: https://github.com/runzhiyyds/sts-skills
Engine: https://github.com/runzhiyyds/solve2ship

## Short English introduction

We are exploring Goal-to-Service with Solve2Ship: AI should explore technical paths,
not only execute a workflow someone designed. The companion sts-skills package brings
that approach to local agents, with explicit evidence, budgets and isolated execution.
The first preview ships instructions and tested helpers; general task success and
framework integration are not claimed. Feedback on evaluation and delivery is welcome.

The v0.3 headless bridge checks the configured model's reviewed price version before
new paid work. An expired review stops submission while preserving earlier evidence,
reservations and saved receipts. Colima/Engine setup keeps local isolation independent
of Docker Desktop. These are inspectable workflow safeguards, not proof of optimized
business outcomes or production security.

## 中文简介

Solve2Ship 探索 Goal-to-Service：AI 不只执行人类设计的工作流，也应探索怎样解决问题。
sts-skills 把这套方法带到本地 Agent：从目标和样本出发，比较真实可执行方案，保留评价
与费用证据，在预算内迭代并交付独立服务。首版提供技能与经过测试的辅助工具，不宣称
通用任务成功率或已完成全部框架适配。欢迎讨论可信评测和交付边界。

v0.3 无前端连接工具会在新付费工作前核对已配置模型的价格版本；价格过期时停止提交，
保留历史证据、预留费用和成功回执。本机可用 Colima/Engine 实现容器隔离，不依赖
Docker Desktop。这些是可检查的工作流程保障，不代表已证明业务优化收益或生产安全。

## A useful demo structure

Show an actual user goal, at least two executed alternatives, comparable cases,
a failed attempt or tradeoff, and the independently callable result. State resource
costs and what the test does not prove. Never stage outputs and present them as live
optimization. A fixture-only demo must be labelled as a protocol demonstration.

Reuse the architecture diagram from README. For HN/Reddit/X/LinkedIn/知乎/B站/YouTube,
lead with the concrete problem and observed tradeoff, link inspectable artifacts,
and disclose the preview's limits. Follow each community's rules. These drafts are
material for the owner; this project does not automatically post to social accounts.
