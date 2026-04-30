# GUI Module - UART Logger Frontend

## 📁 Struktura

```
gui/
├── __init__.py
├── README.md              # Ten plik
├── station_manager.py     # Zarządzanie konfiguracją stanowisk
├── api_client.py          # HTTP client do komunikacji z backend
├── main_view.py           # Dashboard - przegląd stanowisk
├── detail_view.py         # Widok szczegółowy stanowiska
└── components.py          # Komponenty wielokrotnego użytku
```

## 🎯 Architektura

### StationManager (`station_manager.py`)
Zarządza konfiguracją stanowisk:
- Wczytuje `stations.json`
- Opcjonalne auto-discovery (mDNS/Zeroconf)
- Walidacja i merge konfiguracji

### APIClient (`api_client.py`)
HTTP client z retry logic:
- Connection pooling (requests.Session)
- Automatyczne retry (3 próby × 5s timeout)
- Metody dla wszystkich endpointów API

### MainView (`main_view.py`)
Dashboard - strona główna `/`:
- Grid z kartami stanowisk (3 kolumny)
- Status badges (online/offline)
- Liczba cykli i uptime dla każdego stanowiska
- Dropdown "Quick Jump"
- Przycisk "Refresh"
- Nawigacja do detail view

### DetailView (`detail_view.py`)
Szczegółowy widok `/station?url=...`:
- Karty statusu (Status, Cycles, Uptime, UART, Cycle Active)
- Lista logów cykli (klikalne)
- Podgląd zawartości logów w dialogu
- Sekcja UART Send (wysyłanie ramek debug)
- Auto-refresh co 5s

### Components (`components.py`)
Komponenty wielokrotnego użytku:
- `create_status_badge()` - Badge ze statusem
- `create_station_card()` - Karta stanowiska
- `format_uptime()` - Formatowanie czasu
- `format_bytes()` - Formatowanie rozmiaru

## 🚀 Użycie

### W start_frontend.py

```python
from app.gui.station_manager import StationManager
from app.gui.main_view import MainView
from app.gui.detail_view import DetailView

# Inicjalizacja
station_manager = StationManager(
    config_path='stations.json',
    auto_discovery=False
)

# Dashboard page
@ui.page('/')
def dashboard_page():
    view = MainView(
        station_manager=station_manager,
        navigate_to_station_callback=lambda url: ui.navigate.to(f'/station?url={url}')
    )
    view.build_page()

# Detail page
@ui.page('/station')
def station_page(url: str = None):
    station = station_manager.get_station_by_url(url)
    view = DetailView(
        station=station,
        navigate_to_dashboard_callback=lambda: ui.navigate.to('/')
    )
    view.build_page()
```

## 🔧 Konfiguracja

### stations.json

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

Wymagane pola:
- `id` - Unikalny identyfikator
- `name` - Nazwa wyświetlana
- `url` - URL backendu (http://IP:PORT)
- `location` - Lokalizacja fizyczna

## 📡 API Endpoints

APIClient obsługuje:

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/health` | GET | Status stanowiska (healthy/unhealthy) |
| `/status` | GET | Szczegóły aplikacji (cycle active, queue, etc.) |
| `/logs` | GET | Lista plików logów |
| `/logs/{filename}` | GET | Zawartość logu |
| `/uart/send` | POST | Wysłanie ramki UART |

## 🎨 UI/UX Features

- **NiceGUI** - Web framework
- **Tailwind CSS** - Styling (responsive grid, cards, badges)
- **Auto-refresh**:
  - Dashboard: wyłączony (ręczny refresh)
  - Detail: co 5s
- **Material Design Icons**
- **Responsive layout** (3-column grid)

## 📝 Notatki

### Refaktoryzacja (2026-02-20)
Przeniesiono działający kod z `start_frontend.py` do klas:
- **Przed**: Cała logika inline w funkcjach `@ui.page()`
- **Po**: Klasy `MainView` i `DetailView` z metodą `build_page()`
- **Korzyści**: 
  - Separation of concerns
  - Łatwiejsze testowanie
  - Możliwość reużycia komponentów
  - Czystszy `start_frontend.py` (tylko routing)

### Auto-refresh Dashboard
Wyłączony ze względu na problemy z interaktywnością przycisków podczas działania timera.
Użytkownik może użyć przycisku "🔄 Refresh" do ręcznego odświeżenia.
