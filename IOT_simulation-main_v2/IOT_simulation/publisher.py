"""
BLM-0482 | Akıllı Tarım Sistemi — Publisher (Simülatör)
Topic: tarim_sulama/{takim_no}/telemetry
"""

import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime, timezone

BROKER   = "broker.hivemq.com"
PORT     = 1883
TAKIM_NO = 1           # ← Kendi takım numaranı buraya yaz (1, 2 veya 3)
PERIYOT  = 3           # saniye

TOPIC_TELEMETRY = f"tarim_sulama/{TAKIM_NO}/telemetry"
TOPIC_COMMAND   = f"tarim_sulama/{TAKIM_NO}/command"

# ── BİTKİ PROFİLLERİ ────────────────────────────────────────────────────────
# Her bitkinin ideal toprak nemi aralığı (%)
BITKI_PROFILLERI = {
    "marul": {
        "nem_min": 60, "nem_max": 80,
        "sicaklik_ideal": (15, 22),
        "sulama_suresi": 8   # saniye (simülasyon)
    },
    "nane": {
        "nem_min": 50, "nem_max": 70,
        "sicaklik_ideal": (18, 26),
        "sulama_suresi": 6
    },
    "fesleğen": {
        "nem_min": 40, "nem_max": 65,
        "sicaklik_ideal": (20, 30),
        "sulama_suresi": 5
    }
}

# Aktif bitki seçimi
AKTIF_BITKI = "nane"   # ← "marul" | "nane" | "fesleğen"

# ── SİMÜLASYON DURUMU ───────────────────────────────────────────────────────
class SimulasyonDurumu:
    def __init__(self, bitki_adi):
        self.bitki     = BITKI_PROFILLERI[bitki_adi]
        self.bitki_adi = bitki_adi
        # Başlangıç toprak nemi biraz düşük başlıyor (sulama tetiklensin)
        self.toprak_nemi = random.uniform(35, 50)
        self.sulama_aktif = False

    def guncelle(self):
        """Gerçekçi nem simülasyonu: buharlaşma + yağış/sulama etkisi."""
        if self.sulama_aktif:
            # Sulama açıkken nem artar
            self.toprak_nemi += random.uniform(3, 7)
        else:
            # Buharlaşma ile nem düşer
            self.toprak_nemi -= random.uniform(0.5, 2.5)

        # Sınır kontrolü
        self.toprak_nemi = max(10, min(100, self.toprak_nemi))

    def veri_uret(self):
        self.guncelle()
        profil = self.bitki

        return {
            "sensor_id": f"tarim_sulama_{TAKIM_NO}",
            "bitki": self.bitki_adi,
            "values": {
                "toprak_nemi": round(self.toprak_nemi, 2),
                "sicaklik":    round(random.uniform(*profil["sicaklik_ideal"]) + random.gauss(0, 1.5), 2),
                "sulama_aktif": self.sulama_aktif
            },
            "unit": "metric",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }

sim = SimulasyonDurumu(AKTIF_BITKI)

# ── MQTT CALLBACK ────────────────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Broker'a bağlandı.")
        # Command topic'ini dinle (Subscriber'dan gelen komutlar)
        client.subscribe(TOPIC_COMMAND)
        print(f"📡 Command topic dinleniyor: {TOPIC_COMMAND}")
    else:
        print(f"❌ Bağlantı hatası: {rc}")

def on_message(client, userdata, msg):
    """Subscriber'dan gelen sulama komutlarını işle."""
    global sim
    try:
        komut = json.loads(msg.payload.decode())
        eylem = komut.get("action")

        if eylem == "sulama_baslat":
            sim.sulama_aktif = True
            print(f"💧 [KOMUT ALINDI] Sulama BAŞLATILDI | Bitki: {komut.get('bitki')}")

        elif eylem == "sulama_durdur":
            sim.sulama_aktif = False
            print(f"⏹️  [KOMUT ALINDI] Sulama DURDURULDU")

        elif eylem == "bitki_degistir":
            yeni_bitki = komut.get("bitki")
            if yeni_bitki in BITKI_PROFILLERI:
                sim = SimulasyonDurumu(yeni_bitki)
                print(f"🌿 [KOMUT ALINDI] Bitki değiştirildi → {yeni_bitki}")

    except Exception as e:
        print(f"❌ Komut işleme hatası: {e}")

# ── ANA AKIŞ ────────────────────────────────────────────────────────────────
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT)
client.loop_start()

print(f"""
╔══════════════════════════════════════════════╗
║   🌱 Akıllı Tarım Publisher — Başladı        ║
║   Takım No : {TAKIM_NO}                               ║
║   Bitki    : {AKTIF_BITKI:<30}   ║
║   Topic    : {TOPIC_TELEMETRY:<30}   ║
║   Periyot  : {PERIYOT} saniye                          ║
╚══════════════════════════════════════════════╝
""")

try:
    while True:
        veri = sim.veri_uret()
        mesaj = json.dumps(veri, ensure_ascii=False)
        client.publish(TOPIC_TELEMETRY, mesaj)

        nem    = veri["values"]["toprak_nemi"]
        sicak  = veri["values"]["sicaklik"]
        sulama = "💧 AÇIK" if veri["values"]["sulama_aktif"] else "⏹  KAPALI"

        print(f"[{veri['timestamp']}] 🌱{veri['bitki']:8} | Nem:{nem:5.1f}% | Sıcaklık:{sicak:5.1f}°C | Sulama:{sulama}")
        time.sleep(PERIYOT)

except KeyboardInterrupt:
    print("\nPublisher durduruldu.")
    client.loop_stop()
    client.disconnect()
