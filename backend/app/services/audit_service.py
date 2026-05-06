from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.claim import AuditLog

settings = get_settings()


async def write_audit_log(
    db: AsyncSession,
    *,
    actor_user: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    row = AuditLog(
        actor_user=actor_user,
        actor_role=actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id or "",
        details=details or {},
    )
    db.add(row)
    return row


async def purge_expired_audit_logs(db: AsyncSession) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.audit_retention_days)
    result = await db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))
    await db.commit()
    return result.rowcount or 0


async def export_audit_logs(
    db: AsyncSession,
    *,
    from_at: datetime,
    to_at: datetime,
    limit: int = 2000,
) -> list[AuditLog]:
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.created_at >= from_at, AuditLog.created_at <= to_at)
        .order_by(AuditLog.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())
