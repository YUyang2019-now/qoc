from datetime import date, timedelta

from ..db import SessionLocal
from ..models import Setting, SnapshotRow

DEFAULT_RETENTION_DAYS = 60


def get_retention_days(db):
    setting = db.get(Setting, "snapshot_retention_days")
    if not setting or not setting.value:
        return DEFAULT_RETENTION_DAYS
    try:
        return max(1, int(setting.value))
    except (TypeError, ValueError):
        return DEFAULT_RETENTION_DAYS


def cleanup_old_snapshots(db):
    days = get_retention_days(db)
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    deleted = (
        db.query(SnapshotRow)
        .filter(SnapshotRow.date < cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted, cutoff


def run_cleanup_once():
    db = SessionLocal()
    try:
        return cleanup_old_snapshots(db)
    finally:
        db.close()
