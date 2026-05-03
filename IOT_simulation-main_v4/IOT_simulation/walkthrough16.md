# Akıllı Tarım IoT Sistemi — Teknik İnceleme ve Çalışma Mantığı

Bu döküman, projenin teknik mimarisini, kullanılan algoritmaları ve veri akış şemasını detaylandırmak amacıyla hazırlanmıştır.

---

## 1. Sistemin Genel Mimarisi
Proje, klasik bir IoT ekosistemini simüle eden dört ana katmandan oluşur:

1.  **Sensör Katmanı (Publisher):** Veriyi üreten kaynak.
2.  **İletişim Katmanı (MQTT Broker):** Veriyi dağıtan merkez.
3.  **İşleme Katmanı (Subscriber):** Veriyi kaydeden ve analiz eden beyin.
4.  **Sunum Katmanı (Dashboard):** Veriyi kullanıcıya görselleştiren arayüz.

---

## 2. Simülasyon Algoritmaları (İş Mantığı)
Sistemin en kritik parçası, `publisher.py` içerisinde yer alan ve bitki fiziğini taklit eden simülasyon algoritmasıdır.

### A. Doğal Nem Kaybı (Buharlaşma) Algoritması
Bitki sulanmadığında nem oranı doğrusal olmayan bir şekilde azalır.
- **Mantık:** Her 3 saniyede bir, mevcut nem oranından rastgele **%0.5 ile %2.0** arasında bir değer çıkarılır.
- **Formül:** $Nem_{yeni} = Nem_{eski} - Random(0.5, 2.0)$
- **Simülasyon Değeri:** Bu düşüş hızı, toprağın kuruma sürecini gerçekçi bir şekilde modellemek için seçilmiştir.

### B. Sulama ve Nem Artış Algoritması
Sulama sistemi aktif hale geldiğinde (manuel veya otomatik), nem oranı hızla yükselir.
- **Mantık:** Sulama açık olduğu sürece her 3 saniyede nem oranına **%5.0 ile %10.0** arasında bir değer eklenir.
- **Üst Sınır:** Fiziksel gerçeklik gereği nem oranı asla **%100** değerini geçemez (Doygunluk noktası).
- **Formül:** $Nem_{yeni} = Min(100, Nem_{eski} + Random(5, 10))$

### C. Sıcaklık Salınımı
- **Mantık:** Sıcaklık değerleri her periyotta **±0.5°C** bandında küçük salınımlar yapar.
- **Sınır:** Sistem, sıcaklığın ekstrem değerlere çıkmasını önlemek için **15°C - 35°C** aralığında kalmasını sağlar.

---

## 3. Karar Destek Algoritması (Akıllı Karar)
`subscriber.py` içerisinde çalışan bu algoritma, bitkinin sağlığını korumak için "karar" verir. Örneğin **Nane** bitkisi için:
- **Kritik Eşik (Alt):** Eğer nem **%50**'nin altına düşerse, sistem **"SULAMA GEREKLİ"** komutunu üretir.
- **Kritik Eşik (Üst):** Eğer nem **%70**'e ulaşırsa, bitkinin çürümesini önlemek için **"SULAMAYI DURDUR"** komutunu verir.

---

## 4. Veri Akışı ve Teknoloji Yığını
Veri, üretimden sunuma kadar şu aşamalardan geçer:

1.  **JSON Paketleme:** Veriler her zaman yapılandırılmış JSON formatında taşınır.
2.  **MQTT İletimi:** Broker (Mosquitto) üzerinden hafif ve hızlı bir mesajlaşma sağlanır.
3.  **MongoDB Kalıcılığı:** Subscriber, gelen her veriyi NoSQL tabanlı MongoDB'ye kaydederek geriye dönük veri kaybını önler.
4.  **WebSocket Haberleşmesi:** Web paneli (Dashboard), Mosquitto'ya WebSocket üzerinden bağlanarak sayfayı yenilemeye gerek kalmadan "Push" yöntemiyle anlık grafik çizer.

---

## 5. Özet: Birine Nasıl Anlatırsın?
> "Bu sistem, bitkinin nem ihtiyacını takip eden bir yapay zeka öncüsüdür. Python ile yazdığım algoritma toprağın kurumasını simüle ederken, MQTT protokolü bu verileri anlık olarak merkeze taşır. Veritabanı katmanı tüm geçmişi kaydederken, kullanıcı web paneli üzerinden dünyanın her yerinden tarlasını canlı izleyebilir ve müdahale edebilir."
