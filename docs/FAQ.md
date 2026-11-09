# FAQ / 常见问题

**What is Solve2Ship Skills?** An installable instruction package that helps a local
agent turn a goal and examples into evaluated alternatives and a working service.
It is the conversational companion to the STS engine, with no mandatory frontend.

**Do I need to design a workflow or understand ML?** No. Describe the desired outcome
and give examples. The agent should choose technical approaches and explain tradeoffs
in plain language. It may need a small clarification when success is ambiguous.

**Does installation give me a model or sandbox?** No. The skill uses capabilities the
host actually provides. Paid APIs, safe code execution and hosting need appropriate
resources and authorization. Missing isolation never triggers host code execution.

**Is this a fixed multi-agent workflow?** No. Rules, scripts, ML, prompts, workflows,
agents and harnesses are competing approaches, not required steps or guaranteed
integrations. Prefer a simpler solution when the actual evidence supports it.

**Can it guarantee the best solution?** No. It chooses among tested candidates under
real budgets and uncertain evidence. Small synthetic cases and judge scores are not
verified business accuracy. The evaluator itself may need human calibration.

**What can I use immediately?** The skill, installer, deterministic package builder
and durable evidence helper. These are tested utilities, not proof of autonomous
success on every business problem. Task-specific services require actual construction
and independent startup/contract checks in the user's environment.

**Can I use it without STS?** Yes, in an agent that can load the instructions and has
the necessary tools. STS is an optional engine path, not bundled or silently installed.

**Do keys, customer data or development logs go to GitHub?** No. Keep those local and
outside distributable bundles. Public research artifacts require consent and review.

中文：你只需要目标与样本，不需要先懂技术。技能不会自动获得模型、预算、云权限或安全
执行环境，也不能保证“全局最优”。辅助脚本已做协议测试；具体业务服务必须真正构建和
独立验证。没有可信标签时应说明评价的不确定性，不能把模型评分当真实准确率。密钥、
客户数据、数据库与开发日志不进入公开仓库。
