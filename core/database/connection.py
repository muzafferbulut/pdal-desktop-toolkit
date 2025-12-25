from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DB_NAME = "app.db"
DB_URL = f"sqlite:///{DB_NAME}"

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_db(self):
        """Veritabanı tablolarını oluşturur (yoksa)."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Veritabanı işlemleri için yeni bir oturum açar."""
        return self.SessionLocal()