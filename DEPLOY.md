# 阿里云部署步骤

## 最简单方式

首次使用先双击 `配置免密登录.command`，输入一次服务器 root 密码，之后 Mac 登录服务器就不再要密码。

然后双击 `一键部署.command`，脚本已写死服务器 `139.196.232.73`，会自动增量同步改动文件、安装 Docker、启动系统，全程不需要再输入密码。

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
