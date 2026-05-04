
# Dbus Logger Frontend

## Opis

Aplikacja webowa do monitorowania wielu stanowisk (np. urządzeń z DBUS) przez przeglądarkę, oparta o NiceGUI. Pozwala na podgląd statusów, logów oraz szczegółów stanowisk w sieci lokalnej.

## Wymagania
- Python 3.9+
- nicegui
- requests

## Instalacja

1. Utwórz i aktywuj środowisko wirtualne:
	 ```
	 python -m venv venv
	 venv\Scripts\activate  # Windows
	 # lub
	 source venv/bin/activate  # Linux/Mac
	 ```
2. Zainstaluj wymagane pakiety:
	 ```
	 pip install -r requirements.txt
	 ```

## Uruchomienie

1. Skonfiguruj plik `stations.json` (przykład poniżej).
2. Uruchom frontend:
	 ```
	 python start_frontend.py
	 ```
	 Domyślnie GUI będzie dostępne na http://localhost:8080

### Parametry uruchomienia
- `--backend URL` — domyślny backend, jeśli nie ma stacji w configu
- `--stations-config FILE` — ścieżka do pliku konfiguracyjnego stacji
- `--auto-discovery` — automatyczne wykrywanie stacji w LAN (wymaga zeroconf)
- `--port N` — port frontend (domyślnie 8080)
- `--no-browser` — nie otwieraj automatycznie przeglądarki

## Przykładowy stations.json
```json
{
	"stations": [
		{
			"id": "RPI-01",
			"name": "Stanowisko 1 - LOCAL",
			"url": "http://127.0.0.1:8000",
			"location": "Komputer deweloperski"
		},
		{
			"id": "RPI-02",
			"name": "Stanowisko 2",
			"url": "http://192.168.1.11:8000",
			"location": "Laboratorium - Stół 2"
		}
	]
}
```

## Struktura projektu

```
Dbus_Logger_frontend_production/
├── app/
│   └── gui/
│       ├── api_client.py
│       ├── components.py
│       ├── detail_view.py
│       ├── main_view.py
│       ├── station_manager.py
│       └── ...
├── start_frontend.py
├── requirements.txt
└── stations.json
```

## Funkcje
- Dashboard z listą stanowisk
- Szczegółowy widok stanowiska
- Podgląd logów
- Wysyłanie ramek UART (debug)
- Auto-refresh szczegółów stanowiska

## Licencja
MIT
