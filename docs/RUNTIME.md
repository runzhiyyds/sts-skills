# Local container runtime setup / 本地容器运行环境

Solve2Ship Skills does not install or start a container engine. Generated code and
model loading require an approved isolated runtime; running generated code in a host
process is never a fallback. The current STS local adapter uses a local
Docker Engine-compatible API endpoint. A desktop bundle is not required.

Choose the setup that matches your host:

## Apple Silicon macOS with Colima

Install the Docker CLI, the Compose plugin, and Colima using the package manager you
already trust. With Homebrew, the packages are:

```sh
brew install colima docker docker-compose
colima start --runtime docker
docker context use colima
docker info
docker compose version
```

Verify `command -v docker` resolves to the independently installed CLI, and that
`docker context show` returns the intended Colima context. The Engine runs inside
Colima's Linux VM. Docker Desktop.app is not required; retain Colima, the CLI and
Compose if removing Desktop. Data inside a former Desktop VM is separate and does
not automatically migrate to Colima.

The `colima` context keeps the Engine endpoint local to the machine. Stop it when
you are finished with local work:

```sh
colima stop
```

See the [Colima documentation](https://github.com/abiosoft/colima) for host-specific
resource options and the [Docker CLI installation guide](https://docs.docker.com/engine/install/)
for package details.

## Linux with Docker Engine

Install Docker Engine and its Compose plugin from the official instructions for your
distribution, then start the local service and verify the CLI endpoint:

```sh
sudo systemctl enable --now docker
docker info
docker compose version
```

The account running STS must be allowed to access the local Engine socket according
to your distribution's policy. Do not put a Docker socket, Engine credentials or
host filesystem mounts inside a generated candidate container.

Use [Docker Engine installation](https://docs.docker.com/engine/install/) and the
[Docker Compose documentation](https://docs.docker.com/compose/) for the exact
package and service steps on your distribution.

## Compose and STS

Compose can coordinate a multi-service deployment when that project supplies a
reviewed Compose file. STS v0.16 source does not bundle a Compose application stack:
start its local engine with the documented Python/Make commands. Installing Compose
does not replace the candidate sandbox or its acceptance checks.

Follow the STS repository's versioned [local usage guide](https://github.com/runzhiyyds/solve2ship/blob/main/docs/USAGE.md)
for engine startup and service commands. The [STS architecture guide](https://github.com/runzhiyyds/solve2ship/blob/main/docs/PRODUCT_ARCHITECTURE.md)
describes the control-plane/runtime boundary and the [dependency record](https://github.com/runzhiyyds/solve2ship/blob/main/docs/DEPENDENCIES.md)
records the reviewed versions and license duties.

The STS adapter follows Docker CLI context/host configuration and accepts local Unix
sockets. Changing Engine or context requires the STS isolation acceptance checks
again. macOS Colima has recorded STS acceptance; the Linux Engine contract is
documented, with host-specific verification still required.

If `docker info` or the STS isolation acceptance checks fail, pause execution that
needs isolation and preserve the task. A missing Compose plugin blocks only a
project that actually requires a Compose stack; it does not block the STS Engine
adapter by itself. The skill can still inspect inputs, prepare a task contract and
explain the missing setup; it must not execute generated code on the host or silently
install an engine.

## 简体中文

Solve2Ship Skills 不会安装或启动容器引擎。生成代码和加载模型必须在经过批准的隔离
环境中运行，不能退回到宿主进程执行。当前 STS 本机适配器使用本机
Docker Engine 兼容 API；不依赖桌面应用。

Apple Silicon macOS 可使用 Colima、Docker CLI 和 Compose 插件：

```sh
brew install colima docker docker-compose
colima start --runtime docker
docker context use colima
docker info
docker compose version
```

Linux 可按发行版官方说明安装 Docker Engine 与 Compose 插件，再启动并检查本机服务：

```sh
sudo systemctl enable --now docker
docker info
docker compose version
```

确认 `command -v docker` 指向独立安装的 CLI，`docker context show` 为 Colima 上下文。
Docker Engine 在 Colima 的 Linux 虚拟机中运行。STS 不需要 Docker Desktop.app；卸载
Desktop 时保留 Colima、CLI 和 Compose。旧 Desktop 虚拟机中的数据不会自动迁移。

Compose 可用于有经审核 Compose 文件的多服务项目；STS v0.16 未附带 Compose 应用栈，
本机引擎仍按文档使用 Python/Make 启动。Compose 不代替候选方案的隔离验收。
STS 的版本化启动命令请看
[本机使用说明](https://github.com/runzhiyyds/solve2ship/blob/main/docs/USAGE.md)；运行边界和
依赖许可请看 [架构说明](https://github.com/runzhiyyds/solve2ship/blob/main/docs/PRODUCT_ARCHITECTURE.md)
与[依赖记录](https://github.com/runzhiyyds/solve2ship/blob/main/docs/DEPENDENCIES.md)。
切换 Engine 或上下文后须重新执行 STS 隔离检查。已有 Colima 本机验收记录，Linux
遵循相同的本地 Unix 套接字协议，但具体主机仍需实际验证。
如果 Docker Engine 或 STS 隔离验收失败，应暂停需要隔离环境的执行并保留进度。
缺少 Compose 只影响实际依赖 Compose 栈的项目，不会单独阻断 STS Engine 适配器。
仍可检查输入、准备任务；不能在宿主机运行生成代码，也不能偷偷安装引擎。
