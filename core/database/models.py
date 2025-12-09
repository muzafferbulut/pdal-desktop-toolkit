from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class BatchPreset(Base):
    """
    Kaydedilmiş toplu işlem (Batch Process) ayarlarını tutar.
    """
    __tablename__ = 'batch_presets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)      
    description = Column(String(255), nullable=True)
    pipeline_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<BatchPreset(name='{self.name}')>"
    

class DbConnection(Base):
    """
    Kullanıcının kaydettiği veritabanı bağlantı bilgilerini tutar.
    """
    __tablename__ = 'db_connections'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    db_type = Column(String(20), default="postgresql")
    host = Column(String(100), default="localhost")
    port = Column(Integer, default=5432)
    database_name = Column(String(100), nullable=False)
    username = Column(String(100), nullable=True)
    password = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<DbConnection(name='{self.name}', host='{self.host}')>"