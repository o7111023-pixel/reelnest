from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from src.core.security import (
    create_access_token,
    create_refresh_token,
)
from src.models.user import User


async def test_register_user(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "pytest-register@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "pytest-register@example.com"
    assert data["is_active"] is False
    assert "id" in data


async def test_register_duplicate_email(client):
    user_data = {
        "email": "duplicate@example.com",
        "password": "TestPassword123",
    }

    first_response = await client.post(
        "/auth/register",
        json=user_data,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/auth/register",
        json=user_data,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "User with this email already exists"
    )


async def test_login_invalid_password(client):
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "login-test@example.com",
            "password": "TestPassword123",
        },
    )

    assert register_response.status_code == 201

    login_response = await client.post(
        "/auth/login",
        json={
            "email": "login-test@example.com",
            "password": "WrongPassword123",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json()["detail"] == (
        "Incorrect email or password"
    )


async def test_login_success(client, activate_user):
    email = "login-success@example.com"
    password = "TestPassword123"

    register_response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    await activate_user(email)

    login_response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


async def test_get_current_user(client, activate_user):
    email = "current-user@example.com"
    password = "TestPassword123"

    register_response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    user_id = register_response.json()["id"]

    await activate_user(email)

    login_response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    me_response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert me_response.status_code == 200

    data = me_response.json()

    assert data["id"] == user_id
    assert data["email"] == email
    assert data["is_active"] is True


async def test_get_current_user_without_token(client):
    response = await client.get("/auth/me")

    assert response.status_code == 401


async def test_refresh_token_cannot_access_protected_endpoint(
    client,
    activate_user,
):
    email = "refresh-as-access@example.com"
    password = "TestPassword123"

    register_response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    await activate_user(email)

    login_response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {refresh_token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid authentication credentials"
    )


async def test_refresh_token(client, activate_user):
    email = "refresh-test@example.com"
    password = "TestPassword123"

    register_response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    await activate_user(email)

    login_response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    refresh_response = await client.post(
        "/auth/refresh",
        params={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200

    data = refresh_response.json()

    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


async def test_login_inactive_user(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "inactive-user@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 201

    login_response = await client.post(
        "/auth/login",
        json={
            "email": "inactive-user@example.com",
            "password": "TestPassword123",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json()["detail"] == (
        "User account is not active"
    )


async def test_activate_user_invalid_token(client):
    response = await client.get(
        "/auth/activate/invalid-activation-token",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid activation token"


async def test_activate_user_expired_token(client, db_session):
    email = "expired-token@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 201

    result = await db_session.execute(
        select(User).where(User.email == email),
    )
    user = result.scalar_one()

    user.activation_token_expires_at = (
        datetime.now(timezone.utc) - timedelta(hours=1)
    )

    await db_session.commit()

    activation_response = await client.get(
        f"/auth/activate/{user.activation_token}",
    )

    assert activation_response.status_code == 400
    assert activation_response.json()["detail"] == (
        "Activation token has expired"
    )


async def test_refresh_token_invalid(client):
    response = await client.post(
        "/auth/refresh",
        params={"refresh_token": "invalid-refresh-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


async def test_get_current_user_not_found(client):
    access_token = create_access_token(user_id=999999)

    response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User not found"


async def test_activate_user_success(client, db_session):
    email = "activate-success@example.com"

    register_response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123",
        },
    )

    assert register_response.status_code == 201

    result = await db_session.execute(
        select(User).where(User.email == email),
    )
    user = result.scalar_one()

    activation_response = await client.get(
        f"/auth/activate/{user.activation_token}",
    )

    assert activation_response.status_code == 200
    assert activation_response.json()["message"] == (
        "User account activated successfully"
    )

    await db_session.refresh(user)

    assert user.is_active is True
    assert user.activation_token is None
    assert user.activation_token_expires_at is None


async def test_refresh_token_inactive_user(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "inactive-refresh@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 201

    user_id = response.json()["id"]

    refresh_token = create_refresh_token(user_id)

    refresh_response = await client.post(
        "/auth/refresh",
        params={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == (
        "User account is not active"
    )
