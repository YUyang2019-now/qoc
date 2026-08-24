#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "正在安装 Docker，请稍候..."
  curl -fsSL https://get.docker.com | sh
fi

if command -v systemctl >/dev/null 2>&1; then
  systemctl enable --now docker >/dev/null 2>&1 || true
elif command -v service >/dev/null 2>&1; then
  service docker start >/dev/null 2>&1 || true
fi

echo "正在启动 QOC 系统..."
docker compose up -d --build
sleep 3

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -n "$IP" ]; then
  echo "部署完成，浏览器打开 http://$IP"
else
  echo "部署完成，浏览器打开 http://服务器IP"
fi
docker compose ps
