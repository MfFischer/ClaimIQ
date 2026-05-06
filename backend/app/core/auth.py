from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

ROLE_ORDER = {"broker": 1, "lead": 2, "admin": 3}


@dataclass
class AuthContext:
    user_id: str
    role: str


def get_auth_context(
    x_claimiq_user: str | None = Header(default=None, alias="X-ClaimIQ-User"),
    x_claimiq_role: str | None = Header(default=None, alias="X-ClaimIQ-Role"),
) -> AuthContext:
    role = (x_claimiq_role or "broker").strip().lower()
    if role not in ROLE_ORDER:
        raise HTTPException(status_code=400, detail="Invalid X-ClaimIQ-Role header.")
    user_id = (x_claimiq_user or "anonymous").strip() or "anonymous"
    return AuthContext(user_id=user_id, role=role)


def require_role(required_role: str):
    if required_role not in ROLE_ORDER:
        raise ValueError(f"Unknown role: {required_role}")

    def _require(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if ROLE_ORDER[context.role] < ROLE_ORDER[required_role]:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{required_role}' required for this operation.",
            )
        return context

    return _require
