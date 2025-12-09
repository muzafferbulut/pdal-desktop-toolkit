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