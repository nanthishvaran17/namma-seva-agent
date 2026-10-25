"""
Administrative CLI Commands for Namma Seva Agent.

FIRST ADMIN INITIALIZATION (CLI ONLY):
Public endpoints cannot assign role='ADMIN'. The initial administrator account
MUST be created directly on the server console using this CLI tool or an offline seed.

Usage:
    python -m backend.app.cli create-admin --email admin@tnega.gov.in --password "AdminPass123!" --full-name "TNeGA SuperAdmin"
"""

import sys
import asyncio
import argparse
from sqlalchemy import select

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.core.security import get_password_hash

async def create_admin(email: str, password: str, full_name: str) -> int:
    clean_email = email.strip().lower()
    if not clean_email or "@" not in clean_email:
        print("Error: Valid email address is required.", file=sys.stderr)
        return 1
    if not password or len(password) < 8:
        print("Error: Password must be at least 8 characters.", file=sys.stderr)
        return 1

    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.email == clean_email))
        existing = res.scalar_one_or_none()
        if existing:
            if existing.role == "ADMIN":
                print(f"User '{clean_email}' already exists and is already an ADMIN.")
                return 0
            existing.role = "ADMIN"
            session.add(existing)
            await session.commit()
            print(f"Successfully updated user '{clean_email}' to role=ADMIN.")
            return 0

        admin_user = User(
            email=clean_email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role="ADMIN",
            is_active=True
        )
        session.add(admin_user)
        await session.commit()
        print(f"Successfully created administrator '{clean_email}' with role=ADMIN.")
        return 0

def main():
    parser = argparse.ArgumentParser(description="Namma Seva Administrative CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    admin_parser = subparsers.add_parser("create-admin", help="Create or escalate an administrator account")
    admin_parser.add_argument("--email", required=True, help="Administrator email address")
    admin_parser.add_argument("--password", required=True, help="Administrator password")
    admin_parser.add_argument("--full-name", default="System Administrator", help="Administrator display name")

    export_parser = subparsers.add_parser("export-playbooks", help="Export playbooks from DB ground truth to disk JSON files")
    migrate_parser = subparsers.add_parser("migrate-encryption", help="Batch encrypt legacy plaintext database rows to AES-256-GCM")

    reindex_parser = subparsers.add_parser("reindex-blind-index", help="Reindex phone blind indexes using specified key version")
    reindex_parser.add_argument("--key-version", default="1", help="Blind index key version tag to use (default: '1')")

    args = parser.parse_args()
    if args.command == "create-admin":
        code = asyncio.run(create_admin(args.email, args.password, args.full_name))
        sys.exit(code)
    elif args.command == "export-playbooks":
        from backend.app.playbooks.seeder import export_db_playbooks_to_disk
        async def run_export():
            async with AsyncSessionLocal() as session:
                return await export_db_playbooks_to_disk(session)
        count = asyncio.run(run_export())
        print(f"Successfully exported {count} playbooks from DB to disk.")
        sys.exit(0)
    elif args.command == "migrate-encryption":
        from backend.app.db.migrations.encrypt_plaintext_rows import migrate_plaintext_rows_to_encryption
        async def run_migration():
            async with AsyncSessionLocal() as session:
                return await migrate_plaintext_rows_to_encryption(session)
        stats = asyncio.run(run_migration())
        print(f"Encryption migration completed successfully: {stats}")
        sys.exit(0)
    elif args.command == "reindex-blind-index":
        from backend.app.db.migrations.reindex_blind_index import reindex_all_phone_blind_indexes
        async def run_reindex():
            async with AsyncSessionLocal() as session:
                return await reindex_all_phone_blind_indexes(session, key_version=args.key_version)
        stats = asyncio.run(run_reindex())
        print(f"Blind index reindexing completed successfully: {stats}")
        sys.exit(0)

if __name__ == "__main__":
    main()
