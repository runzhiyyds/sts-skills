# Dependencies and provenance / 依赖与来源

This package uses Python 3.10+ standard-library helpers and Markdown instructions.
No third-party package, framework source, model weight, interpreter binary or Docker
image is bundled. Installed CPython/SQLite and agent hosts retain their own licenses.

Own source: Apache-2.0, Copyright 2026 郭辰远 (Chenyuan Guo). LICENSE is the same
owner-approved Apache-2.0 text used by the Solve2Ship source project. NOTICE preserves
attribution. Skill instructions implement the user-confirmed Solve2Ship principles;
they do not copy framework tutorials or claim a new published algorithm.

References to LangGraph, Dify, AutoML, agents or Docker are selection guidance.
Adoption requires current version/source/license/dependency/redistribution review;
no executable integrations with those projects are bundled here. An unmodified
upstream component's license must not be replaced with the STS license.

The initial STS implementation reference is v0.12.0, commit
`dfc52c17d88f1eb6247fa36a085aa09aa1914183`, at
https://github.com/runzhiyyds/solve2ship . This skill can guide other local agents
without installing that engine; its runtime acceptance and model budget are separate.

CI uses the same pinned actions already reviewed in that STS snapshot:
actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 (v4.2.2, MIT), and
actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 (v5.6.0, MIT).
Upstream sources: https://github.com/actions/checkout and
https://github.com/actions/setup-python . Action runner binaries are not redistributed.
No complete CVE, Rust/runtime SBOM or legal certification is claimed.

中文：技能不随包安装框架、模型、解释器或容器镜像。现有辅助脚本仅使用 Python 标准库。
第三方选型需要在实际采用前核验版本、依赖、许可和分发义务。主项目的运行验收与预算
不会因为安装技能而自动继承。当前不是完整安全/法律认证。
