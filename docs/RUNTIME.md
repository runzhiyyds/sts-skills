# Local container runtime setup / 本地容器运行环境

Solve2Ship Skills does not install or start a container engine. Generated code and
model loading require an approved isolated runtime; running generated code in a host
process is never a fallback. The current STS local adapter uses a local
Docker Engine-compatible API endpoint. A desktop bundle is not required.

Choose the setup that matches your host:

## macOS with Colima

Install the Docker CLI, the Compose plugin, and Colima using the package manager you
already trust. With Homebrew, the packages are:

```sh
brew install colima docker docker-compose
colima start --runtime docker
docker context use colima
docker info
docker compose version
```

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

Compose is the local coordination layer for a multi-service setup; it does not
replace the isolated candidate runtime. From the directory containing the reviewed
STS Compose file, validate the rendered configuration and keep listeners on loopback
unless you have separately authorized a deployment:

```sh
docker compose config
docker compose up -d
docker compose ps
```

Follow the STS repository's versioned [local usage guide](https://github.com/runzhiyyds/solve2ship/blob/main/docs/USAGE.md)
for engine startup and service commands. The [STS architecture guide](https://github.com/runzhiyyds/solve2ship/blob/main/docs/ARCHITECTURE.md)
describes the control-plane/runtime boundary and the [dependency record](https://github.com/runzhiyyds/solve2ship/blob/main/docs/THIRD_PARTY_DEPENDENCIES.md)
records the reviewed versions and license duties.

If `docker info` or `docker compose version` fails, pause execution that needs
isolation and preserve the task. The skill can still inspect inputs, prepare a task
contract and explain the missing setup; it must not execute generated code on the
host or silently install an engine.

## 简体中文

Solve2Ship Skills 不会安装或启动容器引擎。生成代码和加载模型必须在经过批准的隔离
环境中运行，不能退回到宿主进程执行。当前 STS 本机适配器使用本机
Docker Engine 兼容 API；不依赖桌面应用。

macOS 可使用 Colima、Docker CLI 和 Compose 插件：

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

Compose 用于协调本机多服务，不代替候选方案的隔离运行环境。STS 的版本化启动命令请看
[本机使用说明](https://github.com/runzhiyyds/solve2ship/blob/main/docs/USAGE.md)；运行边界和
依赖许可请看 [架构说明](https://github.com/runzhiyyds/solve2ship/blob/main/docs/ARCHITECTURE.md)
与[依赖记录](https://github.com/runzhiyyds/solve2ship/blob/main/docs/THIRD_PARTY_DEPENDENCIES.md)。
如果检查失败，应暂停需要隔离环境的执行并保留进度，不能在宿主机运行生成代码，也不能
偷偷安装引擎。
