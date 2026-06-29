# Deployment Guide - Dbus Logger Frontend

Kompletna instrukcja wdrożenia aplikacji Dbus Logger Frontend.

---

## 📋 Spis treści
1. [Szybki start](#-szybki-start)
2. [Deployment z Docker](#-deployment-z-docker) ⭐ **Zalecane dla Raspberry Pi**
3. [Deployment lokalny](#-deployment-lokalny)
4. [Uruchomienie jako usługa](#-uruchomienie-jako-usługa-linux)
5. [Konfiguracja](#-konfiguracja)
6. [Monitorowanie i aktualizacja](#-monitorowanie-i-aktualizacja)
7. [Troubleshooting](#-troubleshooting)

---

## 🚀 Szybki start

### Dla Raspberry Pi (Docker) ⭐ Zalecane
```bash
# 1. Sklonuj repozytorium
git clone <repository-url>
cd Dbus_Logger_frontend_production

# 2. Upewnij się, że stations.json jest obecny
ls stations.json

# 3. Uruchom
docker-compose up -d --build

# 4. Sprawdź status
docker-compose ps
docker-compose logs -f
```

Aplikacja wystartuje automatycznie po restarcie Raspberry Pi.
Dostępna pod: `http://localhost:8080`

### Dla rozwoju lokalnego
```bash
# 1. Sklonuj repozytorium
git clone <repository-url>
cd Dbus_Logger_frontend_production

# 2. Stwórz środowisko wirtualne
python -m venv venv

# 3. Aktywuj środowisko
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 4. Zainstaluj zależności
pip install -r requirements.txt

# 5. Uruchom
python start_frontend.py
```

Dostępna pod: `http://localhost:8080`

---

## 🐳 Deployment z Docker

**Zalecane dla produkcji i Raspberry Pi**

### Wymagania
- Docker Engine 20.10+
- Docker Compose (lub Docker Compose V2)
- **Raspberry Pi**: sprawdź wersję `docker --version`

### Pliki konfiguracyjne

Upewnij się, że w katalogu projektu znajdują się:
- `Dockerfile`
- `docker-compose.yml`
- `start_frontend.py`
- katalog `app/`
- `requirements.txt`
- `stations.json`

### Budowanie obrazu

#### Docker Compose (zalecane)
```bash
docker-compose build
```

#### Ręczne budowanie
```bash
docker build -t dbus-logger-frontend .
```

**Dla Raspberry Pi** (budowanie na innej platformie):
```bash
# RPi 4/5 (64-bit)
docker buildx build --platform linux/arm64 -t dbus-logger-frontend .

# Starsze RPi (32-bit)
docker buildx build --platform linux/arm/v7 -t dbus-logger-frontend .
```

### Uruchamianie

#### Docker Compose (zalecane)
```bash
# Uruchom w tle
docker-compose up -d --build

# Sprawdź status
docker-compose ps

# Zobacz logi
docker-compose logs -f

# Zatrzymaj
docker-compose down
```

#### Ręczne uruchomienie
```bash
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/stations.json:/app/stations.json \
  --name dbus-logger-frontend \
  --restart unless-stopped \
  dbus-logger-frontend
```

**Parametry:**
- `-p 8080:8080` — mapowanie portu
- `-v $(pwd)/stations.json:/app/stations.json` — montowanie konfiguracji
- `--restart unless-stopped` — auto-restart po restarcie systemu
- `-d` — uruchomienie w tle

### Zmiana portu
```bash
# Docker Compose - edytuj docker-compose.yml:
ports:
  - "80:80"
command: ["python", "start_frontend.py", "--port", "80", "--no-browser"]

# Ręczne uruchomienie
docker run -d -p 80:80 dbus-logger-frontend python start_frontend.py --port 80 --no-browser
```

### Uwagi dla Raspberry Pi

**Wydajność:**
- Budowanie obrazu: 5-15 minut
- Zużycie RAM: ~100-200 MB

**Auto-restart:**
Kontener automatycznie wystartuje po restarcie RPi dzięki `restart: unless-stopped`

**Sprawdzenie platformy:**
```bash
docker inspect dbus-logger-frontend | grep Architecture
```

**Problemy z ARM:**
Jeśli obraz nie działa, wymuś platformę ARM:
```bash
docker build --platform linux/arm64 -t dbus-logger-frontend .
```

---

## 💻 Deployment lokalny

**Dla rozwoju i testowania**

### Wymagania
- Python 3.9+
- System: Linux/Windows/macOS
- Dostęp do portu 8080 (lub innego wybranego)

### Przygotowanie środowiska

#### 1. Klonowanie repozytorium
```bash
git clone <adres_repozytorium>
cd Dbus_Logger_frontend_production
```

#### 2. Tworzenie środowiska wirtualnego
```bash
python -m venv venv

# Aktywacja
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

#### 3. Instalacja zależności
```bash
pip install -r requirements.txt
```

### Uruchomienie

#### Standardowe (z przeglądarką)
```bash
python start_frontend.py
```

#### Produkcyjne (bez przeglądarki)
```bash
python start_frontend.py --no-browser
```

#### Zmiana portu
```bash
python start_frontend.py --port 80 --no-browser
```

#### Auto-discovery stacji w LAN
```bash
# Zainstaluj zeroconf
pip install zeroconf

# Uruchom z auto-discovery
python start_frontend.py --auto-discovery
```

### Parametry uruchomienia
```bash
python start_frontend.py --help
```

Dostępne opcje:
- `--port PORT` — zmień port (domyślnie: 8080)
- `--no-browser` — nie otwieraj przeglądarki automatycznie
- `--auto-discovery` — wykrywaj stacje w sieci lokalnej

---

## 🔧 Uruchomienie jako usługa (Linux)

### Systemd Service

#### 1. Utwórz plik usługi
```bash
sudo nano /etc/systemd/system/dbus-logger-frontend.service
```

#### 2. Dodaj konfigurację
```ini
[Unit]
Description=Dbus Logger Frontend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Dbus_Logger_frontend_production
ExecStart=/home/pi/Dbus_Logger_frontend_production/venv/bin/python start_frontend.py --no-browser
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Dostosuj:**
- `User=pi` → twoja nazwa użytkownika
- `WorkingDirectory=...` → ścieżka do projektu
- `ExecStart=...` → ścieżka do python w venv

#### 3. Aktywuj usługę
```bash
# Przeładuj konfigurację
sudo systemctl daemon-reload

# Włącz auto-start
sudo systemctl enable dbus-logger-frontend

# Uruchom usługę
sudo systemctl start dbus-logger-frontend

# Sprawdź status
sudo systemctl status dbus-logger-frontend
```

#### 4. Zarządzanie usługą
```bash
# Start
sudo systemctl start dbus-logger-frontend

# Stop
sudo systemctl stop dbus-logger-frontend

# Restart
sudo systemctl restart dbus-logger-frontend

# Logi
sudo journalctl -u dbus-logger-frontend -f
```

---

## 🔧 Konfiguracja

### Plik stations.json
Plik konfiguracyjny ze stacjami DBus:
```json
{
  "stations": [
    {
      "name": "Station 1",
      "ip": "192.168.1.100",
      "port": 8000
    }
  ]
}
```

### Zmienne środowiskowe (Docker)
W pliku `docker-compose.yml`:
```yaml
environment:
  - PYTHONUNBUFFERED=1
  - CUSTOM_VAR=value
```

### Parametry uruchomienia
```bash
python start_frontend.py --help
```

---

## 📊 Monitorowanie

### Docker
```bash
# Status kontenerów
docker-compose ps

# Logi
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down
```

### Lokalne
Sprawdź terminal gdzie uruchomiono `python start_frontend.py`

---

## 🔄 Aktualizacja

### Docker
```bash
# Pobierz najnowszy kod
git pull

# Przebuduj i uruchom ponownie
docker-compose down
docker-compose up -d --build
```

### Lokalne
```bash
# Pobierz najnowszy kod
git pull

# Zaktualizuj zależności
pip install -r requirements.txt --upgrade

# Uruchom ponownie
python start_frontend.py
```

---

## ⚙️ Porównanie metod deployment

| Funkcja | Docker | Lokalne |
|---------|--------|---------|
| Łatwość instalacji | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Raspberry Pi | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Izolacja | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Auto-restart | ⭐⭐⭐⭐⭐ | ⭐ |
| Rozwój/Debug | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Zużycie RAM | 100-200 MB | 50-100 MB |

**Rekomendacja:**
- 🐳 **Docker** → Produkcja, Raspberry Pi, wdrożenia
- 💻 **Lokalne** → Rozwój, testowanie, debugging

---

## 🆘 Troubleshooting

### Docker nie startuje
```bash
# Sprawdź logi
docker-compose logs

# Sprawdź czy port 8080 jest wolny
netstat -tuln | grep 8080  # Linux
netstat -an | findstr :8080  # Windows

# Rebuild z czystego stanu
docker-compose down -v
docker-compose up -d --build
```

### Aplikacja nie odpowiada (lokalne)
```bash
# Sprawdź czy stations.json istnieje
ls stations.json

# Sprawdź czy wszystkie zależności są zainstalowane
pip list

# Reinstaluj requirements
pip install -r requirements.txt --force-reinstall
```

### Raspberry Pi - obraz nie buduje się
```bash
# Wymuś platformę ARM
docker build --platform linux/arm64 -t dbus-logger-frontend .

# Sprawdź architekturę
uname -m  # powinno być: aarch64 lub armv7l
```

---

## 📚 Dodatkowe zasoby

- [Dokumentacja Docker](deployment_docker.md)
- [Dokumentacja lokalna](deployment_local.md)
- [README projektu](README.md)

---

## 📝 Licencja i kontakt

Więcej informacji w pliku [README.md](README.md)
