#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

SERVER_IP="139.196.232.73"
SERVER_PATH="/opt/qoc"

echo "服务器：$SERVER_IP"
echo "正在同步文件到服务器..."
rsync -az --delete \
  --exclude='backend/.venv' \
  --exclude='frontend/node_modules' \
  --exclude='backend/data' \
  --exclude='data/uploads' \
  --exclude='qoc-deploy.tar.gz' \
  --exclude='.DS_Store' \
  ./ "root@$SERVER_IP:$SERVER_PATH/"

echo "正在启动系统..."
ssh "root@$SERVER_IP" "cd $SERVER_PATH && bash start.sh"

echo "全部完成"
