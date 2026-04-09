import bcrypt as bcrypt_module
from passlib.context import CryptContext

# Passlib 1.7.x still looks for bcrypt.__about__.__version__ on import.
# Newer bcrypt releases removed that attribute, so we provide a tiny shim.
if not hasattr(bcrypt_module, "__about__"):
    class _BcryptAbout:
        __version__ = getattr(bcrypt_module, "__version__", "unknown")

    bcrypt_module.__about__ = _BcryptAbout()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def hash_password(password: str):
    password = password[:72]   # 🔥 MUST KEEP THIS
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    plain_password = plain_password[:72]  # important
    return pwd_context.verify(plain_password, hashed_password)
