"""
Main View - Dashboard z wszystkimi stanowiskami.
"""

import logging
from typing import Dict, Any, Callable
from nicegui import ui

from .api_client import APIClient
from .components import create_station_card, format_uptime

logger = logging.getLogger(__name__)


class MainView:
    """
    Główny widok aplikacji - Dashboard ze wszystkimi stanowiskami.
    
    Features:
    - Dropdown do wyboru stanowiska
    - Przycisk Refresh do odświeżenia listy
    - Grid z kartami stanowisk (status, cycles, uptime)
    - Auto-refresh WYŁĄCZONY (przyciski nie działają z timerem)
    - Navigate do detail view przy kliknięciu karty
    """
    
    def __init__(self, station_manager, navigate_to_station_callback):
        """
        Inicjalizuje MainView.
        
        Args:
            station_manager: Instancja StationManager
            navigate_to_station_callback: Callback do nawigacji (url) -> None
        """
        self.station_manager = station_manager
        self.navigate_to_station = navigate_to_station_callback
        
        # API clients cache
        self.api_clients = {}
        self.station_statuses = {}
    
    def build_page(self):
        """Buduje całą stronę dashboard (header + content)."""
        
        def fetch_statuses():
            """Pobiera statusy wszystkich stanowisk."""
            for station in self.station_manager.get_stations():
                url = station['url']
                
                if url not in self.api_clients:
                    # Krótki timeout i 1 retry dla szybszego sprawdzania (szczególnie dla offline stanowisk)
                    self.api_clients[url] = APIClient(url, timeout=1.0, max_retries=1)
                
                health = self.api_clients[url].get_health()
                
                if health:
                    self.station_statuses[url] = {
                        'status': health.get('status', 'unknown'),
                        'cycles': health.get('service', {}).get('cycles_total', 0),
                        'uptime_seconds': health.get('service', {}).get('uptime_seconds', 0)
                    }
                else:
                    self.station_statuses[url] = {
                        'status': 'offline',
                        'cycles': None,
                        'uptime_seconds': None
                    }
        
        def go_to_station(station_url: str):
            """Przechodzi do strony stanowiska."""
            logger.info(f"Card clicked! Navigating to: {station_url}")
            self.navigate_to_station(station_url)
        
        @ui.refreshable
        def station_cards():
            """Odświeżalna zawartość z kartami stanowisk."""
            current_stations = self.station_manager.get_stations()
            
            if not current_stations:
                ui.label('No stations configured. Add stations to stations.json').classes(
                    'text-gray-500 col-span-3 text-center p-8'
                )
                return
            
            for station in current_stations:
                url = station['url']
                status_data = self.station_statuses.get(url, {})
                
                status = status_data.get('status', 'unknown')
                cycles = status_data.get('cycles')
                uptime_sec = status_data.get('uptime_seconds')
                uptime = format_uptime(uptime_sec) if uptime_sec else None
                
                create_station_card(
                    station_id=station['id'],
                    name=station['name'],
                    location=station['location'],
                    url=url,
                    status=status,
                    cycles=cycles,
                    uptime=uptime,
                    on_click=lambda u=url: go_to_station(u)
                )
        
        def refresh_all():
            """Odświeża statusy i karty."""
            fetch_statuses()
            station_cards.refresh()
        
        def on_manual_refresh():
            """Ręczne odświeżenie."""
            self.station_manager.refresh()
            refresh_all()
            ui.notify('Stations refreshed', type='positive')
        
        # === BUILD UI ===
        
        # Header
        with ui.header(elevated=True).classes('items-center justify-between px-6'):
            ui.label('🌐 DBUS Logger - Multi-Station Monitor').classes('text-h5 font-bold')
            
            # Przycisk Refresh
            ui.button('🔄 Refresh', on_click=on_manual_refresh).classes('bg-blue-500')
        
        # Content
        with ui.column().classes('p-6 w-full'):
            ui.label('Stations Overview').classes('text-h6 mb-4')
            
            with ui.grid(columns=3).classes('gap-4 w-full'):
                station_cards()
        
        # Pierwszy fetch (auto-refresh DISABLED - przyciski nie działają z timerem)
        fetch_statuses()
