from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def hash_password(password: str):
    password = password[:72]   # 🔥 MUST KEEP THIS
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    plain_password = plain_password[:72]  # important
    return pwd_context.verify(plain_password, hashed_password)