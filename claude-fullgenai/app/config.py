import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "banking-secret-key-change-in-production")
ALGORITHM = "HS512"
