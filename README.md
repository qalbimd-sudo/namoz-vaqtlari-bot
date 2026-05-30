# Namoz Vaqtlari Bot

Telegram guruhlarga har kuni namoz vaqtlarini avtomatik yuboradigan bot (Aiogram 3.x + APScheduler).

## Xususiyatlar

- Guruhga qo'shilganda avtomatik ro'yxatdan o'tish (SQLite)
- - Har kuni soat **05:00** da (Toshkent vaqti) barcha guruhlarga namoz vaqtlarini yuborish
  - - `/vaqtlar` buyrug'i bilan istalgan vaqtda bugungi vaqtlarni ko'rish
    - - **NamozTime API** (islom.uz asosida) — asosiy manba
      - - **Aladhan API** — zaxira manba (agar birinchisi ishlamasa)
        - - Bot guruhdan chiqarilsa, avtomatik bazadan o'chirish
         
          - ## Fayl strukturasi
         
          - ```
            namoz-vaqtlari-bot/
            ├── main.py          # Asosiy bot kodi (handlers, scheduler)
            ├── database.py      # SQLite bilan ishlash funksiyalari
            ├── prayer_api.py    # Namoz vaqtlari API integratsiyasi
            ├── config.py        # Sozlamalar (token, mintaqa, vaqt)
            ├── requirements.txt # Kerakli kutubxonalar
            ├── .env.example     # Token namunasi
            └── .gitignore       # Git ignore fayli
            ```

            ## O'rnatish va ishga tushirish

            ### 1. Repozitoriyani yuklab olish

            ```bash
            git clone https://github.com/qalbimd-sudo/namoz-vaqtlari-bot.git
            cd namoz-vaqtlari-bot
            ```

            ### 2. Virtual muhit yaratish (tavsiya etiladi)

            ```bash
            python -m venv venv
            # Windows:
            venv\Scripts\activate
            # Linux/Mac:
            source venv/bin/activate
            ```

            ### 3. Kutubxonalarni o'rnatish

            ```bash
            pip install -r requirements.txt
            ```

            ### 4. Bot tokenini sozlash

            ```bash
            # .env.example dan nusxa oling:
            cp .env.example .env
            ```

            Keyin `.env` faylini oching va tokenni qo'ying:

            ```
            BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi
            ```

            **Token olish:** Telegram da [@BotFather](https://t.me/BotFather) ga boring → `/newbot` → tokenni oling.

            ### 5. Botni ishga tushirish

            ```bash
            python main.py
            ```

            ## Buyruqlar

            | Buyruq | Tavsif |
            |--------|--------|
            | `/start` | Botni ishga tushirish, chatni ro'yxatdan o'tkazish |
            | `/vaqtlar` | Bugungi namoz vaqtlari jadvalini ko'rish |

            ## Sozlamalar (config.py)

            | O'zgaruvchi | Default | Tavsif |
            |-------------|---------|--------|
            | `REGION` | `"Toshkent"` | Mintaqa nomi (NamozTime API uchun) |
            | `CITY` | `"Tashkent"` | Shahar (Aladhan API uchun) |
            | `BROADCAST_HOUR` | `5` | Xabar yuborish soati |
            | `BROADCAST_MINUTE` | `0` | Xabar yuborish daqiqasi |
            | `TIMEZONE` | `"Asia/Tashkent"` | Vaqt mintaqasi |

            ## Serverda ishga tushirish (Linux)

            ### systemd service sifatida

            `/etc/systemd/system/namoz-bot.service` faylini yarating:

            ```ini
            [Unit]
            Description=Namoz Vaqtlari Telegram Bot
            After=network.target

            [Service]
            Type=simple
            User=ubuntu
            WorkingDirectory=/home/ubuntu/namoz-vaqtlari-bot
            ExecStart=/home/ubuntu/namoz-vaqtlari-bot/venv/bin/python main.py
            Restart=always
            RestartSec=10

            [Install]
            WantedBy=multi-user.target
            ```

            Keyin:

            ```bash
            sudo systemctl daemon-reload
            sudo systemctl enable namoz-bot
            sudo systemctl start namoz-bot
            sudo systemctl status namoz-bot
            ```

            ## API haqida

            Bot ikki API dan foydalanadi:

            1. **NamozTime API** (`namoztime.herokuapp.com`) — [zero8d/namozvaqtlariapi](https://github.com/zero8d/namozvaqtlariapi) asosida islom.uz dan olingan vaqtlar
            2. 2. **Aladhan API** (`api.aladhan.com`) — zaxira manba, Method 3 (Muslim World League)
              
               3. ---
              
               4. Muallif: [@qalbimd-sudo](https://github.com/qalbimd-sudo)
               5. 
