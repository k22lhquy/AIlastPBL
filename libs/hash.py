from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)