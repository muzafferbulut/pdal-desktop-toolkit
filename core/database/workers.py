import pdal
import json
import numpy as np
import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from sqlalchemy import text, create_engine

class DbWorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

class DbImportWorker(QThread):
    
    def __init__(self, source_data, conn_info, schema, table, source_name, is_array=False, srid="4326"):
        super().__init__()
        self.source_data, self.conn_info, self.schema, self.table = source_data, conn_info, schema, table
        self.source_name, self.is_array, self.srid = source_name, is_array, srid
        self.signals = DbWorkerSignals()

    def run(self):
        try:
            self.signals.progress.emit(-1)
            writer_config = {
                "type": "writers.pgpointcloud",
                "connection": f"host={self.conn_info['host']} port={self.conn_info['port']} dbname={self.conn_info['dbname']} user={self.conn_info['user']} password={self.conn_info['password']}",
                "table": self.table, "schema": self.schema, "column": "patch",
                "srid": self.srid, "compression": "dimensional", "overwrite": False
            }
            chipper = {"type": "filters.chipper", "capacity": 1000}
            pipeline = pdal.Pipeline(json.dumps([chipper, writer_config]), [self.source_data]) if self.is_array else pdal.Pipeline(json.dumps([self.source_data, chipper, writer_config]))
            
            count = pipeline.execute()

            url = f"postgresql://{self.conn_info['user']}:{self.conn_info['password']}@{self.conn_info['host']}:{self.conn_info['port']}/{self.conn_info['dbname']}"
            engine = create_engine(url)
            with engine.connect() as conn:
                conn.execute(text(f'UPDATE "{self.schema}"."{self.table}" SET source = :s WHERE source IS NULL'), {"s": self.source_name})
                res = conn.execute(text(f'SELECT pcid FROM "{self.schema}"."{self.table}" WHERE pcid IS NOT NULL LIMIT 1')).fetchone()
                if res:
                    actual_pcid = res[0]
                    conn.execute(text(f'ALTER TABLE "{self.schema}"."{self.table}" ALTER COLUMN patch TYPE public.pcpatch({actual_pcid})'))
                conn.commit()

            self.signals.progress.emit(100)
            self.signals.finished.emit(f"{count} points have been successfully saved in the database.")
        except Exception as e:
            self.signals.error.emit(str(e))

class DbLoadWorker(QThread):

    def __init__(self, conn_info, schema, table, where_clause=""):
        super().__init__()
        self.conn_info, self.schema, self.table, self.where = conn_info, schema, table, where_clause
        self.signals = DbWorkerSignals()

    def run(self):
        try:
            self.signals.progress.emit(-1)
            config = {
                "type": "readers.pgpointcloud", "schema": self.schema, "table": self.table, "column": "patch", "where": self.where,
                "connection": f"host={self.conn_info['host']} port={self.conn_info['port']} dbname={self.conn_info['dbname']} user={self.conn_info['user']} password={self.conn_info['password']}"
            }
            pipeline = pdal.Pipeline(json.dumps([config, {"type": "filters.decimation", "step": 10}]))
            pipeline.execute()
            
            if not pipeline.arrays: raise Exception("Sorgu sonucu nokta bulunamadı.")
            df = pd.DataFrame(np.concatenate(pipeline.arrays))
            
            self.signals.progress.emit(100)
            self.signals.finished.emit({
                "data": df, "metadata": pipeline.metadata, "conn": self.conn_info,
                "bounds": {"minx": float(df['X'].min()), "maxx": float(df['X'].max()), "miny": float(df['Y'].min()), "maxy": float(df['Y'].max())},
                "table_info": f"{self.schema}.{self.table}", "query_filter": self.where
            })
        except Exception as e:
            self.signals.progress.emit(0); self.signals.error.emit(str(e))

class DbQueryWorker(QThread):
    finished_success = pyqtSignal(object)
    finished_error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, inspector, sql):
        super().__init__()
        self.inspector, self.sql = inspector, sql
        
    def run(self):
        try:
            res = self.inspector.execute_query(self.sql)
            if res["status"]: self.finished_success.emit(res["data"])
            else: self.finished_error.emit(res["error"])
        finally: self.finished.emit()