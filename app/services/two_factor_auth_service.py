"""Two-factor authentication service"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timezone
from app.database.models import TwoFactorAuth, User
import pyotp
import json
import secrets


class TwoFactorAuthService:
    """Service for managing two-factor authentication"""

    @staticmethod
    def setup_2fa(db: Session, user_id: int, auth_method: str, phone_number: str = None) -> TwoFactorAuth:
        """Setup 2FA for a user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if 2FA already exists
        existing_2fa = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        if existing_2fa and existing_2fa.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Two-factor authentication is already enabled for this account"
            )

        # Generate TOTP secret if method is TOTP
        totp_secret = None
        if auth_method.upper() == "TOTP":
            totp_secret = pyotp.random_base32()

        # Generate backup codes
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        backup_codes_json = json.dumps(backup_codes)

        # Create or update 2FA record
        if existing_2fa:
            existing_2fa.auth_method = auth_method
            existing_2fa.phone_number = phone_number
            existing_2fa.totp_secret = totp_secret
            existing_2fa.backup_codes = backup_codes_json
            existing_2fa.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing_2fa)
            return existing_2fa
        else:
            two_factor = TwoFactorAuth(
                user_id=user_id,
                auth_method=auth_method,
                phone_number=phone_number,
                totp_secret=totp_secret,
                backup_codes=backup_codes_json,
                is_enabled=False
            )
            db.add(two_factor)
            db.commit()
            db.refresh(two_factor)
            return two_factor

    @staticmethod
    def verify_2fa_code(db: Session, user_id: int, code: str) -> bool:
        """Verify a 2FA code (TOTP)"""
        two_factor = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        if not two_factor or not two_factor.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Two-factor authentication is not enabled"
            )

        if two_factor.auth_method.upper() != "TOTP":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This method does not support TOTP verification"
            )

        # Verify TOTP code (allow 1 window of drift)
        totp = pyotp.TOTP(two_factor.totp_secret)
        is_valid = totp.verify(code, valid_window=1)

        if not is_valid:
            # Check if it's a backup code
            try:
                backup_codes = json.loads(two_factor.backup_codes)
                if code in backup_codes:
                    # Remove the used backup code
                    backup_codes.remove(code)
                    two_factor.backup_codes = json.dumps(backup_codes)
                    db.commit()
                    return True
            except (json.JSONDecodeError, TypeError):
                pass

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )

        return is_valid

    @staticmethod
    def enable_2fa(db: Session, user_id: int, code: str = None) -> TwoFactorAuth:
        """Enable 2FA after verification"""
        two_factor = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        if not two_factor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="2FA setup not found. SetUp 2FA first"
            )

        if two_factor.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Two-factor authentication is already enabled"
            )

        # If code is provided, verify it first
        if code and two_factor.auth_method.upper() == "TOTP":
            TwoFactorAuthService.verify_2fa_code(db, user_id, code)

        two_factor.is_enabled = True
        two_factor.verified_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(two_factor)
        return two_factor

    @staticmethod
    def disable_2fa(db: Session, user_id: int) -> TwoFactorAuth:
        """Disable 2FA"""
        two_factor = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        if not two_factor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="2FA not setup"
            )

        two_factor.is_enabled = False
        two_factor.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(two_factor)
        return two_factor

    @staticmethod
    def get_2fa_status(db: Session, user_id: int) -> TwoFactorAuth:
        """Get 2FA status for a user"""
        two_factor = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        if not two_factor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="2FA not setup"
            )
        return two_factor

    @staticmethod
    def regenerate_backup_codes(db: Session, user_id: int) -> dict:
        """Regenerate backup codes"""
        two_factor = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        if not two_factor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="2FA not setup"
            )

        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        two_factor.backup_codes = json.dumps(backup_codes)
        db.commit()

        return {"backup_codes": backup_codes}

    @staticmethod
    def get_totp_qr_code(db: Session, user_id: int) -> str:
        """Get TOTP QR code URL"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        two_factor = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        if not two_factor or not two_factor.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP not setup. Setup TOTP first"
            )

        totp = pyotp.TOTP(two_factor.totp_secret)
        qr_code_url = totp.provisioning_uri(
            name=user.email,
            issuer_name="LexConnect"
        )
        return qr_code_url
