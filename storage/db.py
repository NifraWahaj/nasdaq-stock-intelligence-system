import os
from sqlalchemy import create_engine

# Use os.getenv so it works both locally and in Docker
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/nasdaq_db")

engine = create_engine(DATABASE_URL)

def test_connection():
    try:
        with engine.connect() as conn:
            print("Successfully connected to the PostgreSQL container!")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()