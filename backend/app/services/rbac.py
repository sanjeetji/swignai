"""RBAC helpers — resolve a user's permissions from their roles (blueprint/19)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import Permission, Role, RolePermission, UserRole


async def user_roles(db: AsyncSession, user) -> list[str]:
    rows = await db.execute(
        select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)
    )
    return [r[0] for r in rows.all()]


async def user_permissions(db: AsyncSession, user) -> set[str]:
    rows = await db.execute(
        select(Permission.key)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user.id)
    )
    return {r[0] for r in rows.all()}


async def has_role(db: AsyncSession, user, role_name: str) -> bool:
    return role_name in await user_roles(db, user)
