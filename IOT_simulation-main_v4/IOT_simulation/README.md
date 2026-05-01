# BLM-0482 — Akıllı Tarım Sistemi (Topraklı Tarımda Sulama)

## Proje Yapısı

```
iot_tarim/
├── publisher.py      ← Sensör veri simülatörü (MQTT yayıncı)
├── subscriber.py     ← Veri dinleyici + SQLite + YZ + Grafik
├── dashboard.html    ← Tarayıcı tabanlı yönetim arayüzü
└── telemetry.db      ← Otomatik oluşur (SQLite)
```

## MQTT Topic Standardı

| Bileşen    | Değer                              |
|------------|------------------------------------|
| problem_id | `tarim_sulama`                     |
| takim_no   | `1` (değiştirilebilir)             |
| mesaj_tipi | `telemetry` / `command`            |
| **Topic**  | `tarim_sulama/1/telemetry`         |
|            | `tarim_sulama/1/command`           |

## Kurulum

### 1. Python Kütüphaneleri

```bash
pip install paho-mqtt matplotlib numpy
```

### 2. Mosquitto (Yerel MQTT Broker)

**Windows:**
- https://mosquitto.org/download/ → indir ve kur
- Sonra: `net start mosquitto`

**Linux:**
```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
```

**macOS:**
```bash
brew install mosquitto && brew services start mosquitto
```

## Çalıştırma Sırası

```
Terminal 1 (Broker zaten serviste çalışıyor)

Terminal 2:
    python subscriber.py

Terminal 3:
    python publisher.py
```

## Bitki Profilleri

| Bitki     | Nem Min | Nem Max | Sıcaklık İdeal | Sulama Süresi |
|-----------|---------|---------|----------------|---------------|
| Marul     | %60     | %80     | 15–22°C        | ~8 sn         |
| Nane      | %50     | %70     | 18–26°C        | ~6 sn         |
| Fesleğen  | %40     | %65     | 20–30°C        | ~5 sn         |

## JSON Format (telemetry)

```json
{
  "sensor_id": "tarim_sulama_1",
  "bitki": "marul",
  "values": {
    "toprak_nemi": 62.4,
    "sicaklik": 19.3,
    "sulama_aktif": false
  },
  "unit": "metric",
  "timestamp": "2026-04-07T10:00:00Z"
}
```

## JSON Format (command)

```json
{
  "action": "sulama_baslat",
  "bitki": "marul",
  "sebep": "Toprak nemi 58.2% minimumun altında",
  "timestamp": "2026-04-07T10:00:00Z"
}
```

## YZ Karar Motoru (Kural Tabanlı)

| Kural | Koşul | Eylem |
|-------|-------|-------|
| 1 | Nem < nem_min | sulama_baslat |
| 2 | Nem ≥ nem_max | sulama_durdur |
| 3 | Sıcaklık > sicaklik_max + 3°C | sulama_baslat (serinletme) |

## Grafik Çıktısı

`subscriber.py` Ctrl+C ile durdurulduğunda → `sensor_analiz.png` oluşur.  
Her 30 saniyede bir otomatik güncellenir.

## Dashboard

`dashboard.html` dosyasını doğrudan tarayıcıda açın.  
Canlı simülasyon, YZ kararları ve istatistikler görüntülenir.
