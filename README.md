# 🚀 PDAL Desktop Toolkit

**PDAL Desktop Toolkit**, nokta bulutu verilerini (LAS/LAZ) hızlı bir şekilde okumak, görselleştirmek (2D Harita ve 3D Nokta Bulutu) ve PDAL filtrelerini kullanarak işlemek için tasarlanmış modern bir masaüstü uygulamasıdır. PyQt5, PyVista ve PDAL gibi güçlü coğrafi bilgi sistemleri (CBS) kütüphaneleri üzerine inşa edilmiştir.

---

## ✨ Temel Özellikler

* **Çoklu Görünüm Desteği :**
    * **2D Harita Görünümü (Leaflet) :** Veri sınırlarını (BBOX) WGS84 (EPSG:4326) koordinatlarında görüntüler.
    * **3D Nokta Bulutu Görünümü (PyVista) :** Yüksek performanslı 3D görselleştirme sunar.

* **Meta Veri :** Okunan verinin nokta sayısı, koordinat sistemi, kaydedilen yazılım gibi bilgileri metaverisinden çekere görüntüleme imkanı sunar.

* **Katman Paneli :** Uygulama çalışır durumdayken katman paneli yardımıyla birden fazla veri eklenebilmekte ve bilgilere ayrı ayrı ulaşılabilmektedir.

* **Log Paneli :** Uygulama yaptığı işleri ve aldığı hataları log panelinde raporlamaktadır.

---

## 🖥️ Kullanım

1.  Uygulama açıldıktan sonra üst araç çubuğundaki **"Open File"** butonuna (veya `Ctrl+O`) tıklayın.
2.  Bilgisayarınızdan bir `.las` veya `.laz` dosyası seçin.
3.  Dosya, sol paneldeki **Data Sources** altına eklendikten sonra:
    * Dosyaya **Tek Tıkladığınızda**, sol alt paneldeki **Metadata** (özet meta veriler) otomatik olarak güncellenir.
    * Dosyaya **Çift Tıkladığınızda**, **Map View** (Veri sınırları çizilir) ve **3D View** (Nokta bulutunun örneklenmiş kısmı görüntülenir) sekmeleri güncellenir.

---


## 🤝 Katkıda Bulunma

Geliştirme sürecine katkıda bulunmak isterseniz, lütfen **Clean Code** ve **Sürdürülebilirlik** ilkelerine dikkat ederek bir **Pull Request** açın.

---

## 📧 İletişim

* **Geliştirici:** Muzaffer Bulut
* **İletişim:** bulutmuzafferr@gmail.com
* **Versiyon:** 0.7.0 (Geliştirme Aşamasında)