from PyQt5.QtCore import QThread, pyqtSignal, QObject
from sqlalchemy import text, create_engine
from core.render_utils import RenderUtils
import pandas as pd
import numpy as np
import pdal
import json
import math

class DbWorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)


class DbImportWorker(QThread):

    def __init__(
        self,
        source_data,
        conn_info,
        schema,
        table,
        source_name,
        is_array=False,
        srid=None,
    ):
        super().__init__()
        self.source_data, self.conn_info, self.schema, self.table = (
            source_data,
            conn_info,
            schema,
            table,
        )
        self.source_name, self.is_array, self.srid = source_name, is_array, srid
        self.signals = DbWorkerSignals()

    def run(self):
        try:
            self.signals.progress.emit(-1)
            target_srid = str(self.srid) if self.srid else "4326"
            writer_config = {
                "type": "writers.pgpointcloud",
                "connection": f"host={self.conn_info['host']} port={self.conn_info['port']} dbname={self.conn_info['dbname']} user={self.conn_info['user']} password={self.conn_info['password']}",
                "table": self.table,
                "schema": self.schema,
                "column": "patch",
                "srid": target_srid,
                "compression": "dimensional",
                "overwrite": False,
            }
            chipper = {"type": "filters.chipper", "capacity": 1000}

            if self.is_array:
                pipeline_stages = [chipper, writer_config]
                pipeline = pdal.Pipeline(
                    json.dumps(pipeline_stages), [self.source_data]
                )
            else:
                reader_config = {"type": "readers.las", "filename": self.source_data}
                pipeline_stages = [reader_config, chipper, writer_config]
                pipeline = pdal.Pipeline(json.dumps(pipeline_stages))

            count = pipeline.execute()

            url = f"postgresql://{self.conn_info['user']}:{self.conn_info['password']}@{self.conn_info['host']}:{self.conn_info['port']}/{self.conn_info['dbname']}"
            engine = create_engine(url)
            with engine.connect() as conn:
                conn.execute(
                    text(
                        f'UPDATE "{self.schema}"."{self.table}" SET source = :s WHERE source IS NULL'
                    ),
                    {"s": self.source_name},
                )

                res = conn.execute(
                    text(
                        f'SELECT pcid FROM "{self.schema}"."{self.table}" WHERE pcid IS NOT NULL LIMIT 1'
                    )
                ).fetchone()
                if res:
                    actual_pcid = res[0]
                    conn.execute(
                        text(
                            f'ALTER TABLE "{self.schema}"."{self.table}" ALTER COLUMN patch TYPE public.pcpatch({actual_pcid})'
                        )
                    )
                conn.commit()

            self.signals.progress.emit(100)
            self.signals.finished.emit(
                f"Successfully saved {count} points to database. (SRID: {target_srid})"
            )

        except Exception as e:
            self.signals.error.emit(f"Database write error : {str(e)}")


class DbLoadWorker(QThread):

    def __init__(self, conn_info, schema, table, where_clause=""):
        super().__init__()
        self.conn_info, self.schema, self.table, self.where = (
            conn_info,
            schema,
            table,
            where_clause,
        )
        self.signals = DbWorkerSignals()

    def run(self):
        try:
            self.signals.progress.emit(-1)
            total_points = self._get_total_count()
            step = 1

            if total_points > RenderUtils.MAX_VISIBLE_POINTS:
                step = math.ceil(total_points / RenderUtils.MAX_VISIBLE_POINTS)

            reader_config = {
                "type": "readers.pgpointcloud",
                "schema": self.schema,
                "table": self.table,
                "column": "patch",
                "where": self.where,
                "connection": f"host={self.conn_info['host']} port={self.conn_info['port']} dbname={self.conn_info['dbname']} user={self.conn_info['user']} password={self.conn_info['password']}",
            }

            stages = [reader_config]

            if step > 1:
                stages.append({"type": "filters.decimation", "step": step})

            pipeline = pdal.Pipeline(json.dumps(stages))
            pipeline.execute()

            if not pipeline.arrays:
                raise Exception("No points found for the given query.")

            arrays = pipeline.arrays[0]
            data_dict = {}
            for name in arrays.dtype.names:
                data_dict[name] = arrays[name]

            data_dict["count"] = len(arrays)

            bounds = {
                "minx": float(np.min(data_dict["X"])),
                "maxx": float(np.max(data_dict["X"])),
                "miny": float(np.min(data_dict["Y"])),
                "maxy": float(np.max(data_dict["Y"])),
            }

            self.signals.progress.emit(100)
            self.signals.finished.emit(
                {
                    "data": data_dict,
                    "metadata": pipeline.metadata,
                    "conn": self.conn_info,
                    "bounds": bounds,
                    "table_info": f"{self.schema}.{self.table}",
                    "query_filter": self.where,
                }
            )
        except Exception as e:
            self.signals.progress.emit(0)
            self.signals.error.emit(str(e))

    def _get_total_count(self) -> int:
        try:
            url = f"postgresql://{self.conn_info['user']}:{self.conn_info['password']}@{self.conn_info['host']}:{self.conn_info['port']}/{self.conn_info['dbname']}"
            engine = create_engine(url)
            where_sql = f"WHERE {self.where}" if self.where else ""
            query = text(f'SELECT Sum(PC_NumPoints(patch)) FROM "{self.schema}"."{self.table}" {where_sql}')

            with engine.connect() as conn:
                result = conn.execute(query).scalar()
                return int(result) if result else 0
            
        except Exception as e:
            print(f"DB Count Error: {e}")
            return 0

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
            if res["status"]:
                self.finished_success.emit(res["data"])
            else:
                self.finished_error.emit(res["error"])
        finally:
            self.finished.emit()