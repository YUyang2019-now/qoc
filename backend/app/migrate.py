import argparse
import secrets
from datetime import datetime

from .db import Base, SessionLocal, engine
from .main import seed_defaults
from .models import ImportBatch
from .routes import confirm_import
from .services.importer import parse_workbook, store_staging


def main():
    parser = argparse.ArgumentParser(description="首次迁移 Excel 到 QOC 数据库")
    parser.add_argument("path", help="Excel 文件路径")
    parser.add_argument("--date", help="快照日期 YYYY-MM-DD，默认从文件名识别")
    parser.add_argument("--force", action="store_true", help="允许重复执行迁移")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    seed_defaults()
    db = SessionLocal()
    try:
        existing = db.query(ImportBatch).filter(ImportBatch.status == "done").first()
        if existing and not args.force:
            print("数据库已有完成导入，使用 --force 可重新迁移")
            return

        snapshot_date, summaries, rows = parse_workbook(
            args.path, snapshot_date=args.date, include_master=True
        )
        print(f"识别日期：{snapshot_date}，共 {len(rows)} 行")
        for summary in summaries:
            print(f"  {summary['sheet_name']}: {summary['row_count']} 行")

        token = f"migration-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        store_staging(db, token, rows)
        db.add(
            ImportBatch(
                token=token,
                filename=args.path,
                file_size=0,
                import_date=snapshot_date,
                status="preview",
                summary_json='{"include_master": true, "migration": true}',
            )
        )
        db.commit()
        batch = confirm_import(db, token)
        print(f"迁移完成，导入记录 #{batch.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
