"""
Script to seed admin users from a configuration file.
This bypasses the public registration endpoint which only allows student registration.

Usage:
    python seed_admins.py                    # Seed from seed_admins.json
    python seed_admins.py --file custom.json # Seed from custom file
"""
import asyncio
import json
import uuid
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.user import User
from app.models.organization import Organization
from app.utils.password import hash_password


DEFAULT_SEED_FILE = Path(__file__).parent / "seed_admins.json"
DEFAULT_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def create_admin(session: AsyncSession, name: str, email: str, password: str, org_id: uuid.UUID) -> User | None:
    """Create a single admin user. Returns the user if created, None if already exists."""
    # Check if user already exists
    result = await session.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        print(f"  ⚠ Skipping: User with email '{email}' already exists.")
        return None
    
    # Get the organization
    result = await session.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()
    
    if not org:
        print(f"  ✗ Error: Organization not found for ID {org_id}")
        return None
    
    # Generate username from email
    username = email.split("@")[0].lower()
    username = "".join(c if c.isalnum() or c == "_" else "_" for c in username)
    
    # Check if username exists and add suffix if needed
    suffix = 1
    base_username = username
    while True:
        result = await session.execute(select(User).where(User.username == username))
        if not result.scalar_one_or_none():
            break
        username = f"{base_username}{suffix}"
        suffix += 1
    
    # Create the admin user
    admin_user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        full_name=name,
        role=UserRole.ADMIN,
        is_active=True,
        organization_id=org_id,
    )
    
    session.add(admin_user)
    await session.flush()
    await session.refresh(admin_user)
    
    print(f"  ✓ Created: {email} (username: {username})")
    return admin_user


async def seed_admins_from_config(seed_file: Path) -> None:
    """Seed admin users from a JSON configuration file."""
    if not seed_file.exists():
        print(f"Error: Seed file not found: {seed_file}")
        return
    
    with open(seed_file) as f:
        config = json.load(f)
    
    admins = config.get("admins", [])
    org_id = config.get("organization_id", str(DEFAULT_ORG_ID))
    
    if not admins:
        print("No admins found in configuration file.")
        return
    
    print(f"Seeding {len(admins)} admin(s) from {seed_file}...")
    
    async with AsyncSessionLocal() as session:
        created_count = 0
        skipped_count = 0
        
        for admin_data in admins:
            name = admin_data["name"]
            email = admin_data["email"]
            password = admin_data["password"]
            
            result = await create_admin(session, name, email, password, uuid.UUID(org_id))
            if result:
                created_count += 1
            else:
                skipped_count += 1
        
        await session.commit()
        
        print(f"\nSummary:")
        print(f"  Created: {created_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Total: {len(admins)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed admin users from a JSON configuration file")
    parser.add_argument(
        "--file", 
        type=Path, 
        default=DEFAULT_SEED_FILE,
        help=f"Path to seed configuration file (default: {DEFAULT_SEED_FILE})"
    )
    
    args = parser.parse_args()
    asyncio.run(seed_admins_from_config(args.file))
