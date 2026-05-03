# IOT_simulation

PS > & "C:\Program Files\mosquitto\mosquitto.exe" -c "c:\Users\HP\Desktop\sil16\nesnelerin_interneti\IOT_simulation-main\IOT_simulation-main_v2\IOT_simulation\yerel_mosquitto.conf" -v


```mermaid
graph TD
    subgraph "Uç Cihaz Katmanı (Edge Layer)"
        S1[Sensör Simülasyonu] -->|Veri Üretimi| S2[Toprak Nemi & Sıcaklık]
        S2 -->|JSON Payload| P1[Publisher - MQTT]
    end

    subgraph "Haberleşme Katmanı (Broker)"
        P1 -->|Telemetry Topic| B[MQTT Broker]
        B -->|Command Topic| P2[Sulama Ünitesi/Aktüatör]
    end

    subgraph "Merkezi İşleme Katmanı (Backend & AI)"
        B -->|Subscribe| Sub[Subscriber Service]
        
        Sub --> DB[(MongoDB)]
        Sub --> AI[YZ Karar Motoru]
        Sub --> Viz[Grafik Üretimi - Matplotlib]
        
        AI -->|Mantıksal Analiz| CM[Komut Üretimi]
        CM -->|sulama_ac / sulama_kapat| P_CMD[Command Publisher]
        P_CMD --> B
    end

    style S1 fill:#f9f,stroke:#333,stroke-width:2px
    style AI fill:#00ff00,stroke:#333,stroke-width:2px
    style DB fill:#4488ff,stroke:#333,stroke-width:2px
```
