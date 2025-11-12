# TASARIM

## Katmanlı Mimari

Uygulamamızı 3 ana katmana ayırarak Tek Sorumluluk Prensibi (SRP)'ni uygulayacağız:

* Sunum Katmanı (Presentation Layer): PyQt5 ile kullanıcı arayüzü (UI) ve kullanıcı etkileşimlerini yönetir. (Gereksinimler: UI-01'den UI-11'e kadar her şey).

* İş Mantığı Katmanı (Business Logic Layer / Core): Uygulamanın temel görevlerini (örneğin: Pipeline oluşturma, loglama, tema yönetimi) içerir.

* Veri Erişim Katmanı (Data Access Layer): PDAL kütüphanesi ile doğrudan etkileşimi yönetir, veri okuma ve işleme işlemlerini yapar. (Gereksinimler: DS-01, DS-03, DS-04).

## Genişletilebilirlik

Veri kaynaklarının genişletilebilir olması için Açık/Kapalı Prensibi (OCP) ve Bağımlılık Tersine Çevirme Prensibi (DIP) hayati önem taşır:

* OCP (Open/Closed Principle): Uygulamamız yeni veri formatlarına (.las, .laz dışında .ply, .e57 vb.) açık olmalı, ancak mevcut kodda büyük değişiklikler yapmaya kapalı olmalıdır. Bunu Soyutlamalar (Abstraction) kullanarak başaracağız.

* DIP (Dependency Inversion Principle): Üst seviye modüller (örneğin ana uygulama mantığı) alt seviye modüllere (örneğin LasFileHandler sınıfına) doğrudan bağımlı olmak yerine, aradaki bir arayüze (Interface/Abstract Class) bağımlı olmalıdır.

# GEREKSİNİMLER

## Uygulama Arayüzü

* UI-01: Uygulama arayüzünde menu bar olmalı. Menü bar seçenekleri şunlar olmalı “File”, “View”, “Themes”, “Help”.

* UI-02: File menüsü altında “Open File”, “Save Pipeline”, “Save as” seçenekleri olmalı.

* UI-03: View menüsü altında uygulamada yer alan dock widgetlar yer almalı. Bu dock widgetların ekranda görüntülenip görüntülenmemesi durumu burdan yönetilebilmeli. Default’a dönüş mümkün olmalı.

* UI-04: Themes menüsü altında uygulamada yer alan temalar görüntülenebilmeli ve kullanıcı varsayılan temasını değiştirebilmeli.

* UI-05: Help menüsü altında basit bir dialog penceresi ile uygulama bilgileri yer almalıdır.
 
* UI-06: Uygulama bir toolbar’a sahip olmalı. Bu toolbarda dosya ekleme, pipeline çalıştırma, mevcut çalışmayı kaydetme gibi özellikler olmalı.

* UI-07: Uygulama ana ekranın sol kısmında data sources ve metadata olmak üzere 2 adet dock widget olmalı.

* UI-08: Uygulama ana ekranı sağ tarafında Filters dock paneli olmalı.

* UI-09: Uygulama ana ekranı altında log paneli olmalı.Yapılan her işlem log panelinde yer almalı.

* UI-10: Uygulama ana ekranı ortasında 2 tab ekranından oluşan bir tab widget olmalı. bu tab widget’ı 1. tab’i bir leaflet haritası, 2. tab’i ise bir 3d görüntüleme ekranına sahip olmalıdır.

* UI-11: Uygulamaya eklenen nokta bulutu verisinin bboxu leaflet haritasına çizilmelidir.

## Veri Okuma

* DR-01: .laz/.las dosyaları veri kaynağı olarak kullanılabilmelidir.

* DR-02: Veri kaynakları daha sonradan genişletilebilir olmalıdır.

* DR-03: Okunan veriler basitleştirilmiş şekilde uygulamada render edilmelidir.

* DR-04: Hangi verinin render edildiği/okunduğu uygulamanın sol tarafında bulunan bir ağaç yapısı ile kaynak/veri hiyerarşisinde gösterilmelidir.

