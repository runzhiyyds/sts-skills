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

**What can I use immediately?** The skill, installer, deterministic package builder,
durable evidence helper and optional [headless STS bridge](HEADLESS.md). These are tested utilities, not proof of autonomous
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


**Can my agent use STS without its webpage?** Yes, when the local engine is already
installed/configured. The packaged bridge uses real loopback APIs with no browser.
It can inspect, preview/save, explicitly start/cancel, exchange actual operator review
files and download an accepted service archive. It does not secretly set up resources,
start paid work by default or manufacture operator attestations. See [headless use](HEADLESS.md).

中文：已有本机 STS 时，Agent 可通过附带工具直接调用真实接口，无需打开页面。工具
默认只读，付费探索必须明确启动且已有额度；复核仅能记录用户真实判断，不自动认可。

**Why does it stop with an API key and money still available?** A model connection,
budget and price review are separate requirements. The v0.3 bridge requires model-bound
`pricing.ready` from STS v0.16+ before new paid submissions. If the review expires,
inspect current official prices and explicitly import the reviewed version locally.
The bridge does not renew it or reset historical usage. Read-only work and cached
successful receipts remain available. See [price review](../skills/solve2ship/references/pricing.md).

中文：有密钥和余额不代表价格审核仍有效。新付费操作需 STS v0.16+ 返回模型绑定价格
已就绪；过期后先核对当前官方价格并明确导入。工具不会自动续期或清空历史费用，
只读工作和已有成功回执仍可继续。

**Does it need Docker Desktop?** No. The documented STS paths use Colima with Docker
Engine/CLI on Apple Silicon macOS, or Docker Engine on Linux. Compose is available
for projects that supply a Compose stack; it is not the candidate sandbox. Actual
STS isolation acceptance is required before running generated code. See [runtime setup](RUNTIME.md).

中文：不需要 Docker Desktop。Apple Silicon macOS 可用 Colima + Docker Engine/CLI，
Linux 可用 Docker Engine；安装 Compose 不等于隔离验收。生成代码仍需通过 STS 的
实际隔离检查后才能运行。
