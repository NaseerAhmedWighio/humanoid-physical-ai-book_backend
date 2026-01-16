from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt import InvalidTokenError, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy.orm import Session
from ..models.user import User
from ..database import get_db, get_db_with_retry
import os
from dotenv import load_dotenv
import hashlib
import secrets
import logging
import time

load_dotenv()

# Password hashing - with fallback mechanism
try:
    # Try to initialize bcrypt context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__ident="2b", bcrypt__rounds=12)
    BCRYPT_AVAILABLE = True
except Exception:
    # Fallback to alternative if bcrypt is problematic
    BCRYPT_AVAILABLE = False

def hash_password_fallback(password: str) -> str:
    """Fallback password hashing using PBKDF2 if bcrypt fails"""
    # Truncate to 70 characters to stay under any potential limits
    if len(password) > 70:
        password = password[:70]

    # Use PBKDF2 with SHA-256 as fallback
    salt = secrets.token_hex(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256',
                                  password.encode('utf-8'),
                                  salt.encode('utf-8'),
                                  100000)  # 100,000 iterations
    return f"pbkdf2${salt}${pwdhash.hex()}"

def verify_password_fallback(plain_password: str, hashed_password: str) -> bool:
    """Verify password using fallback method"""
    if not hashed_password.startswith('pbkdf2$'):
        return False

    try:
        _, salt, stored_hash = hashed_password.split('$')
        # Truncate to 70 characters if needed
        if len(plain_password) > 70:
            plain_password = plain_password[:70]

        pwdhash = hashlib.pbkdf2_hmac('sha256',
                                      plain_password.encode('utf-8'),
                                      salt.encode('utf-8'),
                                      100000)
        return pwdhash.hex() == stored_hash
    except:
        return False

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

logger = logging.getLogger(__name__)

class UserCreate(BaseModel):
    email: str
    password: str
    has_mobile: bool = False
    has_laptop: bool = False
    has_physical_robot: bool = False
    has_other_hardware: Optional[str] = None
    web_dev_experience: Optional[str] = None
    language_preference: str = 'en'
    personalization_enabled: bool = True

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) > 70:  # Conservative limit under bcrypt's 72-byte limit
            raise ValueError('Password must be 70 characters or fewer to comply with bcrypt limitations')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @model_validator(mode='after')
    def validate_hardware_preferences(self):
        # Check if at least one hardware preference is selected
        if not self.has_mobile and not self.has_laptop and not self.has_physical_robot and not (self.has_other_hardware and self.has_other_hardware.strip()):
            # For registration, we could require at least one hardware preference,
            # but for now we'll allow users to register without hardware preferences
            # and let them set preferences later in their profile
            pass
        return self

class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) > 70:  # Conservative limit under bcrypt's 72-byte limit
            raise ValueError('Password must be 70 characters or fewer to comply with bcrypt limitations')
        if len(v) < 1:  # At least 1 character for login
            raise ValueError('Password cannot be empty')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    has_mobile: bool
    has_laptop: bool
    has_physical_robot: bool
    has_other_hardware: Optional[str] = None
    web_dev_experience: Optional[str] = None
    language_preference: str = 'en'
    personalization_enabled: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class UserRegistration(BaseModel):
    email: str
    password: str
    has_mobile: bool = False
    has_laptop: bool = False
    has_physical_robot: bool = False
    has_other_hardware: Optional[str] = None
    web_dev_experience: Optional[str] = None
    language_preference: str = 'en'
    personalization_enabled: bool = True

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) > 70:  # Conservative limit under bcrypt's 72-byte limit
            raise ValueError('Password must be 70 characters or fewer to comply with bcrypt limitations')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @model_validator(mode='after')
    def validate_hardware_preferences(self):
        # Require at least one hardware preference during registration
        if not self.has_mobile and not self.has_laptop and not self.has_physical_robot and not (self.has_other_hardware and self.has_other_hardware.strip()):
            raise ValueError('At least one hardware preference must be selected (mobile, laptop, physical robot, or other hardware)')
        return self

    @field_validator('language_preference')
    @classmethod
    def validate_language_preference(cls, v):
        # Validate that language preference is one of the allowed values
        allowed_languages = ['en', 'ur']  # English and Urdu
        if v not in allowed_languages:
            raise ValueError(f'Language preference must be one of: {", ".join(allowed_languages)}')
        return v

    @field_validator('web_dev_experience')
    @classmethod
    def validate_web_dev_experience(cls, v):
        if v is None:
            return v
        # Validate that web development experience is one of the allowed values
        allowed_experiences = ['beginner', 'intermediate', 'experienced', 'expert']
        if v not in allowed_experiences:
            raise ValueError(f'Web development experience must be one of: {", ".join(allowed_experiences)}')
        return v

