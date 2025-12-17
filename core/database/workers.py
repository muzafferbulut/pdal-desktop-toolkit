import pdal
import json
import numpy as np
import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal, QObject

class DbWorkerSignals(QObject):
    """
    Worker'ların sinyallerini topladığımız sınıf.
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

class DbImportWorker(QThread):
    """
    Dosyayı veya mevcut katmanı veritabanına yazar (writers.pgpointcloud).
    """
    def __init__(self, source_file, conn_info, table_name, srid="4326"):
        super().__init__()
        self.source = source_file
        self.conn_info = conn_info
        self.table_name = table_name
        self.srid = srid
        self.signals = DbWorkerSignals()

    def run(self):
        try:
            self.signals.progress.emit(10)
            
            pipeline_json = [
                self.source,
                {
                    "type": "writers.pgpointcloud",
                    "connection": f"host={self.conn_info['host']} port={self.conn_info['port']} "
                                  f"dbname={self.conn_info['dbname']} user={self.conn_info['user']} "
                                  f"password={self.conn_info['password']}",
                    "table": self.table_name,
                    "srid": self.srid,
                    "overwrite": False
                }
            ]

            pipeline = pdal.Pipeline(json.dumps(pipeline_json))
            self.signals.progress.emit(30)

            count = pipeline.execute()
            
            self.signals.progress.emit(100)
            self.signals.finished.emit(f"Successfully imported {count} points into {self.table_name}.")

        except Exception as e:
            self.signals.error.emit(str(e))

class DbLoadWorker(QThread):
    """
    Veritabanından (SQL veya Tablo) okuyup, seyreltip (decimate) Canvas için veri hazırlar.
    """
    def __init__(self, conn_info, schema, table, where_clause=""):
        super().__init__()
        self.conn_info = conn_info
        self.schema = schema
        self.table = table
        self.where = where_clause
        self.signals = DbWorkerSignals()

    def run(self):
        try:
            self.signals.progress.emit(10)

            pipeline_json = [
                {
                    "type": "readers.pgpointcloud",
                    "connection": f"host={self.conn_info['host']} port={self.conn_info['port']} "
                                  f"dbname={self.conn_info['dbname']} user={self.conn_info['user']} "
                                  f"password={self.conn_info['password']}",
                    "table": self.table,
                    "schema": self.schema,
                    "where": self.where
                },
                {
                    "type": "filters.decimation",
                    "step": 10
                }
            ]
            
            pipeline = pdal.Pipeline(json.dumps(pipeline_json))
            count = pipeline.execute()
            
            if count == 0:
                raise Exception("Query returned 0 points.")

            self.signals.progress.emit(50)

            arrays = pipeline.arrays
            combined_data = np.concatenate(arrays)
            df = pd.DataFrame(combined_data)

            stats = {
                "count": int(count), 
                "schema": list(df.columns),
                "is_decimated": True
            }
            
            bounds = {
                "minx": float(df['X'].min()), "maxx": float(df['X'].max()),
                "miny": float(df['Y'].min()), "maxy": float(df['Y'].max()),
                "minz": float(df['Z'].min()), "maxz": float(df['Z'].max()) if 'Z' in df else 0
            }

            result_payload = {
                "source_type": "database",
                "conn": self.conn_info,
                "table_info": f"{self.schema}.{self.table}",
                "query_filter": self.where,
                "data": df,
                "bounds": bounds,
                "stats": stats
            }
            
            self.signals.progress.emit(100)
            self.signals.finished.emit(result_payload)

        except Exception as e:
            self.signals.error.emit(str(e))

class DbQueryWorker(QThread):
    """
    SQL Penceresindeki metin tabanlı sorgular için (Pandas DataFrame döner).
    """
    finished_success = pyqtSignal(object)
    finished_error = pyqtSignal(str)

    def __init__(self, inspector, sql):
        super().__init__()
        self.inspector = inspector
        self.sql = sql

    def run(self):
        result = self.inspector.execute_query(self.sql)
        if result["status"]:
            self.finished_success.emit(result["data"])
        else:
            self.finished_error.emit(result["error"])