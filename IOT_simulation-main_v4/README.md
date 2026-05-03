# IOT_simulation

PS > & "C:\Program Files\mosquitto\mosquitto.exe" -c "c:\Users\HP\Desktop\sil16\nesnelerin_interneti\IOT_simulation-main\IOT_simulation-main_v2\IOT_simulation\yerel_mosquitto.conf" -v



        [Sensör Simülasyonu] 
               |
               v
        Toprak Nemi & Sıcaklık
               |
               v
        [Publisher (MQTT)]
               |
               |  → Telemetry Topic: tarim_sulama/{takim_no}/telemetry
               |
               v
        [Subscriber (MQTT)]
               |
        ┌───────────────┬───────────────┐
        |               |               |
        v               v               v
 [Veritabanı Kaydı]   [YZ Karar Motoru]   [Grafik Üretimi]
   (MongoDB)          (Nem & Sıcaklık)    (Matplotlib)
        |                   |                   |
        |                   |                   |
        |                   v                   |
        |         Komut Üretimi (sulama aç/kapat)
        |                   |
        |                   v
        |        → Command Topic: tarim_sulama/{takim_no}/command
        |                   |
        └───────────────────┘
               |
               v
        [Publisher Sulama Durumu Günceller]
