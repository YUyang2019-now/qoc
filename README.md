# QOC 商品管理系统

用网页和数据库替代原来的 Excel 大表，保存商品档案、库存和销量快照。每天只需要把运营发的 Excel 上传一次，系统会自动解析并更新当天数据，同时保留历史快照。

## 功能

- 共用账号登录，账号密码可在系统里修改
- 商品档案管理：品牌、条码、名称、规格、价格、供应商等信息
- 库存与销量查询：按品牌 / 渠道 / SKU 筛选
- 数据趋势：单个商品的历史库存与销量曲线
- 每日导入：上传运营 Excel，预览后确认入库；同一天重复导入会覆盖当天快照
- 低库存预警：按预警值列出库存不足的商品
- 快照保留：设置保留天数，系统每天自动清理过老快照，也可手动立即清理
- 数据导出：商品、库存、销量 CSV

## 本地开发

后端：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
QOC_DATA_DIR=data .venv/bin/python -m app.migrate "/path/to/内裤产品表.xlsx"
QOC_DATA_DIR=data .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

浏览器打开前端地址，默认账号 `admin`，密码 `admin123`，登录后可在“设置”里改密码和低库存预警值。

“设置”里的快照保留天数默认 60 天。如果每天导入全量运营表，建议按磁盘空间调整为 30-60 天；更早的快照会被系统每天自动清理。

首次使用需要迁移一次旧 Excel：在“数据导入”页上传完整工作簿并勾选“首次迁移（同时导入商品档案）”。之后每天只需上传运营更新的 Excel，不要勾选该项。

## Docker 部署

```bash
docker compose up -d --build
```

默认访问 `http://服务器IP`（80 端口）。数据保存在项目目录的 `data/` 中，升级代码不会丢数据。
前端文件在本地打包进部署包，服务器不会执行 npm 构建。

如果想把本地已经迁移好的数据库带到服务器，先在项目根目录放一份：

```bash
mkdir -p data
cp backend/data/qoc.db data/qoc.db
```

再执行 `docker compose up -d --build`。以后备份数据库就是直接复制 `data/qoc.db`。

如需修改初始账号密码：

```bash
QOC_ADMIN_USER=myadmin QOC_ADMIN_PASSWORD=mysecret docker compose up -d --build
```

## 数据库文件

SQLite 数据库默认在 `backend/data/qoc.db`；Docker 部署时使用项目根目录的 `data/qoc.db`（容器内是 `/data/qoc.db`）。迁移或备份时直接复制对应文件即可。
