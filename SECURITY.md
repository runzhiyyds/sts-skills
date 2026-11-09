# Security / 安全边界

The helper ledger is owner-local SQLite, not an encrypted vault or hostile-operator
quota service. Preserve state across restarts; deleting or cloning it defeats its
accounting boundary. Reported costs are not provider invoices. Do not store API keys
in the ledger or send them in public issues.

Generated code/model loading requires appropriate isolation. This package does not
provide that runtime and has no host execution fallback. Inspect the host agent's
permissions before use. Installers never overwrite a different existing skill.
A skill archive hash is an integrity check, not a security certification.

For sensitive reports contact the repository maintainer privately; public issues
must omit keys, customer data and private evidence. 本地明文状态不能冒充生产保险库；
敏感问题请私下联系维护者，不要在公开 Issue 中贴凭据或客户数据。
