"""
API Client dla komunikacji z backend UART Logger.
Obsługuje retry logic i connection pooling.
"""

import logging
import time
from typing import Optional, Dict, Any, List
import requests

logger = logging.getLogger(__name__)


class APIClient:
    """
    Klient API dla komunikacji z backendem UART Logger.
    
    Features:
    - Connection pooling (requests.Session)
    - Retry logic (3 próby × 5s timeout)
    - Automatyczne logowanie błędów
    """
    
    def __init__(self, base_url: str, timeout: float = 5.0, max_retries: int = 3):
        """
        Inicjalizuje klienta API.
        
        Args:
            base_url: URL backendu (np. "http://192.168.1.10:8000")
            timeout: Timeout dla requestów w sekundach
            max_retries: Maksymalna liczba prób przy błędzie
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self._connected = False
        
        logger.info(f"APIClient initialized for {base_url}")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Wykonuje request z retry logic.
        
        Args:
            method: Metoda HTTP ('GET', 'POST', etc.)
            endpoint: Endpoint API (np. '/status')
            **kwargs: Dodatkowe argumenty dla requests (json, params, etc.)
        
        Returns:
            Dict z odpowiedzią JSON lub None przy błędzie
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code == 200:
                    self._connected = True
                    return response.json()
                else:
                    logger.warning(
                        f"Request {method} {endpoint} failed with status {response.status_code}"
                    )
                    
            except requests.exceptions.Timeout:
                logger.warning(
                    f"Timeout #{attempt+1}/{self.max_retries} for {method} {endpoint}"
                )
            except requests.exceptions.ConnectionError:
                logger.warning(
                    f"Connection error #{attempt+1}/{self.max_retries} for {method} {endpoint}"
                )
            except Exception as e:
                logger.error(f"Unexpected error for {method} {endpoint}: {e}")
            
            # Czekaj przed kolejną próbą (oprócz ostatniej)
            if attempt < self.max_retries - 1:
                time.sleep(0.5)
        
        # Wszystkie próby nieudane
        self._connected = False
        return None
    
    def is_connected(self) -> bool:
        """Zwraca status połączenia (True jeśli ostatni request się powiódł)."""
        return self._connected
    
    # =========================================================================
    # ENDPOINT METHODS
    # =========================================================================
    
    def get_health(self) -> Optional[Dict[str, Any]]:
        """
        GET /health - Health check stanowiska.
        
        Returns:
            {
                "status": "healthy" | "unhealthy",
                "station_id": str,
                "hostname": str,
                "ip_address": str,
                "uart": {...},
                "service": {...},
                "timestamp": str
            }
        """
        return self._request('GET', '/health')
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        GET /status - Status aplikacji.
        
        Returns:
            {
                "running": bool,
                "cycle_active": bool,
                "current_cycle": int,
                "current_log_filename": str,
                "rx_queue_size": int,
                "last_activity_time": str
            }
        """
        return self._request('GET', '/status')
    
    def get_logs(self) -> Optional[Dict[str, Any]]:
        """
        GET /logs - Lista plików logów.
        
        Returns:
            {
                "count": int,
                "logs": [
                    {
                        "filename": str,
                        "size_bytes": int,
                        "created": str,
                        "cycle_number": int
                    },
                    ...
                ]
            }
        """
        return self._request('GET', '/logs')
    
    def get_log_content(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        GET /logs/{filename} - Zawartość logu.
        
        Args:
            filename: Nazwa pliku logu
        
        Returns:
            {
                "filename": str,
                "cycle_number": int,
                "lines": [str, ...],
                "frames_count": int
            }
        """
        return self._request('GET', f'/logs/{filename}')
    
    def send_uart_frame(self, addr: int, cmd_h: int, cmd_l: int, data: List[int] = None) -> Optional[Dict[str, Any]]:
        """
        POST /uart/send - Wysłanie ramki UART.
        
        Args:
            addr: Adres urządzenia (0-255)
            cmd_h: Komenda HIGH byte (0-255)
            cmd_l: Komenda LOW byte (0-255)
            data: Opcjonalne dane (lista bajtów)
        
        Returns:
            {
                "success": bool,
                "message": str,
                "frame_hex": str
            }
        """
        payload = {
            "addr": addr,
            "cmd_h": cmd_h,
            "cmd_l": cmd_l,
            "data": data or []
        }
        return self._request('POST', '/uart/send', json=payload)
    
    def get_log_head_tail(self, filename: str, head: int = 10, tail: int = 10) -> Optional[Dict[str, Any]]:
        """
        GET /logs/{filename}?head=N&tail=N - Pobierz pierwsze i ostatnie N linii logu.

        Args:
            filename: Nazwa pliku logu
            head: Ile linii z początku pliku
            tail: Ile linii z końca pliku

        Returns:
            Dict z fragmentem logu lub None przy błędzie
        """
        params = {"head": head, "tail": tail}
        return self._request('GET', f'/logs/{filename}', params=params)

    def close(self):
        """Zamyka session (connection pooling cleanup)."""
        try:
            self.session.close()
            logger.info(f"APIClient session closed for {self.base_url}")
        except Exception as e:
            logger.error(f"Error closing session: {e}")
