## 官方提供的镜像只适合于 `x86` 架构
##  解决
使用**交叉编译**：
### 安装 buildx
**(以下安装基于docker19.03.12ubuntu20.04)**

`buildx` 是 Docker 官方提供的一个构建工具，它可以帮助用户快速、高效地构建 Docker 镜像，并支持多种平台的构建。使用 `buildx`，用户可以在单个命令中构建多种架构的镜像，例如 x86 和 ARM 架构，而无需手动操作多个构建命令。此外，`buildx` 还支持 Dockerfile 的多阶段构建和缓存，这可以大大提高镜像构建的效率和速度。

如果需要手动安装，可以从 GitHub 发布页面[下载](https://link.zhihu.com/?target=https%3A//github.com/docker/buildx/releases/tag/v0.10.4)对应平台的最新二进制文件，重命名为 `docker-buildx`，然后将其放到 Docker 插件目录下（Linux/Mac 系统为 `$HOME/.docker/cli-plugins`，Windows 系统为 `%USERPROFILE%\.docker\cli-plugins`）。
给插件增加可执行权限 `chmod +x ~/.docker/cli-plugins/docker-buildx`

```bash
# 我在虚拟机上进行的交叉编译，是x86架构
wget https://github.com/docker/buildx/releases/download/v0.10.4/buildx-v0.10.4.darwin-amd64

# 重命名
mv buildx-v0.10.4.darwin-amd64 docker-buildx

# 放到对应目录
mv docker-buildx $HOME/.docker/cli-plugins

# 添加权限
chmod +x ~/.docker/cli-plugins/docker-buildx

# 验证可用
docker buildx version

```

### 创建 mybuilder
要使用 `buildx` 构建跨平台镜像，我们需要先创建一个 `builder`，可以翻译为「构建器」。

```bash
$ docker buildx create --name mybuilder --use
mybuilder
```

或使用docker buildx构建镜像时需要使用代理:
```bash

$ docker buildx create --use --name mybuilder --driver-opt env.http_proxy=http://192.168.3.5:7890 --driver-opt env.https_proxy=http://192.168.3.5:7890
mybuilder
```

查看已创建镜像：
```bash
$ docker buildx ls
NAME/NODE    DRIVER/ENDPOINT             STATUS  BUILDKIT             PLATFORMS
mybuilder *  docker-container                                         
  mybuilder0 unix:///var/run/docker.sock running v0.12.3              linux/amd64, linux/amd64/v2, linux/amd64/v3, linux/amd64/v4, linux/386
default      docker                                                   
  default    default                     running v0.11.6+0a15675913b7 linux/amd64, linux/amd64/v2, linux/amd64/v3, linux/amd64/v4, linux/386
```

其中 * 所在的即为正在使用的

### 启动 mybuilder
如果 mybuilder 的状态为 `inactive` 或者 `stopped` 需要手动进行启动（上面的操作中--use 也会自动启动）
```bash
$ docker buildx inspect --bootstrap mybuilder
[+] Building 16.8s (1/1) FINISHED
 => [internal] booting buildkit                                                                                                                                  16.8sdocker
 => => pulling image moby/buildkit:buildx-stable-1                                                                                                               16.1s
 => => creating container buildx_buildkit_mybuilder0                                                                                                       /arm64       0.7s
Name:   mybuilder
Driver: docker-container

Nodes:
Name:      mybuilder0
Endpoint:  unix:///var/run/docker.sock
Status:    running
Buildkit:  v0.12.3
Platforms: linux/amd64, linux/amd64/v2, linux/amd64/v3, linux/amd64/v4, linux/386

```

### 构建镜像
以 Auto-Edge 的 controller 为例，运行在云端和边端，其中云端是 x86 架构，边端是 arm 架构
```bash
$ docker buildx build --platform linux/arm64,linux/amd64 --build-arg GO_LDFLAGS="" -t onecheck/controller:v1.0.0 -f build/lc/Dockerfile . --push
```