class AuthService:
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        # Check if this is a PBKDF2 hashed password (fallback)
        if hashed_password.startswith('pbkdf2$'):
            return verify_password_fallback(plain_password, hashed_password)

        # Use bcrypt if available
        if BCRYPT_AVAILABLE:
            # Ensure password doesn't exceed bcrypt's 72-byte limit to prevent errors
            # Truncate to 70 characters as a conservative approach to stay under the limit
            if len(plain_password) > 70:
                plain_password = plain_password[:70]
            # Additional safety: truncate at byte level to ensure under 72 bytes
            plain_password_bytes = plain_password.encode('utf-8')
            if len(plain_password_bytes) > 70:
                # Truncate at byte level to ensure we're under the limit
                plain_password_bytes = plain_password_bytes[:70]
                # Decode back to string, handling potential incomplete UTF-8 sequences
                plain_password = plain_password_bytes.decode('utf-8', errors='ignore')
            return pwd_context.verify(plain_password, hashed_password)
        else:
            # Fallback: This shouldn't happen in normal operation since new passwords
            # are hashed with the fallback method, but just in case
            return False

    def get_password_hash(self, password: str) -> str:
        # Use fallback method if bcrypt is not available
        if not BCRYPT_AVAILABLE:
            return hash_password_fallback(password)

        # Otherwise, use bcrypt with safety measures
        # Ensure password doesn't exceed bcrypt's 72-byte limit to prevent errors
        # Truncate to 70 characters as a conservative approach to stay under the limit
        if len(password) > 70:
            password = password[:70]
        # Additional safety: truncate at byte level to ensure under 72 bytes
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 70:
            # Truncate at byte level to ensure we're under the limit
            password_bytes = password_bytes[:70]
            # Decode back to string, handling potential incomplete UTF-8 sequences
            password = password_bytes.decode('utf-8', errors='ignore')
        try:
            return pwd_context.hash(password)
        except Exception:
            # If bcrypt fails for any reason, fall back to our own implementation
            return hash_password_fallback(password)

    def create_user(self, db: Session, user_data: UserCreate) -> User:
        # Check if user already exists
        try:
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # Hash the password
            hashed_password = self.get_password_hash(user_data.password)

            # Create new user
            db_user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                has_mobile=user_data.has_mobile,
                has_laptop=user_data.has_laptop,
                has_physical_robot=user_data.has_physical_robot,
                has_other_hardware=user_data.has_other_hardware,
                web_dev_experience=user_data.web_dev_experience,
                language_preference=user_data.language_preference,
                personalization_enabled=user_data.personalization_enabled
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    def create_user_with_retry(self, user_data: UserCreate) -> User:
        """Create a user with database connection retry logic"""
        for attempt in range(3):  # Try up to 3 times
            try:
                db = get_db_with_retry()
                return self.create_user(db, user_data)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} to create user failed: {e}")
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
            finally:
                try:
                    db.close()
                except:
                    pass

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user or not self.verify_password(password, user.hashed_password):
                return None
            return user
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    def authenticate_user_with_retry(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with database connection retry logic"""
        for attempt in range(3):  # Try up to 3 times
            try:
                db = get_db_with_retry()
                result = self.authenticate_user(db, email, password)
                return result
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} to authenticate user failed: {e}")
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
            finally:
                try:
                    db.close()
                except:
                    pass
        return None

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> TokenData:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            token_data = TokenData(email=email)
        except (InvalidTokenError, ExpiredSignatureError, jwt.PyJWTError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return token_data

    def get_current_user(self,
                        credentials: HTTPAuthorizationCredentials = Depends(security),
                        db: Session = Depends(get_db)) -> User:
        try:
            token = credentials.credentials
            token_data = self.decode_token(token)
            user = db.query(User).filter(User.email == token_data.email).first()
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            return user
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise

    def get_current_user_with_retry(self,
                                  credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """Get current user with database connection retry logic"""
        for attempt in range(3):  # Try up to 3 times
            try:
                db = get_db_with_retry()
                token = credentials.credentials
                token_data = self.decode_token(token)
                user = db.query(User).filter(User.email == token_data.email).first()
                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not validate credentials"
                    )
                return user
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} to get current user failed: {e}")
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
            finally:
                try:
                    db.close()
                except:
                    pass

# Global instance
auth_service = AuthService()