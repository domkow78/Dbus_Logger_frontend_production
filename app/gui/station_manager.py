"""
Station Manager - Zarządzanie konfiguracją stanowisk.
Wczytuje stations.json + opcjonalne auto-discovery (mDNS).
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class StationManager:
    """
    Zarządza listą stanowisk (backends).
    
    Features:
    - Wczytywanie z stations.json
    - Opcjonalne auto-discovery (mDNS/Zeroconf)
    - Merge konfiguracji (config ma priorytet dla nazw/lokalizacji)
    - Walidacja danych
    """
    
    def __init__(self, config_path: str = "stations.json", auto_discovery: bool = False):
        """
        Inicjalizuje StationManager.
        
        Args:
            config_path: Ścieżka do pliku stations.json
            auto_discovery: Czy włączyć auto-discovery (mDNS)
        """
        self.config_path = Path(config_path)
        self.auto_discovery_enabled = auto_discovery
        self.stations: List[Dict[str, Any]] = []
        
        # Wczytaj konfigurację
        self.load_stations()
        
        # Auto-discovery jeśli włączone
        if self.auto_discovery_enabled:
            self.discover_stations()
    
    def load_stations(self) -> None:
        """
        Wczytuje listę stanowisk z pliku JSON.
        
        Waliduje wymagane pola: id, name, url, location
        """
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                logger.info("Using empty station list")
                self.stations = []
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Walidacja
            if not isinstance(data, dict) or 'stations' not in data:
                logger.error("Invalid stations.json format - expected {'stations': [...]}")
                self.stations = []
                return
            
            raw_stations = data['stations']
            
            if not isinstance(raw_stations, list):
                logger.error("Invalid stations.json format - 'stations' must be array")
                self.stations = []
                return
            
            # Waliduj każde stanowisko
            validated = []
            for idx, station in enumerate(raw_stations):
                if self._validate_station(station, idx):
                    validated.append(station)
            
            self.stations = validated
            logger.info(f"Loaded {len(self.stations)} stations from {self.config_path}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.config_path}: {e}")
            self.stations = []
        except Exception as e:
            logger.error(f"Error loading stations config: {e}")
            self.stations = []
    
    def _validate_station(self, station: Dict[str, Any], index: int) -> bool:
        """
        Waliduje pojedyncze stanowisko.
        
        Args:
            station: Dict z danymi stanowiska
            index: Index w liście (dla komunikatów błędów)
        
        Returns:
            True jeśli valid, False jeśli invalid
        """
        required_fields = ['id', 'name', 'url', 'location']
        
        for field in required_fields:
            if field not in station:
                logger.warning(
                    f"Station #{index} missing required field '{field}' - skipping"
                )
                return False
            
            if not isinstance(station[field], str) or not station[field].strip():
                logger.warning(
                    f"Station #{index} field '{field}' must be non-empty string - skipping"
                )
                return False
        
        # Sprawdź format URL
        url = station['url']
        if not url.startswith('http://') and not url.startswith('https://'):
            logger.warning(
                f"Station #{index} URL '{url}' should start with http:// or https://"
            )
            # Nie odrzucaj - może działać
        
        return True
    
    def discover_stations(self) -> None:
        """
        Auto-discovery stanowisk w sieci (mDNS/Zeroconf).
        
        Wymaga: pip install zeroconf
        Wyszukuje usługi _uart-logger._tcp.local.
        Merguje z istniejącą konfiguracją (config ma priorytet).
        """
        try:
            from zeroconf import ServiceBrowser, Zeroconf, ServiceListener
            import time
            
            class UARTLoggerListener(ServiceListener):
                def __init__(self):
                    self.discovered = []
                
                def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
                    info = zc.get_service_info(type_, name)
                    if info:
                        # Parsuj informacje
                        import socket
                        addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
                        if addresses:
                            station_data = {
                                'id': info.properties.get(b'station_id', b'Unknown').decode('utf-8'),
                                'name': f"Auto-discovered: {name}",
                                'url': f"http://{addresses[0]}:{info.port}",
                                'location': "Auto-discovered via mDNS"
                            }
                            self.discovered.append(station_data)
                            logger.info(f"Discovered station: {station_data['id']} at {station_data['url']}")
                
                def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
                    pass
                
                def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
                    pass
            
            logger.info("Starting mDNS auto-discovery...")
            zeroconf = Zeroconf()
            listener = UARTLoggerListener()
            browser = ServiceBrowser(zeroconf, "_uart-logger._tcp.local.", listener)
            
            # Czekaj 3 sekundy na odpowiedzi
            time.sleep(3)
            
            zeroconf.close()
            
            # Merge z istniejącą konfiguracją
            if listener.discovered:
                logger.info(f"Auto-discovered {len(listener.discovered)} stations")
                self._merge_stations(listener.discovered)
            else:
                logger.info("No stations discovered via mDNS")
            
        except ImportError:
            logger.warning("Auto-discovery disabled: 'zeroconf' package not installed")
            logger.info("Install with: pip install zeroconf")
        except Exception as e:
            logger.error(f"Error during auto-discovery: {e}")
    
    def _merge_stations(self, discovered: List[Dict[str, Any]]) -> None:
        """
        Merguje discovered stations z config stations.
        Config ma priorytet dla name/location.
        
        Args:
            discovered: Lista stanowisk z auto-discovery
        """
        # Tworzymy dict dla szybkiego lookup (klucz: url)
        config_by_url = {s['url']: s for s in self.stations}
        
        for disc_station in discovered:
            url = disc_station['url']
            
            if url in config_by_url:
                # Już mamy w config - config ma priorytet, tylko sprawdzamy czy dostępne
                logger.debug(f"Station {url} already in config - keeping config data")
            else:
                # Nowe stanowisko - dodaj
                logger.info(f"Adding new discovered station: {url}")
                self.stations.append(disc_station)
    
    def get_stations(self) -> List[Dict[str, Any]]:
        """
        Zwraca listę wszystkich stanowisk.
        
        Returns:
            Lista dict z polami: id, name, url, location
        """
        return self.stations.copy()
    
    def get_station_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Znajduje stanowisko po URL.
        
        Args:
            url: URL stanowiska
        
        Returns:
            Dict ze stanowiskiem lub None
        """
        for station in self.stations:
            if station['url'] == url:
                return station.copy()
        return None
    
    def refresh(self) -> None:
        """
        Odświeża listę stanowisk.
        Przeładowuje config + ponowne auto-discovery jeśli włączone.
        """
        logger.info("Refreshing station list...")
        self.load_stations()
        
        if self.auto_discovery_enabled:
            self.discover_stations()
        
        logger.info(f"Refresh complete - {len(self.stations)} stations available")
