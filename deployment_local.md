# Deployment - Dbus Logger Frontend

Instrukcja wdrożenia i uruchomienia aplikacji produkcyjnie.

---

## 1. Wymagania systemowe
- Python 3.9+
- System: Linux/Windows
- Dostęp do portu 8080 (lub innego wybranego)

## 2. Przygotowanie środowiska

### a) Klonowanie repozytorium
```bash
git clone <adres_repozytorium>
cd Dbus_Logger_frontend_production
```

### b) Tworzenie środowiska wirtualnego
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# lub
source venv/bin/activate  # Linux/Mac
```

### c) Instalacja zależności
```bash
pip install -r requirements.txt
```

## 3. Konfiguracja

Przygotuj plik `stations.json` z listą stanowisk (patrz README.md).

## 4. Uruchomienie produkcyjne

### a) Standardowe uruchomienie
```bash
python start_frontend.py --no-browser
```

### b) Zmiana portu
```bash
python start_frontend.py --port 80 --no-browser
```

### c) Wykrywanie stacji w LAN (opcjonalnie)
```bash
pip install zeroconf
python start_frontend.py --auto-discovery
```

## 5. Uruchomienie jako usługa (Linux)

Przykład pliku systemd:

```
[Unit]
Description=Dbus Logger Frontend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Dbus_Logger_frontend_production
ExecStart=/home/pi/Dbus_Logger_frontend_production/venv/bin/python start_frontend.py --no-browser
Restart=always

[Install]
WantedBy=multi-user.target
```

Zapisz jako `/etc/systemd/system/dbus-logger-frontend.service`, następnie:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dbus-logger-frontend
sudo systemctl start dbus-logger-frontend
```

## 6. Aktualizacja

Aby zaktualizować kod:
```bash
git pull
pip install -r requirements.txt
sudo systemctl restart dbus-logger-frontend
```

## 7. Uwagi
- Domyślnie aplikacja nasłuchuje na porcie 8080.
- Możesz zmienić port parametrem `--port`.
- Wersja developerska: uruchamiaj z automatycznym otwieraniem przeglądarki (bez `--no-browser`).
- Wersja produkcyjna: uruchamiaj z `--no-browser`.

---

## Kontakt
Autor: [Twoje Imię]
