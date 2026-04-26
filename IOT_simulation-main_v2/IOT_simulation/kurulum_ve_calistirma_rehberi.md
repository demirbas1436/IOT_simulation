# 🚀 Akıllı Tarım Sistemi — Yeni Bilgisayarda Kurulum ve Çalıştırma Rehberi

Bu proje, bulut üzerinde (MongoDB Atlas ve HiveMQ) entegre çalışan bir sistemdir. Kodlarınızı hocanızın veya başka bir ekibin bilgisayarında sorunsuz açabilmeniz için hiçbir adımı atlamadan aşağıdaki rehberi uygulayın.

---

## 🛠️ ADIM 1: Gerekli Programların Kurulumu

Gittiğiniz yeni bilgisayarda sadece Python yüklü olması yeterli değildir. Projemiz için gerekli olan MQTT ve Grafik çizim kütüphanelerini sisteme tanıtmamız gerekir.

1. Bilgisayarda **Python 3.x** sürümünün yüklü olduğundan emin olun. (Yüklü değilse `python.org` üzerinden indirin ve kurarken _"Add Python to PATH"_ kutucuğunu kesinlikle işaretleyin).
2. Bir **Komut İstemcisi** (Terminal / CMD / PowerShell) veya VS Code terminali açın.
3. Şu komutu tam olarak böyle yazın ve Enter'a basın:
   ```bash
   pip install paho-mqtt pymongo dnspython matplotlib
   ```
   *Not: Bu komut, internetten sistemi yönetecek 4 dev kütüphaneyi indirip kuracaktır.*

---

## 🔐 ADIM 2: MongoDB Atlas İzinlerini Açmak (Çok Önemli!)

Daha önce yaşadığımız gibi, MongoDB Atlas güvenlik nedeni ile sizin internetinize ait IP adresini tanımazsa sistemi anında bloke edecektir (SSL Handshake Hatası).

1. Kodları sunacağınız veya çalıştıracağınız internet ağına bağlı olun (Okul interneti veya telefon vb.).
2. Tarayıcıdan **MongoDB Atlas** sitesine girin ve `demirbas1436` hesabınız ile giriş yapın.
3. Sol taraftaki menüden **Network Access** (**Ağ Erişimi**) sekmesine tıklayın.
4. Sağ üstteki yeşil **Add IP Address** butonuna tıklayın.
5. Açılan pencerede **"ALLOW ACCESS FROM ANYWHERE"** (Her Yerden Erişime İzin Ver) seçeneğini işaretleyin. Böylece kural listesine `0.0.0.0/0` eklenecek ve sistem evrensel olarak IP sormadan testlere açılacaktır. (İşlemi onaylayın ve statüsünün *Active* olmasını bekleyin).

---

## 🏃 ADIM 3: Sistemi Çalıştırma (Sırasıyla)

Yeni bilgisayarda proje dosyalarınızın olduğu klasörde (`IOT_simulation`) 2 farklı terminal (siyah komut ekranı) açmanız gerekmektedir. İşlemi şu sırayla yapın:

### 1️⃣ Birinci Ekran: Sunucuyu (Dinleyiciyi) Ayağa Kaldırmak
İlk açtığınız komut satırına klasör içindeyken şunu yazın:

```bash
python subscriber.py
```
* **Ekranda Beklenen Çıktı:** Yeşil tiklerle `✅ Broker'a bağlandı` ve `✅ MongoDB bağlantı kontrolü yapıldı` yazılarını gördüyseniz sistem başarıyla dış dünyayı dinlemeye başlamıştır. Bu pencereyi bir kenarda **açık bırakın.**

### 2️⃣ İkinci Ekran: Sensörü (Yayıncıyı) Başlatmak
İkinci komut satırına klasör içindeyken şunu yazın:

```bash
python publisher.py
```
* **Ekranda Beklenen Çıktı:** Sensör anında uyanacak, nem ölçümlerine başlayacak ve her 3 saniyede bir ekranınızdan `💧 AÇIK` veya `⏹ KAPALI` şeklinde gerçek zamanlı verileri basmaya başlayacaktır.

---

## 🎨 ADIM 4: İzleme ve Grafikler Görüntüleme

Sistem çalışırken arka planda gerçekleşen işlemleri şöyle izleyebilirsiniz:

1. **Görsel Web Arayüzü:** Proje klasöründeki **`dashboard.html`** dosyasına iki kere tıklayıp tarayıcınızda açın. Sistemin YZ karar alma mantığını ve bitki seçimlerinin nasıl davrandığını buradan simüle edebilirsiniz.
2. **Gerçek Zamanlı Çizilen Grafikler:** Arka planda çalışan `subscriber.py` düzenli olarak 30 saniyede bir MongoDB'den istatistik çekip o proje klasörüne `sensor_analiz.png` isminde harika bir veri grafiği bırakır. Klasörünüzdeki bu resme tıklayarak istatistikleri sunabilirsiniz (Resim düzenli değiştiği için üzerine tıklayıp yeni veriyi görebilirsiniz).
3. **Bulut Veri (MongoDB) Kontrolü:** MongoDB Ara yüzünden *Browse Collections* diyerek tarlada kaydedilen ham JSON verilerinin nasıl alt alta dizildiğini projeyi anlattığınız kişiye kanıt olarak gösterebilirsiniz.

Hepsi bu kadar, başarınızın tadını çıkarın! 🌟
