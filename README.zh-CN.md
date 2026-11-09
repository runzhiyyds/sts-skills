# Solve2Ship Skills — 从业务目标到可用的 AI 解决方案

[English](README.md) · [简体中文](README.zh-CN.md) · [Solve2Ship 主项目](https://github.com/runzhiyyds/solve2ship)

**告诉本地 Agent 你想达成什么，让不同方案竞争，拿到可以使用的服务。**

这是可安装到本地编程 Agent 的开源技能，探索 **Goal-to-Service**：从业务目标和输入
样本出发，自主比较可执行技术路线，真实评测，在预算内剪枝和迭代，最终交付可独立
调用的本地服务。无需 STS 前端，也无需用户先设计工作流或懂技术选型。

核心思想：**AI 应该能探索解决问题的技术路径，而不只是执行人类设计好的 Workflow。**
规则、脚本、ML、Prompt、工作流和 Agent 都是可选方案；简单程序也可以胜过复杂 Agent。

**v0.1.0 预览。** 当前交付的是技能指令和经过测试的证据/安装/打包辅助工具，不是另一个
自治引擎、模型或隔离执行环境。实际质量取决于 Agent、资源与评价证据。LangGraph、Dify
等内容是选型指引，不代表已经完成这些平台的运行适配。

## 普通用户怎样开始

安装后，直接告诉你的 Agent：

> 使用 $solve2ship。我有一批客服留言，想分成退款、物流、其他。请你判断适合的方法，
> 比较并测试，最后给我本地能使用的服务。用普通业务语言解释，不要付费调用或云部署。

提供输入样本和一段期望即可，逐条标签可选。Agent 应先检查已有资源，只询问影响结果
的必要信息；技术细节由它处理。需要额外额度、凭据或安全执行环境时，会解释原因和
最小配合步骤。安装技能不会自动获得模型 API、Docker、云权限或付费预算。

可先用[客服留言分类示例](docs/EXAMPLE.md)和[20 条无标签合成输入](examples/customer-routing.json)
试用。示例提供零付费、本地运行的自然语言请求和真实前向测试摘要，并明确保留质量
复核门禁。

## 安装

从 GitHub 下载仓库 ZIP，交给本地 Agent 并说：“请帮我安装这个 Solve2Ship 技能，
保留已有不同版本。”核对源码和宿主请求的权限后，让 Agent 处理技术步骤。也可手动
使用以下命令。
可选脚本需要 Python 3.10+；技能主体是 Markdown 指令。

```sh
git clone https://github.com/runzhiyyds/sts-skills.git
cd sts-skills
python3 scripts/install_skill.py --agent codex
# Claude 用户改为：python3 scripts/install_skill.py --agent claude
```

按宿主要求重新加载技能或重启。不同 Agent 对技能的支持不同，应以其当前文档为准。
其他宿主可将 `skills/solve2ship/` 复制到支持的技能目录，或使用 `--destination` 指定目录。
安装器遇到内容不同的已有技能会停止，不会静默覆盖。

发布 ZIP 包内有 `solve2ship/` 文件夹、校验清单和 LICENSE/NOTICE，可解压到宿主的技能
目录。校验和只能证明文件一致，不能证明 Agent 将来生成的每个方案都安全或正确。

## 工作方式与边界

目标与样本 → 提出不同方案 → 真正构建与评测 → 剪枝和迭代 → 冻结最终检查 → 独立服务。

技能要求区分用户标签、可执行检查、未校准模型裁判和人工反馈；最终测试数据不能回流
优化。生成代码和模型加载必须在合适的隔离环境里运行，没有宿主执行兜底。密钥和数据
留在本地，未知费用继续预留，失败或费用不明的请求不自动重试。

- [技能入口](skills/solve2ship/SKILL.md)
- [权限与隔离](skills/solve2ship/references/execution.md)
- [方案选择](skills/solve2ship/references/adapters.md)
- [评价与证据](skills/solve2ship/references/evaluation.md)
- [独立交付](skills/solve2ship/references/delivery.md)
- [常见问题](docs/FAQ.md)、[依赖和许可](docs/DEPENDENCIES.md)、[传播素材](docs/SHARING.md)

运行 `python3 -m unittest discover -s tests -v` 验证辅助工具，执行
`python3 scripts/package_skill.py` 生成安装 ZIP。这些测试不能冒充真实业务准确率或优化
收益。生产托管、公开部署、外部下载和费用需要各自的授权与真实验收。

## 许可与引用

[Apache-2.0](LICENSE)，Copyright 2026 郭辰远（Chenyuan Guo），请保留 [NOTICE](NOTICE)。
第三方项目、模型与运行环境保留自己的许可。引用信息见 [CITATION.cff](CITATION.cff)，
不宣称已发表论文或已证明的算法创新。
