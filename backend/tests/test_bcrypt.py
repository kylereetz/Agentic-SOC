"""Smoke test: verifies that the bcrypt password hashing library (passlib) is installed and functional."""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
try:
    h = pwd_context.hash("admin123")
    print(f"Hash success: {h}")
except Exception as e:
    print(f"Error: {e}")
