"""Admin authentication backend"""
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.database.models import User
from app.core.security import verify_password
from app.core.config import settings


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # Check .env credentials first (takes priority)
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            request.session.update({"admin_id": "admin", "admin_name": username})
            return True

        # Fall back to database lookup
        db: Session = SessionLocal()
        try:
            user = (
                db.query(User)
                .filter(
                    (User.username == username) | (User.email == username),
                    User.user_type == "admin",
                    User.is_active == True,
                )
                .first()
            )
            if user and verify_password(password, user.password):
                request.session.update({"admin_id": str(user.id), "admin_name": user.username})
                return True
        finally:
            db.close()
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "admin_id" in request.session


authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
