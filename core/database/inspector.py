from sqlalchemy import create_engine, inspect, text
import pandas as pd

class DbInspector:
    """
    Hedef veritabanına bağlanıp şema, tablo ve view bilgilerini okuyan sınıf.
    """
    def __init__(self, conn_info: dict):
        self.conn_info = conn_info
        self.engine = self._create_engine()
        self.inspector = inspect(self.engine)

    def _create_engine(self):
        url = f"postgresql://{self.conn_info['user']}:{self.conn_info['password']}@" \
              f"{self.conn_info['host']}:{self.conn_info['port']}/{self.conn_info['dbname']}"
        return create_engine(url)

    def get_schemas(self):
        return self.inspector.get_schema_names()

    def get_tables(self, schema: str):
        return self.inspector.get_table_names(schema=schema)

    def get_views(self, schema: str):
        return self.inspector.get_view_names(schema=schema)

    def get_columns(self, schema: str, table: str):
        return self.inspector.get_columns(table_name=table, schema=schema)

    def execute_query(self, sql: str, limit=100):
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql_query(text(sql), conn)
                return {"status": True, "data": result}
        except Exception as e:
            return {"status": False, "error": str(e)}