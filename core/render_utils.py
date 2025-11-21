import numpy as np

class RenderUtils:
    
    # Görüntülenecek maksimum nokta sayısı (1 Milyon)
    MAX_VISIBLE_POINTS = 1_000_000 

    @staticmethod
    def downsample(data_dict: dict):
        """
        Sözlük içindeki tüm numpy dizilerini (x, y, z, intensity...) 
        aynı oranda seyreltir.
        
        Parametre:
            data_dict (dict): {'x': np.array, 'y': np.array, ...} içeren sözlük.
        """
        
        # Referans olarak X'i alalım, yoksa işlem yapamayız
        if "x" not in data_dict:
            return data_dict

        # X verisini al (Numpy array olduğunu varsayıyoruz)
        x_data = data_dict["x"]
        total_points = len(x_data)

        # Eğer nokta sayısı limitin altındaysa hiçbir şeye dokunmadan geri dön
        if total_points <= RenderUtils.MAX_VISIBLE_POINTS:
            return data_dict
        
        # Adım sayısını hesapla (Örn: 10M nokta varsa ve limit 1M ise, step=10)
        step = total_points // RenderUtils.MAX_VISIBLE_POINTS
        
        # Eğer step 1 veya daha küçükse bölmeye gerek yok
        if step <= 1:
            return data_dict

        # Yeni bir sözlük oluşturup verileri keserek (slice) içine atacağız
        result_dict = {}
        
        for key, value in data_dict.items():
            # Sadece Numpy array olanları ve boyutu X ile aynı olanları kesiyoruz.
            # 'count' gibi tekil sayıları veya 'status' gibi stringleri ellememeliyiz.
            if isinstance(value, np.ndarray) and len(value) == total_points:
                result_dict[key] = value[::step]
            else:
                # Array değilse (örn: count sayısı) olduğu gibi kopyala
                result_dict[key] = value
        
        return result_dict