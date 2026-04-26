"""
BLM-0482 | Akıllı Tarım Sistemi — Subscriber
- MQTT dinleyici
- SQLite veritabanı kaydı
- YZ destekli sulama karar alma
- Zaman serisi grafik üretimi
"""

import paho.mqtt.client as mqtt
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from datetime import datetime, timezone
import threading
import time

# ── AYARLAR ─────────────────────────────────────────────────────────────────
BROKER   = "broker.hivemq.com"
PORT     = 1883
TAKIM_NO = 1
TOPIC_TELEMETRY = f"tarim_sulama/{TAKIM_NO}/telemetry"
TOPIC_COMMAND   = f"tarim_sulama/{TAKIM_NO}/command"
MONGO_URI       = "mongodb+srv://demirbas1436:Muratmurat123.@iot.hfzt942.mongodb.net/?appName=IOT"
DB_NAME         = "akilli_tarim"

# ── BİTKİ PROFİLLERİ ─────────────────────────────────────────────────────────
BITKI_PROFILLERI = {
    "marul":    {"nem_min": 60, "nem_max": 80, "sicaklik_max": 24},
    "nane":     {"nem_min": 50, "nem_max": 70, "sicaklik_max": 28},
    "fesleğen": {"nem_min": 40, "nem_max": 65, "sicaklik_max": 32},
}

sulama_durumu = {"aktif": False, "bitki": "marul"}

# ── VERİTABANI ───────────────────────────────────────────────────────────────
import pymongo

def get_db():
    client = pymongo.MongoClient(MONGO_URI)
    return client[DB_NAME]

def db_baslat():
    print("✅ MongoDB bağlantı kontrolü yapıldı.")

def db_kaydet(veri):
    db = get_db()
    v = veri["values"]
    dokuman = {
        "sensor_id": veri["sensor_id"],
        "bitki": veri["bitki"],
        "toprak_nemi": v["toprak_nemi"],
        "sicaklik": v["sicaklik"],
        "sulama_aktif": int(v["sulama_aktif"]),
        "timestamp": veri["timestamp"]
    }
    db.telemetry.insert_one(dokuman)

