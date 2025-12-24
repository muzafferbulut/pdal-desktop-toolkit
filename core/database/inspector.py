from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SAWarning
import pandas as pd
import warnings

warnings.filterwarnings("ignore", category=SAWarning, message=".*Did not recognize type 'pcpatch'.*")

class DbInspector:
    
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

    def validate_pc_table(self, schema: str, table: str) -> bool:
        try:
            columns = [col['name'].lower() for col in self.get_columns(schema, table)]
            required = {'id', 'patch', 'pcid', 'source', 'created_at'}
            return required.issubset(set(columns))
        except Exception:
            return False

    def execute_query(self, sql: str):
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql_query(text(sql), conn)
                return {"status": True, "data": result}
        except Exception as e:
            return {"status": False, "error": str(e)}

    def create_schema(self, schema_name: str):
        sql = f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'
        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
                return {"status": True}
        except Exception as e:
            return {"status": False, "error": str(e)}

    def create_pc_table(self, schema_name: str, table_name: str):
        create_sql = f"""
        CREATE TABLE "{schema_name}"."{table_name}" (
            id SERIAL PRIMARY KEY,
            pcid INTEGER, 
            patch public.PCPATCH,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        trigger_func = f"""
        CREATE OR REPLACE FUNCTION "{schema_name}"."fn_fill_pcid_{table_name}"()
        RETURNS TRIGGER AS $$
        BEGIN
            -- patch verisinin içindeki gerçek ID'yi (örneğin 3) otomatik kolona yazar
            NEW.pcid := public.pc_pcid(NEW.patch); 
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        trigger_bind = f"""
        CREATE TRIGGER "trg_fill_pcid_{table_name}"
        BEFORE INSERT ON "{schema_name}"."{table_name}"
        FOR EACH ROW EXECUTE FUNCTION "{schema_name}"."fn_fill_pcid_{table_name}"();
        """

        try:
            with self.engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.execute(text(trigger_func))
                conn.execute(text(trigger_bind))
                conn.commit()
                return {"status": True}
        except Exception as e:
            return {"status": False, "error": str(e)}