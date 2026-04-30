"""
Detail View - Szczegółowy widok pojedynczego stanowiska.
Monitoring, logi, wysyłanie ramek UART.
"""

import logging
from typing import Dict, Any
from nicegui import ui

from .api_client import APIClient
from .components import create_status_badge, format_uptime, format_bytes

logger = logging.getLogger(__name__)


class DetailView:
    """
    Szczegółowy widok pojedynczego stanowiska.
    
    Features:
    - Real-time status monitoring
    - Lista logów cykli
    - Podgląd zawartości logów
    - Wysyłanie ramek UART (debug)
    - Auto-refresh co 5s
    """
    
    def __init__(self, station: Dict[str, Any], navigate_to_dashboard_callback):
        """
        Inicjalizuje DetailView.
        
        Args:
            station: Dict ze stanowiskiem (id, name, url, location)
            navigate_to_dashboard_callback: Callback do powrotu do dashboardu
        """
        self.station = station
        self.navigate_to_dashboard = navigate_to_dashboard_callback
        self.api_client = APIClient(station['url'], timeout=5.0, max_retries=2)
    
    def build_page(self):
        """Buduje całą stronę detail view (header + content)."""
        
        # === REFRESH FUNCTIONS (define before UI) ===
        
        # Zmienna do kontroli auto-refresh (zatrzymaj gdy dialog otwarty)
        refresh_timer_active = {'value': True}
        
        @ui.refreshable
        def status_display():
            """Odświeżalna zawartość statusu."""
            health = self.api_client.get_health()
            
            if health:
                status = health.get('status', 'unknown')
                service = health.get('service', {})
                uart = health.get('uart', {})
                
                # UWAGA: /health zwraca 'in_cycle' a nie 'cycle_active'
                cycle_active = service.get('in_cycle', False)
                
                with ui.row().classes('gap-4 flex-wrap items-stretch'):
                    # Status badge
                    with ui.card().classes('p-4 flex flex-col justify-between min-h-24'):
                        ui.label('Status').classes('text-sm text-gray-500')
                        create_status_badge(status)
                    
                    # Cycles
                    with ui.card().classes('p-4 flex flex-col justify-between min-h-24'):
                        ui.label('Cycles').classes('text-sm text-gray-500')
                        ui.label(str(service.get('cycles_total', 0))).classes('text-2xl font-bold')
                    
                    # Uptime
                    with ui.card().classes('p-4 flex flex-col justify-between min-h-24'):
                        ui.label('Uptime').classes('text-sm text-gray-500')
                        uptime = format_uptime(service.get('uptime_seconds', 0))
                        ui.label(uptime).classes('text-2xl font-bold')
                    
                    # UART Status
                    with ui.card().classes('p-4 flex flex-col justify-between min-h-24'):
                        ui.label('UART').classes('text-sm text-gray-500')
                        uart_status = 'online' if uart.get('connected') else 'offline'
                        create_status_badge(uart_status, uart.get('port', 'N/A'))
                    
                    # Cycle Active
                    with ui.card().classes('p-4 flex flex-col justify-between min-h-24'):
                        ui.label('Cycle Active').classes('text-sm text-gray-500')
                        create_status_badge('online' if cycle_active else 'offline', 
                                           'YES' if cycle_active else 'NO')
            else:
                ui.label('⚠️ Cannot connect to station').classes('text-orange-500')
                create_status_badge('offline')
        
        def refresh_logs():
            """Odświeża listę logów."""
            try:
                logs_container.clear()
                
                logs_response = self.api_client.get_logs()
                
                with logs_container:
                    if logs_response and 'logs' in logs_response:
                        logs_list = logs_response['logs']
                        logs_count_badge.set_text(str(len(logs_list)))
                        
                        for log_info in logs_list[:20]:  # Max 20 ostatnich
                            filename = log_info.get('filename', 'unknown')
                            size = log_info.get('size_bytes', 0)
                            
                            with ui.card().classes('p-2 cursor-pointer hover:bg-gray-100 w-full').on(
                                'click', lambda f=filename: show_log_content(f)
                            ):
                                with ui.row().classes('items-center justify-between w-full'):
                                    ui.label(f"📄 {filename}").classes('font-mono text-sm')
                                    ui.label(format_bytes(size)).classes('text-xs text-gray-500')
                    else:
                        logs_count_badge.set_text('0')
                        ui.label('No logs available').classes('text-gray-500')
            except Exception:
                # Strona została opuszczona, timer będzie zatrzymany
                pass
        
        def show_log_content(filename: str):
            """Pokazuje zawartość logu w dialogu."""
            # Zatrzymaj auto-refresh podczas gdy dialog otwarty
            refresh_timer_active['value'] = False
            
            content = self.api_client.get_log_content(filename)
            
            # Dialog tworzony na poziomie strony (nie wewnątrz logs_container)
            # aby nie został usunięty przez logs_container.clear() podczas auto-refresh
            dialog = ui.dialog()
            
            def on_close():
                dialog.close()
                # Wznów auto-refresh po zamknięciu dialogu
                refresh_timer_active['value'] = True
            
            with dialog, ui.card().classes('w-full max-w-4xl max-h-[80vh] overflow-auto'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label(f"📄 {filename}").classes('text-h6')
                    ui.button('✕', on_click=on_close).props('flat round dense')
                
                if content and 'lines' in content:
                    lines = content['lines']
                    ui.label(f"Lines: {len(lines)}").classes('text-sm text-gray-600 mb-2')
                    # Białe tło z czarnym tekstem - pasek przewijania zawsze widoczny
                    with ui.scroll_area().classes('w-full h-[60vh] bg-white p-4 border border-gray-300'):
                        for line in lines:
                            ui.label(line).classes('font-mono text-xs text-black')
                else:
                    ui.label('Cannot load log content').classes('text-red-500')
                
                # Przyciski na dole
                with ui.row().classes('w-full gap-2 mt-4'):
                    ui.button('💾 Download', on_click=lambda: ui.navigate.to(f"{self.api_client.base_url}/logs/{filename}/download", new_tab=True)).classes('flex-grow')
                    ui.button('Close', on_click=on_close)
            
            dialog.open()
        
        def refresh_all():
            """Odświeża wszystko."""
            # Skip refresh jeśli dialog otwarty
            if not refresh_timer_active['value']:
                return
                
            try:
                status_display.refresh()
                refresh_logs()
            except Exception:
                # Client został usunięty (użytkownik opuścił stronę)
                pass
        
        # === BUILD UI ===
        
        # Header
        with ui.header(elevated=True).classes('items-center justify-between px-6'):
            with ui.row().classes('items-center gap-4'):
                ui.button('Dashboard', on_click=self.navigate_to_dashboard).classes('bg-gray-600')
                ui.label(f"🌐 {self.station['name']}").classes('text-h5 font-bold')
            
            with ui.row().classes('items-center gap-2'):
                ui.label(f"ID: {self.station['id']}").classes('text-sm text-white')
                ui.label('|').classes('text-white')
                ui.label(f"📍 {self.station['location']}").classes('text-sm text-white')
        
        # Content
        with ui.column().classes('p-6 w-full gap-6'):
            
            # === STATUS SECTION ===
            with ui.card().classes('w-full p-6'):
                ui.label('📊 Application Status').classes('text-h6 mb-4')
                
                with ui.column().classes('w-full gap-4'):
                    status_display()
            
            # === LOGS SECTION ===
            with ui.card().classes('w-full p-6'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('📁 Cycle Logs').classes('text-h6')
                    logs_count_badge = ui.badge('0', color='blue')
                
                logs_container = ui.column().classes('w-full gap-2 max-h-96 overflow-auto')
            
            # === UART SEND SECTION ===
            with ui.expansion('⚡ UART Send (Debug)', icon='send').classes('w-full'):
                with ui.card_section():
                    with ui.grid(columns=3).classes('w-full gap-4'):
                        uart_addr = ui.number('ADDR', value=21, min=0, max=255, precision=0)
                        uart_cmd_h = ui.number('CMD_H', value=16, min=0, max=255, precision=0)
                        uart_cmd_l = ui.number('CMD_L', value=1, min=0, max=255, precision=0)
                    
                    uart_data = ui.input('DATA (hex, np: 01 00)', placeholder='01 00').classes('w-full')
                    
                    with ui.row().classes('w-full gap-2 mt-4'):
                        def send_frame():
                            try:
                                addr = int(uart_addr.value)
                                cmd_h = int(uart_cmd_h.value)
                                cmd_l = int(uart_cmd_l.value)
                                data_hex = uart_data.value.strip()
                                data_bytes = bytes.fromhex(data_hex.replace(' ', '')) if data_hex else b''
                                
                                result = self.api_client.send_uart_frame(addr, cmd_h, cmd_l, list(data_bytes))
                                if result and result.get('success'):
                                    ui.notify(f"✓ Frame sent: {result.get('frame_hex')}", type='positive')
                                else:
                                    msg = result.get('message', 'Unknown error') if result else 'No response'
                                    ui.notify(f'✗ Failed: {msg}', type='negative')
                            except Exception as e:
                                ui.notify(f'Error: {e}', type='negative')
                        
                        ui.button('📤 Wyślij ramkę', on_click=send_frame).classes('w-full')
        
        # Auto-refresh timer (co 5s)
        ui.timer(5.0, refresh_all)
