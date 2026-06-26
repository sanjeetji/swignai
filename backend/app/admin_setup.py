"""First super-admin bootstrap (blueprint/19).

No demo admin is seeded — the first super admin is created here, interactively
(`python -m app.admin_setup`) or non-interactively with flags (CI/automation):
    python -m app.admin_setup --email you@x.com --name "You" --password secret123

Idempotent: promotes an existing email to super_admin and (re)sets the password rather
than duplicating. Ensures the structural seed (roles/permissions/presets/plans) exists.
"""
from __future__ import annotations

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import func, select

from .core.db import SessionLocal, init_db
from .core.security import hash_password
from .models.user import Role, User, UserRole
from .seed import seed_if_empty


async def has_super_admin() -> bool:
    async with SessionLocal() as db:
        sa = (await db.execute(select(Role).where(Role.name == "super_admin"))).scalar_one_or_none()
        if not sa:
            return False
        n = (await db.execute(
            select(func.count()).select_from(UserRole).where(UserRole.role_id == sa.id)
        )).scalar_one()
        return n > 0


async def create_super_admin(email: str, name: str, password: str) -> str:
    await init_db()
    await seed_if_empty()  # ensure roles/permissions/presets/plans exist
    async with SessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user is None:
            user = User(email=email, name=name, password_hash=hash_password(password), is_email_verified=True)
            db.add(user)
            await db.flush()
        else:
            user.password_hash = hash_password(password)
        sa = (await db.execute(select(Role).where(Role.name == "super_admin"))).scalar_one()
        link = (await db.execute(
            select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == sa.id)
        )).scalar_one_or_none()
        if link is None:
            db.add(UserRole(user_id=user.id, role_id=sa.id))
        await db.commit()
        return str(user.id)


def _prompt() -> tuple[str, str, str]:
    print("\n— Create the first SwingAI super admin —")
    email = input("  Email: ").strip()
    name = input("  Full name: ").strip() or "Platform Owner"
    while True:
        pw = getpass.getpass("  Password (min 8 chars): ")
        if len(pw) < 8:
            print("  ✗ too short, try again"); continue
        if pw != getpass.getpass("  Confirm password: "):
            print("  ✗ passwords don't match, try again"); continue
        break
    return email, name, pw


def main() -> None:
    ap = argparse.ArgumentParser(description="Create the first super admin")
    ap.add_argument("--email"); ap.add_argument("--name"); ap.add_argument("--password")
    ap.add_argument("--check", action="store_true",
                    help="exit 0 if a super admin exists, else 1 (no changes)")
    args = ap.parse_args()

    if args.check:
        sys.exit(0 if asyncio.run(has_super_admin()) else 1)

    if args.email and args.password:
        email, name, pw = args.email, args.name or "Platform Owner", args.password
    else:
        if not sys.stdin.isatty():
            print("No TTY and no --email/--password given; aborting.", file=sys.stderr)
            sys.exit(1)
        email, name, pw = _prompt()

    uid = asyncio.run(create_super_admin(email, name, pw))
    print(f"\n✓ super admin ready: {email}  (id {uid[:8]}…)\n")


if __name__ == "__main__":
    main()
