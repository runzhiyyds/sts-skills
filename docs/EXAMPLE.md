# Try customer-message routing / 试用客服留言分类

Use the [20 synthetic Chinese messages](../examples/customer-routing.json) with your
installed [Solve2Ship skill](../skills/solve2ship/SKILL.md). These are example inputs,
not user data, labeled truth, a trained model or a shipped winning classifier. The
sample stays in this repository; the installable skill ZIP does not include it.

## Ask in ordinary language / 直接用自然语言开始

Attach the JSON file to your local agent, or give it the file's local path, and say:

> Use the Solve2Ship skill. Read examples/customer-routing.json. I want to classify
> each customer message as 退款 (refund), 物流 (delivery) or 其他 (other). Decide which
> approaches fit, compare real results and prepare something I can try locally.
> Do not make paid calls or deploy to the cloud. Explain any resource or quality
> limitation in plain language.

中文可直接说：

> 使用 Solve2Ship 技能，读取 examples/customer-routing.json。请把客服留言分成退款、物流、
> 其他。你来判断适合的方法，比较实际结果，给我能在本地试用的服务。不要付费调用，
> 不要云部署；资源或质量有问题时，用普通业务语言解释。

For a host that supports `$solve2ship`, that explicit name can invoke the skill.
Other hosts use their own skill-loading mechanism. You do not need to select a
framework or design a workflow. If safe execution is unavailable, the agent should
explain the smallest setup step and preserve progress; installing the skill alone
does not supply Docker, a model subscription or an API budget.

支持 `$solve2ship` 的宿主可以用这个名称调用；其他宿主按自己的技能加载方式使用。
你不必选择技术框架或设计工作流。没有合适的安全执行环境时，Agent 应说明最少需要
怎样配合并保留进度；技能本身不会安装 Docker、赠送模型额度或取得云权限。

## Observed forward test / 已观察到的前向测试

A maintainer ran this request with the current skill and the separately accepted
local STS execution resources. The agent compared bounded keyword rules with a
small contextual script; generated Python executed only in the reviewed Docker
runtime. This is a forward-test summary, not a packaged reproducible benchmark or
proof that every agent will behave identically.

| Observation / 观察 | Actual result / 实际结果 |
|---|---|
| Synthetic inputs, supplied human labels / 合成输入、提供的人工标签 | 20 inputs, 0 labels / 20 条、0 标签 |
| Frozen train / validation / final split / 固定数据划分 | 10 / 6 / 4 |
| Common validation execution / 公共验证执行 | 6 cases per approach; 12 actual outputs / 每方案 6 条，共 12 次实际输出 |
| Structural category check / 类别格式检查 | All 12 outputs used one of the three allowed strings / 12 次均符合允许类别格式 |
| Cross-approach disagreement / 方案分歧 | 1 of 6 validation inputs / 6 条中有 1 条分歧 |
| Paid API/model-judge calls / 付费 API、模型裁判调用 | 0 / 0 |
| Positive budget reservation under zero authorization / 零授权下的正数预留 | Refused before any submission / 提交前拒绝 |
| Independent draft service / 独立草稿服务 | 6 HTTP equivalence cases, health check, malformed request 422, foreign Origin 403; clean stop / 6 条 HTTP 等价检查、健康检查、异常请求拒绝及正常停止 |
| Final holdout usage / 最终保留集使用 | 0 of 4; remained unused / 4 条均未使用 |
| Quality acceptance / 质量验收 | Review required / 仍需复核 |

The disagreement was on a message asking about warranty after confirming receipt.
The keyword approach returned 物流; the contextual script returned 其他. Neither
response became a human-approved label. Output agreement and category-format checks
are not accuracy, and service startup is not semantic quality acceptance.

分歧出现在“已收到货，只想问保修”的留言：关键词规则返回“物流”，上下文脚本返回
“其他”。两者都没有被冒充为人工确认的标签。方案一致性、类别格式和服务启动均不能
证明业务准确率。

The agent prepared an independently startup-verified **draft**, using the accepted
STS gateway/runtime resources without the STS search controller, experiment DB or
model profile. No service artifact, generated program, private execution log or raw
business dataset is distributed with this example. Your agent must build and verify
its own result against the resources and constraints actually available locally.

测试只交付了经独立启动验证的**试用草稿**；使用已有验收的 STS 网关/运行环境，不依赖
STS 搜索进程、实验数据库或模型配置。本示例不分发该服务、生成程序、私有日志或真实
业务数据。你的 Agent 必须根据本机实际资源构建并验证自己的产物。

## What to expect next / 下一步应得到什么

Expect a brief comparison, a local usage explanation and a few targeted review
questions about ambiguous cases. The agent should keep final inputs sealed until
an acceptance rule is established. It may need you to confirm business priorities
such as negation, historical mentions or multiple intents; it should not ask you to
label every message or invent a final winner from unsupported scores.

你应收到简明比较、本地使用方式，以及少量边界案例复核问题。最终保留输入应在验收
标准明确前继续封存。Agent 可以请你确认否定表达、历史提及、多意图的业务优先级，
但不应要求你先标完所有数据，也不能用缺少依据的分数编造胜出方案。
