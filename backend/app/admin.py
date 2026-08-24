import argparse

from .auth import hash_password
from .db import SessionLocal
from .models import User


def reset_admin_password(password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            user = User(username="admin")
            db.add(user)
        user.password_hash = hash_password(password)
        db.commit()
        print("管理员密码已重置")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="QOC 管理员维护命令")
    sub = parser.add_subparsers(dest="command", required=True)
    reset = sub.add_parser("reset-admin", help="重置管理员密码")
    reset.add_argument("password", help="新密码")
    args = parser.parse_args()
    if args.command == "reset-admin":
        reset_admin_password(args.password)


if __name__ == "__main__":
    main()
