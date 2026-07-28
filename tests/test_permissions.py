import pytest
from fastapi import HTTPException

from app.core.permissions import build_current_user


def test_get_current_user_defaults_to_admin_for_local_compatibility() -> None:
    user = build_current_user()

    assert user.role == "admin"
    assert user.can("ai:execute")


def test_get_current_user_reads_role_and_user_id_headers() -> None:
    user = build_current_user(
        x_user_id="7",
        x_user_role="vendedor",
    )

    assert user.user_id == 7
    assert user.role == "vendedor"
    assert user.can("inventory:read")
    assert not user.can("inventory:write")


def test_get_current_user_rejects_unknown_role() -> None:
    with pytest.raises(HTTPException) as exc:
        build_current_user(x_user_role="externo")

    assert exc.value.status_code == 403
