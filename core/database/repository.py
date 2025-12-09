from .models import BatchPreset, DbConnection
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

    def save_connection(self, conn_data: dict) -> bool:
        session = self.db_manager.get_session()
        try:
            conn = DbConnection(
                name=conn_data["name"],
                db_type=conn_data.get("db_type", "postgresql"),
                host=conn_data.get("host", "localhost"),
                port=int(conn_data.get("port", 5432)),
                database_name=conn_data["database_name"],
                username=conn_data.get("username"),
                password=conn_data.get("password")
            )
            session.add(conn)
            session.commit()
            return True
        except Exception as e:
            print(f"DB Error (Save Conn): {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_connections(self) -> list:
        session = self.db_manager.get_session()
        try:
            conns = session.query(DbConnection).all()
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": c.db_type,
                    "host": c.host,
                    "port": c.port,
                    "dbname": c.database_name,
                    "user": c.username,
                    "password": c.password
                } for c in conns
            ]
        except Exception:
            return []
        finally:
            session.close()

    def delete_connection(self, conn_id: int) -> bool:
        session = self.db_manager.get_session()
        try:
            conn = session.query(DbConnection).filter(DbConnection.id == conn_id).first()
            if conn:
                session.delete(conn)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()