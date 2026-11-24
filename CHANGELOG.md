# Changelog / 版本变动

## v0.3.0 — 2026-11-24

New paid-capable bridge commands check the model-bound STS v0.16 price version before
submission. Missing, expired, future, mismatched and inconsistent readiness fails
closed; no price import/renewal, authorization or ledger mutation is performed by
the bridge. Read-only commands, deterministic final review, cancellation and saved
successful receipts remain usable without new paid calls. Added bilingual reasons,
an installed price-review guide and six protocol tests.

新的付费相关命令会在提交前核对 STS v0.16 返回的模型绑定价格版本；价格缺失、过期、
未生效、不匹配或状态不一致时停止。连接工具不导入/续期价格，不创建预算或修改费用
账本。只读、确定性最终复核、取消与历史成功回执无需新付费调用。增加双语原因、
随安装包分发的价格复核指引和六项协议测试。

Documented container-runtime-agnostic local setup: Colima with the Docker CLI and
Compose on macOS, Docker Engine with Compose on Linux, and links to the versioned STS
usage, architecture and dependency records. Existing pricing, budgets and runtime
images are unchanged.

补充与容器运行环境无关的本机设置说明：macOS 使用 Colima、Docker CLI 和 Compose，Linux
使用 Docker Engine 和 Compose，并链接到 STS 版本化的使用、架构及依赖记录。现有价格、
预算和运行时镜像均未改变。

## v0.2.0 — 2026-11-10

Optional headless STS client: private operation receipts, explicit exploration,
operator-feedback file exchange and hash-verified accepted service download.
Loopback-only, read-only default; no automatic budget, key reader or candidate execution.
Successful receipts recover without HTTP resubmission after resource exhaustion.
Deterministic finals require explicit review intent; archive download requires quality acceptance.
新增可选无前端引擎连接：私有回执、明确探索、真实用户复核文件、已验收服务包哈希下载。
仅连接本机，默认只读，不创建预算、不读取密钥、不执行候选代码。
资源耗尽后成功回执仍可恢复且不重提请求；确定性最终检查须明确复核，下载须先通过质量门禁。

## v0.1.1 — 2026-11-09

Supported hosted runner, restored CI, bilingual synthetic example and matching package metadata.
修复托管环境兼容性，恢复 CI，补齐双语合成示例与版本一致的安装包。

## v0.1.0 — 2026-11-09

Initial installable Goal-to-Service skill and tested budget/evidence/install/package helpers.
首个可安装的 Goal-to-Service 技能及预算/证据/安装/打包工具。