def db_komut_kaydet(action, bitki, sebep):
    db = get_db()
    dokuman = {
        "action": action,
        "bitki": bitki,
        "sebep": sebep,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    db.komutlar.insert_one(dokuman)

def db_oku():
    db = get_db()
    veriler = list(db.telemetry.find({}, {
        "toprak_nemi": 1, 
        "sicaklik": 1, 
        "sulama_aktif": 1, 
        "timestamp": 1,
        "_id": 0
    }).sort("_id", pymongo.ASCENDING))
    
    rows = [(v.get("toprak_nemi"), v.get("sicaklik"), v.get("sulama_aktif"), v.get("timestamp")) for v in veriler]
    return rows

# ── YZ DESTEKLİ KARAR ALMA ──────────────────────────────────────────────────
def yz_karar_ver(client, veri):
    """
    Kural tabanlı + eşik bazlı YZ karar motoru.
    Bitkinin nem profiline göre sulama başlatır veya durdurur.
    """
    bitki_adi = veri.get("bitki", "marul")
    profil    = BITKI_PROFILLERI.get(bitki_adi, BITKI_PROFILLERI["marul"])
    nem       = veri["values"]["toprak_nemi"]
    sicaklik  = veri["values"]["sicaklik"]

    nem_min = profil["nem_min"]
    nem_max = profil["nem_max"]

    # ─── Karar Mantığı ───────────────────────────────
    # Kural 1: Nem kritik düzeyde düşükse → sulama başlat
    if nem < nem_min and not sulama_durumu["aktif"]:
        sebep = f"Toprak nemi ({nem:.1f}%) {bitki_adi} için minimumun ({nem_min}%) altında"
        komut = {
            "action": "sulama_baslat",
            "bitki":  bitki_adi,
            "sebep":  sebep,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        client.publish(TOPIC_COMMAND, json.dumps(komut, ensure_ascii=False))
        db_komut_kaydet("sulama_baslat", bitki_adi, sebep)
        sulama_durumu["aktif"] = True
        print(f"  🤖 [YZ KARAR] Sulama BAŞLATILDI → {sebep}")

    # Kural 2: Nem yeterli seviyeye ulaştıysa → sulama durdur
    elif nem >= nem_max and sulama_durumu["aktif"]:
        sebep = f"Toprak nemi ({nem:.1f}%) {bitki_adi} için maksimuma ({nem_max}%) ulaştı"
        komut = {
            "action": "sulama_durdur",
            "bitki":  bitki_adi,
            "sebep":  sebep,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        client.publish(TOPIC_COMMAND, json.dumps(komut, ensure_ascii=False))
        db_komut_kaydet("sulama_durdur", bitki_adi, sebep)
        sulama_durumu["aktif"] = False
        print(f"  🤖 [YZ KARAR] Sulama DURDURULDU → {sebep}")

    # Kural 3: Sıcaklık çok yüksekse ek sulama
    elif sicaklik > profil["sicaklik_max"] + 3 and not sulama_durumu["aktif"]:
        sebep = f"Yüksek sıcaklık ({sicaklik:.1f}°C) — serinletme sulaması"
        komut = {
            "action": "sulama_baslat",
            "bitki":  bitki_adi,
            "sebep":  sebep,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        client.publish(TOPIC_COMMAND, json.dumps(komut, ensure_ascii=False))
        db_komut_kaydet("sulama_baslat", bitki_adi, sebep)
        sulama_durumu["aktif"] = True
        print(f"  🤖 [YZ KARAR] Serinletme sulaması → {sebep}")

# ── GRAFİK ──────────────────────────────────────────────────────────────────
def grafik_ciz():
    rows = db_oku()
    if len(rows) < 2:
        print("Yeterli veri yok (en az 2 kayıt gerekli).")
        return

    nemler   = [r[0] for r in rows]
    sicaklar = [r[1] for r in rows]
    sulamalar= [r[2] for r in rows]
    zaman    = list(range(1, len(rows) + 1))

    # Bitki profilini tahmin et (son kayıttan)
    import pymongo
    db = get_db()
    son_kayit = list(db.telemetry.find({}, {"bitki": 1, "_id": 0}).sort("_id", pymongo.DESCENDING).limit(1))
    bitki_adi = son_kayit[0]["bitki"] if son_kayit else "?"
    profil = BITKI_PROFILLERI.get(bitki_adi, {})

    sensörler = [
        {
            "isim":   "Toprak Nemi (%)",
            "degerler": nemler,
            "renk":   "#4CAF50",
            "sinir_min": profil.get("nem_min"),
            "sinir_max": profil.get("nem_max"),
            "birim":  "%"
        },
        {
            "isim":   "Sıcaklık (°C)",
            "degerler": sicaklar,
            "renk":   "#FF5722",
            "sinir_min": None,
            "sinir_max": profil.get("sicaklik_max"),
            "birim":  "°C"
        },
    ]

    fig = plt.figure(figsize=(16, 12), facecolor="#F8FBF0")
    fig.suptitle(
        f"🌱 Akıllı Tarım Sistemi — Sensör Analiz Paneli\nBitki: {bitki_adi.capitalize()} | Takım {TAKIM_NO}",
        fontsize=15, fontweight="bold", color="#2E7D32", y=0.98
    )

    gs = gridspec.GridSpec(2, 2, width_ratios=[3, 1], hspace=0.55, wspace=0.25,
                           left=0.07, right=0.97, top=0.92, bottom=0.05)

    for i, s in enumerate(sensörler):
        dizi = np.array(s["degerler"])
        ax_g = fig.add_subplot(gs[i, 0])

        # Ana grafik
        ax_g.plot(zaman, dizi, color=s["renk"], linewidth=2, zorder=3, label=s["isim"])
        ax_g.fill_between(zaman, dizi, alpha=0.12, color=s["renk"])

        # İdeal aralık bandı (varsa)
        if s["sinir_min"] is not None:
            ax_g.axhline(s["sinir_min"], color="steelblue", linestyle="--", linewidth=1.2, alpha=0.7, label=f"Min ideal: {s['sinir_min']}")
        if s["sinir_max"] is not None:
            ax_g.axhline(s["sinir_max"], color="tomato",    linestyle="--", linewidth=1.2, alpha=0.7, label=f"Max ideal: {s['sinir_max']}")

        # Sulama anlarını işaretle (sadece nem grafiğinde)
        if i == 0:
            for j, (z, sul) in enumerate(zip(zaman, sulamalar)):
                if sul == 1:
                    ax_g.axvline(z, color="cornflowerblue", alpha=0.3, linewidth=1)

        ax_g.set_title(s["isim"], fontsize=11, fontweight="bold", color="#1B5E20")
        ax_g.set_xlabel("Ölçüm No", fontsize=9)
        ax_g.set_ylabel(s["birim"], fontsize=9)
        ax_g.grid(True, linestyle="--", alpha=0.4)
        ax_g.legend(fontsize=8, loc="upper right")
        ax_g.set_facecolor("#FAFFF5")

        # İstatistik kutusu
        ax_s = fig.add_subplot(gs[i, 1])
        ax_s.axis("off")

        istat = (
            f"Min      : {dizi.min():.2f} {s['birim']}\n"
            f"Max      : {dizi.max():.2f} {s['birim']}\n"
            f"Ortalama : {dizi.mean():.2f} {s['birim']}\n"
            f"Varyans  : {dizi.var():.2f}"
        )

        ax_s.text(
            0.05, 0.5, istat,
            transform=ax_s.transAxes,
            fontsize=10, verticalalignment="center",
            fontfamily="monospace",
            bbox=dict(
                boxstyle="round,pad=0.7",
                facecolor="#E8F5E9",
                edgecolor="#66BB6A",
                linewidth=1.5
            )
        )

    plt.savefig("sensor_analiz.png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print("✅ Grafik kaydedildi → sensor_analiz.png")
    plt.close()

# ── MQTT CALLBACK'LERİ ───────────────────────────────────────────────────────
mqtt_client_ref = None

def on_connect(client, userdata, flags, rc):
    global mqtt_client_ref
    mqtt_client_ref = client
    if rc == 0:
        print(f"✅ Broker'a bağlandı → Dinleniyor: {TOPIC_TELEMETRY}")
        client.subscribe(TOPIC_TELEMETRY)
    else:
        print(f"❌ Bağlantı hatası: {rc}")

def on_message(client, userdata, msg):
    try:
        veri = json.loads(msg.payload.decode())
        db_kaydet(veri)

        v = veri["values"]
        nem   = v["toprak_nemi"]
        sicak = v["sicaklik"]
        sul   = "💧" if v["sulama_aktif"] else "⏹"

        print(f"[{veri['timestamp']}] 🌿{veri['bitki']:8} | Nem:{nem:5.1f}% | Sıcak:{sicak:5.1f}°C | {sul}")

        # YZ karar motoru
        yz_karar_ver(client, veri)

    except Exception as e:
        print(f"❌ Mesaj hatası: {e}")

# ── OTOMATİK GRAFİK GÜNCELLEMESİ ────────────────────────────────────────────
def periyodik_grafik(aralik=30):
    """Her 30 saniyede bir grafik güncelle."""
    while True:
        time.sleep(aralik)
        grafik_ciz()

# ── ANA AKIŞ ────────────────────────────────────────────────────────────────
db_baslat()

# Arka planda periyodik grafik üretimi
t = threading.Thread(target=periyodik_grafik, args=(30,), daemon=True)
t.start()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT)

db_bilgi = f"MongoDB ({DB_NAME})"
print(f"""
╔══════════════════════════════════════════════╗
║   🌱 Akıllı Tarım Subscriber — Başladı       ║
║   Takım No : {TAKIM_NO}                               ║
║   Topic    : {TOPIC_TELEMETRY:<30}   ║
║   DB       : {db_bilgi:<30}   ║
║   Grafik   : Her 30 sn güncelleniyor          ║
║   Çıkış    : Ctrl+C → son grafik üretilir     ║
╚══════════════════════════════════════════════╝
""")

try:
    client.loop_forever()

except KeyboardInterrupt:
    print("\n📊 Son grafik üretiliyor...")
    client.disconnect()
    grafik_ciz()
    print("✅ Tamamlandı.")
