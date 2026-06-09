from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    # bcrypt hard limit is 72 bytes
    return pwd_context.hash(password[:72])

def verify_password(password: str, hashPassword: str) -> bool:
    # truncate same way before verifying
    return pwd_context.verify(password[:72], hashPassword)