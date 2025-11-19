# core/filter_worker.py

from PyQt5.QtCore import QObject, pyqtSignal
import pdal
import json
import traceback
from core.layer_context import PipelineStage 

class FilterWorker(QObject):
    # (Dosya Yolu, Sonuç Verisi, Stage Nesnesi)
    finished = pyqtSignal(str, dict, object) 
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, file_path: str, pipeline_config: list, stage: object):
        super().__init__()
        self.file_path = file_path
        self.pipeline_config = pipeline_config
        self.stage = stage

    def run(self):
        try:
            print("DEBUG: Worker başladı.") # Konsola yazdırarak takip edelim
            self.progress.emit(10)
            
            # JSON debug
            json_str = json.dumps(self.pipeline_config, indent=2)
            print(f"DEBUG: Pipeline JSON:\n{json_str}")

            pipeline = pdal.Pipeline(json_str)
            
            print("DEBUG: Pipeline execute ediliyor (Bu işlem sürebilir)...")
            count = pipeline.execute()
            print(f"DEBUG: Execute bitti. Count: {count}")
            
            self.progress.emit(80)
            
            arrays = pipeline.arrays[0]
            
            result_data = {
                "x": arrays["X"].tolist(),
                "y": arrays["Y"].tolist(),
                "z": arrays["Z"].tolist(),
                "count": count
            }
            
            print("DEBUG: Veri hazırlandı, sinyal gönderiliyor...")
            self.progress.emit(100)
            
            # BURAYA DİKKAT: 3 argüman gönderiyoruz.
            self.finished.emit(self.file_path, result_data, self.stage)
            print("DEBUG: Sinyal gönderildi.")

        except Exception as e:
            error_details = f"Worker Hatası: {str(e)}\n{traceback.format_exc()}"
            print(f"DEBUG ERROR: {error_details}") # Konsolda hatayı gör
            self.error.emit(error_details)