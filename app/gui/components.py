"""
Reusable UI Components dla UART Logger GUI.
"""

from nicegui import ui
from typing import Optional, Callable


def create_status_badge(status: str, text: Optional[str] = None) -> ui.badge:
    """
    Tworzy badge ze statusem.
    
    Args:
        status: 'online', 'offline', 'warning', 'unknown'
        text: Opcjonalny tekst (default: status.upper())
    
    Returns:
        ui.badge
    """
    color_map = {
        'online': 'positive',
        'healthy': 'positive',
        'offline': 'negative',
        'unhealthy': 'negative',
        'warning': 'warning',
        'unknown': 'grey'
    }
    
    display_text = text or status.upper()
    color = color_map.get(status.lower(), 'grey')
    
    return ui.badge(display_text, color=color)


def create_info_card(title: str, value: str, icon: Optional[str] = None) -> ui.card:
    """
    Tworzy kartę z informacją (title + value).
    
    Args:
        title: Tytuł (mała czcionka, grey)
        value: Wartość (duża czcionka, bold)
        icon: Opcjonalna ikona Material Design
    
    Returns:
        ui.card
    """
    with ui.card().classes('p-4'):
        if icon:
            with ui.row().classes('items-center gap-2'):
                ui.icon(icon).classes('text-2xl text-blue-500')
                ui.label(title).classes('text-sm text-gray-500')
        else:
            ui.label(title).classes('text-sm text-gray-500')
        
        ui.label(value).classes('text-2xl font-bold')
    
    return ui.card


def create_station_card(
    station_id: str,
    name: str,
    location: str,
    url: str,
    status: str = 'unknown',
    cycles: Optional[int] = None,
    uptime: Optional[str] = None,
    on_click: Optional[Callable] = None
) -> ui.card:
    """
    Tworzy kartę stanowiska dla dashboard.
    
    Args:
        station_id: ID stanowiska
        name: Nazwa stanowiska
        location: Lokalizacja
        url: URL backendu
        status: Status ('online', 'offline', 'unknown')
        cycles: Liczba cykli (optional)
        uptime: Uptime string (optional)
        on_click: Callback przy kliknięciu
    
    Returns:
        ui.card
    """
    card = ui.card().classes('p-4 hover:shadow-lg transition-shadow')
    
    with card:
        # Header: nazwa + status badge
        with ui.row().classes('items-center justify-between w-full mb-2'):
            ui.label(name).classes('text-lg font-bold')
            create_status_badge(status)
        
        # Informacje
        ui.label(f"ID: {station_id}").classes('text-sm text-gray-600')
        ui.label(f"📍 {location}").classes('text-sm text-gray-600')
        ui.label(f"🔗 {url}").classes('text-xs text-gray-400 font-mono')
        
        # Metryki jeśli dostępne
        if cycles is not None or uptime is not None:
            ui.separator().classes('my-2')
            with ui.row().classes('gap-4'):
                if cycles is not None:
                    ui.label(f"🔄 Cycles: {cycles}").classes('text-sm')
                if uptime is not None:
                    ui.label(f"⏱️ Uptime: {uptime}").classes('text-sm')
        
        # Przycisk do przejścia - zablokowany jeśli stanowisko offline/unknown
        if on_click:
            is_online = status.lower() in ['online', 'healthy']
            button = ui.button('🔍 View Details', on_click=on_click if is_online else None)
            button.classes('mt-2 w-full')
            
            if not is_online:
                button.disable()
                button.classes('opacity-50 cursor-not-allowed')
                button.tooltip('Stanowisko niedostępne - nie można wyświetlić szczegółów')
    
    return card


def format_uptime(seconds: float) -> str:
    """
    Formatuje uptime w sekundach na czytelny string.
    
    Args:
        seconds: Uptime w sekundach
    
    Returns:
        String np. "2h 15m" lub "45m" lub "30s"
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


def format_bytes(bytes_count: int) -> str:
    """
    Formatuje rozmiar w bajtach na czytelny string.
    
    Args:
        bytes_count: Rozmiar w bajtach
    
    Returns:
        String np. "1.5 KB" lub "2.3 MB"
    """
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    else:
        return f"{bytes_count / (1024 * 1024):.1f} MB"
