from app.utils.database import engine
from app.models.base import Base
from sqlalchemy import text

print("Testing database connection...")
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Database connection OK.")
except Exception as e:
    print("Database connection FAILED:", e)
    exit(1)

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
