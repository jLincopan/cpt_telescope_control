# antenna_pointing_calibration.py

import sys
import os
from AntennaTracking import AntennaTracking

try:
    import tty
    import termios
    UNIX = True
except ImportError:
    UNIX = False

def read_key_unix(fd, old_settings):
    """
    Lee una tecla en raw mode. 
    IMPORTANTE: el caller ya configuró raw mode, no lo hacemos aquí.
    """
    ch = os.read(fd, 1).decode('utf-8', errors='replace')
    if ch == '\x03':
        raise KeyboardInterrupt
    if ch == '\x1b':
        # Intentar leer el resto del escape sequence con timeout
        # setamos un timeout para no bloquear si es Esc solo
        import select
        r, _, _ = select.select([sys.stdin], [], [], 0.05)
        if r:
            ch2 = os.read(fd, 1).decode('utf-8', errors='replace')
            if ch2 == '[':
                r2, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r2:
                    ch3 = os.read(fd, 1).decode('utf-8', errors='replace')
                    return '\x1b[' + ch3
        return '\x1b'
    return ch

def antenna_pointing_calibration(antenna_tracking: AntennaTracking):
    """
    Modo calibración: toma control exclusivo del terminal.
    Debe llamarse desde el hilo principal o con prompt_toolkit pausado.
    """
    ARROW_KEYS_UNIX = {
        '\x1b[A': 'arriba',
        '\x1b[B': 'abajo',
        '\x1b[C': 'derecha',   # OJO: C es RIGHT = derecha en azimuth+
        '\x1b[D': 'izquierda', # D es LEFT
    }

    if not UNIX:
        print("Calibración por teclado no disponible en este sistema.")
        return

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    def raw_print(msg):
        print('\r' + msg)

    raw_print("Modo calibración activo, 'q' = salir. Ajustar offset con las flechas en el teclado (arriba,abajo,izquierda,derecha)")
    raw_print(f"Offset actual: az={antenna_tracking.azimuth_offset:.2f}° el={antenna_tracking.elevation_offset:.2f}°")

    try:
        tty.setraw(fd)
        while antenna_tracking.is_tracking:
            key = read_key_unix(fd, old_settings)
            if key == 'q':
                raw_print("Saliendo de calibración...")
                antenna_tracking.is_tracking = False
                break
            label = ARROW_KEYS_UNIX.get(key)
            if label:
                if label == "arriba":
                    antenna_tracking.elevation_offset = round(antenna_tracking.elevation_offset + 0.1, 1)
                elif label == "abajo":
                    antenna_tracking.elevation_offset = round(antenna_tracking.elevation_offset - 0.1, 1)
                elif label == "izquierda":
                    antenna_tracking.azimuth_offset = round(antenna_tracking.azimuth_offset - 0.1, 1)
                elif label == "derecha":
                    antenna_tracking.azimuth_offset = round(antenna_tracking.azimuth_offset + 0.1, 1)
    except KeyboardInterrupt:
        raw_print("\nInterrumpido.")
    finally:
        # SIEMPRE restaurar antes de salir
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)