#!/usr/bin/env python3
"""
DBUS Logger - Frontend Entry Point
Uruchamia NiceGUI web interface dla multi-station monitoring.

Przeznaczony do uruchomienia na PC operatora.
Frontend dostępny na porcie 8080 (localhost).
"""

import logging
import argparse
import sys
from pathlib import Path

from nicegui import ui, app

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parsuje argumenty wiersza poleceń."""
    parser = argparse.ArgumentParser(
        description='DBUS Logger Frontend - Multi-Station Monitor'
    )
    
    parser.add_argument(
        '--backend',
        type=str,
        default=None,
        help='Default backend URL (np. http://192.168.1.10:8000). If not specified, uses first from config.'
    )
    
    parser.add_argument(
        '--stations-config',
        type=str,
        default='stations.json',
        help='Path to stations.json config file (default: stations.json)'
    )
    
    parser.add_argument(
        '--auto-discovery',
        action='store_true',
        help='Enable mDNS auto-discovery of stations (requires: pip install zeroconf)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Frontend port (default: 8080)'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not auto-open browser'
    )
    
    return parser.parse_args()


def print_banner(args):
    """Wyświetla banner informacyjny."""
    print("\n" + "="*70)
    print("🎨 DBUS LOGGER - FRONTEND (Multi-Station Monitor)")
    print("="*70)
    print(f"Config file:      {args.stations_config}")
    print(f"Auto-discovery:   {'Enabled' if args.auto_discovery else 'Disabled'}")
    print(f"Default backend:  {args.backend or 'From config'}")
    print()
    print(f"Frontend dostępny na:")
    print(f"  • GUI:  http://localhost:{args.port}")
    print()
    print("Aby zatrzymać: Ctrl+C")
    print("="*70 + "\n")


def main():
    """Główna funkcja aplikacji."""
    args = parse_arguments()
    
    # Sprawdź czy config istnieje
    config_path = Path(args.stations_config)
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        logger.warning("Creating empty config - you can add stations later via Refresh")
    
    print_banner(args)
    
    try:
        from app.gui.station_manager import StationManager
        from app.gui.main_view import MainView
        from app.gui.detail_view import DetailView
        
        # Inicjalizuj StationManager
        logger.info("Initializing StationManager...")
        station_manager = StationManager(
            config_path=args.stations_config,
            auto_discovery=args.auto_discovery
        )
        
        stations = station_manager.get_stations()
        logger.info(f"Loaded {len(stations)} stations")
        
        # Jeśli brak stanowisk
        if not stations and not args.backend:
            logger.error("No stations configured and no --backend specified!")
            logger.error("Please:")
            logger.error(f"  1. Add stations to {args.stations_config}, OR")
            logger.error("  2. Use --backend http://IP:8000, OR")
            logger.error("  3. Enable --auto-discovery")
            sys.exit(1)
        
        # =====================================================================
        # ROUTING
        # =====================================================================
        
        @ui.page('/')
        def dashboard_page():
            """Dashboard - przegląd wszystkich stanowisk."""
            view = MainView(
                station_manager=station_manager,
                navigate_to_station_callback=lambda url: ui.navigate.to(f'/station?url={url}')
            )
            view.build_page()
        
        @ui.page('/station')
        def station_page(url: str = None):
            """Szczegółowy widok stanowiska."""
            
            if not url:
                with ui.header(elevated=True).classes('items-center px-6'):
                    ui.button('← Dashboard', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-600')
                    ui.label('Error').classes('text-h5 font-bold text-red-500')
                
                with ui.column().classes('p-6'):
                    ui.label('No station URL provided').classes('text-red-500 text-lg')
                return
            
            # Znajdź stanowisko
            station = station_manager.get_station_by_url(url)
            if not station:
                with ui.header(elevated=True).classes('items-center px-6'):
                    ui.button('← Dashboard', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-600')
                    ui.label('Error').classes('text-h5 font-bold text-red-500')
                
                with ui.column().classes('p-6'):
                    ui.label(f'Station not found: {url}').classes('text-red-500 text-lg')
                return
            
            # Utwórz widok
            view = DetailView(
                station=station,
                navigate_to_dashboard_callback=lambda: ui.navigate.to('/')
            )
            view.build_page()
        
        # =====================================================================
        # RUN
        # =====================================================================
        
        logger.info("Starting NiceGUI frontend...")
        
        ui.run(
            title='DBUS Logger - Multi-Station Monitor',
            port=args.port,
            reload=False,
            show=not args.no_browser
        )
        
    except KeyboardInterrupt:
        logger.info("\n✓ Frontend zatrzymany przez użytkownika (Ctrl+C)")
    except Exception as e:
        logger.error(f"✗ Błąd uruchomienia frontendu: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
