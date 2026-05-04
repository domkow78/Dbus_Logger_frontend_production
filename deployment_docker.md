# Deployment with Docker - Dbus Logger Frontend

Instrukcja uruchomienia aplikacji w kontenerze Docker.

---

## 1. Wymagania
- Docker zainstalowany na systemie

## 2. Przygotowanie plików

Upewnij się, że w katalogu projektu znajdują się:
- `start_frontend.py`
- katalog `app/`
- `requirements.txt`
- `stations.json` (lub zamontuj go jako wolumen)

## 3. Przykładowy Dockerfile

```Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "start_frontend.py", "--no-browser"]
```


## 4. Budowanie obrazu

### a) Budowanie ręczne (Docker)
W katalogu projektu uruchom:
```bash
docker build -t dbus-logger-frontend .
```

### b) Budowanie przez Docker Compose
W katalogu projektu uruchom:
```bash
docker-compose build
```


## 5. Uruchamianie kontenera

### a) Docker Compose (zalecane)

W katalogu projektu uruchom:
```bash
docker-compose up --build -d
```

Plik stations.json zostanie automatycznie zamontowany do kontenera.

### b) Ręczne uruchomienie kontenera

```bash
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/stations.json:/app/stations.json \
  --name dbus-logger-frontend \
  dbus-logger-frontend
```

- `-p 8080:8080` — mapuje port kontenera na port hosta
- `-v ...` — montuje plik konfiguracyjny stacji

## 6. Zmienne środowiskowe i parametry
Możesz przekazać parametry startowe, np. inny port:
```bash
docker-compose run dbus-logger-frontend python start_frontend.py --port 80 --no-browser
```
lub
```bash
docker run -d -p 80:80 dbus-logger-frontend python start_frontend.py --port 80 --no-browser
```

## 7. Aktualizacja
Aby zaktualizować aplikację:
```bash
docker-compose build
docker-compose up -d
```
lub dla pojedynczego kontenera:
```bash
docker build -t dbus-logger-frontend .
docker stop dbus-logger-frontend
# (opcjonalnie: docker rm dbus-logger-frontend)
docker run ...
```

---

## Notatki
- Plik `stations.json` możesz trzymać poza kontenerem i montować jako wolumen.
- Jeśli korzystasz z auto-discovery, dodaj do requirements.txt pakiet zeroconf.
- Możesz dodać własny plik Docker Compose do zarządzania wieloma usługami.

---

## Kontakt
Autor: [Twoje Imię]
