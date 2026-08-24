# 阿里云部署步骤

## 最简单方式

首次使用先双击 `配置免密登录.command`，输入一次服务器 root 密码，之后 Mac 登录服务器就不再要密码。

然后双击 `一键部署.command`，脚本已写死服务器 `139.196.232.73`，会自动增量同步改动文件、安装 Docker、启动系统，全程不需要再输入密码。

## GitHub 自动部署

把代码推送到 GitHub 后，可以配置成自动部署到阿里云服务器。

1. 打开 GitHub 仓库的 Settings → Secrets and variables → Actions。
2. 添加一个 Secret：
   - `SERVER_PASSWORD`：阿里云服务器 root 密码
3. 以后每次 `git push` 到 `main`，GitHub 会自动同步代码到服务器并启动系统。

数据库 `data/` 不会被 GitHub 覆盖，服务器上的数据会保留。

GitHub 会把系统打包成 Docker 镜像并推送到 GitHub 容器仓库，服务器直接拉取镜像启动，不再在服务器上安装后端依赖或执行 npm 构建。

## 阿里云镜像仓库（国内拉取更快）

如果从 GitHub 容器仓库拉取太慢，可以改用阿里云容器镜像服务：

1. 打开阿里云控制台，搜索“容器镜像服务 ACR”，进入个人版。
2. 在“访问凭证”里设置镜像仓库密码。
3. 创建命名空间 `qoc`，再创建镜像仓库 `qoc`。
4. 记下镜像仓库地址，例如 `registry.cn-shanghai.aliyuncs.com/qoc/qoc`。
5. 在 GitHub 仓库的 Actions Secrets 里添加：
   - `ACR_ADDRESS`：上面的镜像仓库地址
   - `ACR_USERNAME`：阿里云账号用户名
   - `ACR_PASSWORD`：镜像仓库密码
6. 重新 `git push` 即可，服务器会直接从阿里云拉取镜像。

## 手动方式

## 1. 上传部署包

在 Mac 的终端里执行，把 `服务器IP` 换成阿里云公网 IP：

```bash
scp /Users/yang.yu/Desktop/my/qoc/qoc-deploy.tar.gz root@服务器IP:/opt/
```

如果提示密码，输入阿里云服务器的 root 密码。

## 2. 连接服务器并解压

```bash
ssh root@服务器IP
cd /opt
mkdir -p qoc
tar -xzf qoc-deploy.tar.gz -C qoc
cd qoc
```

## 3. 安装 Docker

第一次部署时需要安装：

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
```

如果服务器没有网络限制，安装完成后检查：

```bash
docker compose version
```

## 4. 启动系统

```bash
docker compose up -d --build
```

前端已经在本地打包好并放进部署包，服务器不会执行 npm 构建，只会安装后端依赖并启动。

启动后访问 `http://服务器IP`，默认账号 `admin`，密码 `admin123`。

## 5. 确认端口

服务使用 80 端口，你现有的安全组规则已经放行 80，不需要再额外开放端口。

如果服务器本身还开着防火墙，再执行：

```bash
firewall-cmd --add-port=80/tcp --permanent && firewall-cmd --reload
```

也可以直接在服务器 `/opt/qoc` 目录执行 `bash start.sh`，它会自动安装 Docker 并启动系统。

## 6. 以后更新

重新打包上传后，在服务器 `/opt/qoc` 里执行：

```bash
docker compose up -d --build
```

数据库文件在 `/opt/qoc/data/qoc.db`，备份时直接复制它即可。
