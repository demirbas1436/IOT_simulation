# 📖 Akıllı Tarım Sistemi — Kod Açıklama Rehberi

Bu belge, Akıllı Tarım Sistemi IoT simülasyonunun arkasındaki yazılım mimarisini, dosyaların görevlerini ve sistemin birbiriyle nasıl konuştuğunu adım adım açıklamaktadır.

## 🏗️ 1. Genel Mimari ve Protokoller
Sistemimiz temelde 3 ana parçadan (Publisher, Subscriber, Dashboard) oluşur ve iki farklı güçlü teknoloji ile haberleşir:
* **MQTT Protokolü:** Cihazlar arası anlık, çok hızlı ve düşük veri tüketimli IoT mesajlaşmasını sağlar. Public bulut sunucusu olan `broker.hivemq.com` üzerinden gerçekleşir.
* **MongoDB (NoSQL Veritabanı):** Sensörlerden gelen JSON tabanlı verileri düzenli ve esnek bir hiyerarşide bulutta saklar.

---

## 📡 2. publisher.py (Tarla Sensörleri / Simülatör)
Bu dosya fiziksel bir donanımı (örneğin bir ESP32 veya Arduino) taklit eder. Tarlada toprağın içine saplanmış bir HW-390 nem sensörü gibi davranır.

* **Toprak Nemi ve Sıcaklık Simülasyonu:** Kod bloğundaki `SimulasyonDurumu` sınıfı, "Buharlaşma" ile toprağın kendi kendine kuruduğu, "Sulama" durumunda ise nemin yapay olarak düzenli arttığı bir matematiksel modelleme yapar.
* **MQTT Topic Standartı:** 
  Veriler PDF belgelerindeki standart olan `tarim_sulama/>takim_no</telemetry` kanalına düzenli olarak 3 saniyede bir `JSON` dizisi olarak fırlatılır (Publish edilir).
* **Komut Dinleme (Command):** Cihaz aynı zamanda dışarıdan gelecek sulama aç/kapat komutlarını alabilmek için `tarim_sulama/>takim_no</command` kanalını "dinler" (Subscribe olur). Gelen mesaja göre vanayı (simülasyonu) açar veya bitkiyi değiştirir.

---

## 🧠 3. subscriber.py (Ana Sunucu / YZ Motoru)
Bu dosya sistemin "Beynidir". İnternetten devamlı MQTT kanalını dinler, veriyi okur, analiz eder ve bir karar verir.

* **Bulut MQTT Dinleme:** `paho-mqtt` kütüphanesini `VERSION1` kalitesiyle çağırıp, HiveMQ sunucusundaki `tarim_sulama/1/telemetry` kanalına abone olur. Publisher veri attığı an devreye girer.
* **Yapay Zeka (Kural Tabanlı) Karar Motoru:** Dosya içerisindeki `yz_karar_ver()` fonksiyonu, o anki seçili olan bitki türüne göre karar alır. 
    > Örneğin; "Eğer nem %60'ın altındaysa ve bitki Marul ise hemen sulama başlat komutu gönder!" der. Bu noktada kendisi bir komut paketini MQTT üzerinden `command` kanalına fırlatır.
* **MongoDB Veritabanı Kaydı (`pymongo`):**
  - Gelen ham veri, NoSQL standartlarına göre bir Dictionary içerisine ayrılır.
  - `db.telemetry.insert_one(dokuman)` fonksiyonu ile saniyesinde **MongoDB Atlas** bulut veritabanına kalıcı olarak yazılır.
* **Matplotlib ile Grafik Üretimi:** 
  Arka planda (Thread kullanılarak) her 30 saniyede bir veritabanından en güncel verileri (`db.telemetry.find()`) çeker, analiz eder ve bir tablo (`sensor_analiz.png`) üretir.

---

## 🖥️ 4. dashboard.html (Arayüz Paneli)
Sistemin görsel şölenidir. Saf HTML, CSS ve interaktif kısımlar için JavaScript (Vanilla) + Chart.js araçları ile kodlanmıştır.

* Herhangi bir kurulum gerektirmez, doğrudan çift tıklanarak tarayıcıda açılır.
* `bitciSec()` ve `sulamaToggle()` fonksiyonları JavaScript tabanlı YZ kararlarını yerel cihazda görsel simüle eder.
* Sensör analizleri bir zaman tüneli olan `Chart.js` grafiklerinde, tıpkı `matplotlib` gibi ancak hareketli çizilir ve renk değiştirerek uyarı verir.
