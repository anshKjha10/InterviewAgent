import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
DB_PATH = os.getenv("DB_PATH", "interview_prep.db")
GROQ_MODEL = "llama-3.3-70b-versatile"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
