from core.enums import Dimensions
import numpy as np


class RenderUtils:

    # Görüntülenecek maksimum nokta sayısı (1 Milyon)
    MAX_VISIBLE_POINTS = 1_000_000

    # ASPRS Standart LAS Sınıflandırma Kodları
    LAS_LABELS = {
        0: "Created, never classified",
        1: "Unclassified",
        2: "Ground",
        3: "Low Vegetation",
        4: "Medium Vegetation",
        5: "High Vegetation",
        6: "Building",
        7: "Low Point (Noise)",
        8: "Model Key-point",
        9: "Water",
        10: "Rail",
        11: "Road Surface",
        12: "Overlap",
        13: "Wire - Guard (Shield)",
        14: "Wire - Conductor (Phase)",
        15: "Transmission Tower",
        16: "Wire-Structure Connector",
        17: "Bridge Deck",
        18: "High Noise",
    }

    @staticmethod
    def get_label(class_id):
        """Verilen sınıf ID'sine karşılık gelen metni döndürür."""
        try:
            cid = int(float(class_id))
            return RenderUtils.LAS_LABELS.get(cid, f"Class {cid}")
        except:
            return str(class_id)