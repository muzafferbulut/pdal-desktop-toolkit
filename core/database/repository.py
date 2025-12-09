from .models import BatchPreset
from .connection import DatabaseManager
import json

class Repository:
    """
    Tüm veritabanı CRUD (Create, Read, Update, Delete) işlemlerini yönetir.
    """
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_manager.init_db()

    def save_batch_preset(self, name: str, pipeline_config: list, description: str = "") -> bool:
        """Yeni bir batch preset kaydeder."""
        session = self.db_manager.get_session()
        try:
            json_str = json.dumps(pipeline_config)
            
            preset = BatchPreset(
                name=name, 
                description=description, 
                pipeline_json=json_str
            )
            session.add(preset)
            session.commit()
            return True
        except Exception as e:
            print(f"DB Error (Save): {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_all_presets(self) -> list:
        """Tüm kayıtlı presetleri döndürür."""
        session = self.db_manager.get_session()
        try:
            presets = session.query(BatchPreset).order_by(BatchPreset.created_at.desc()).all()
            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "config": json.loads(p.pipeline_json),
                    "date": p.created_at.strftime("%Y-%m-%d %H:%M")
                }
                for p in presets
            ]
        except Exception as e:
            print(f"DB Error (Get All): {e}")
            return []
        finally:
            session.close()

    def delete_preset(self, preset_id: int) -> bool:
        """ID'ye göre preset siler."""
        session = self.db_manager.get_session()
        try:
            preset = session.query(BatchPreset).filter(BatchPreset.id == preset_id).first()
            if preset:
                session.delete(preset)
                session.commit()
                return True
            return False
        except Exception as e:
            print(f"DB Error (Delete): {e}")
            session.rollback()
            return False
        finally:
            session.close()