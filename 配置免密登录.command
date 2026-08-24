#!/bin/bash
set -euo pipefail

SERVER_IP="139.196.232.73"
KEY="$HOME/.ssh/id_ed25519"

if [ ! -f "$KEY" ]; then
  echo "正在生成本机登录密钥..."
  ssh-keygen -t ed25519 -N "" -f "$KEY" -C "qoc-deploy"
fi

if command -v ssh-copy-id >/dev/null 2>&1; then
  ssh-copy-id -i "$KEY.pub" "root@$SERVER_IP"
else
  cat "$KEY.pub" | ssh "root@$SERVER_IP" \
    "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
fi

echo "免密登录已配置，以后部署不再需要输入密码"
