# Archivo: modules/simulacion/backend/simulacion_backend/infrastructure/virtual_serial.py
"""
Simulador de puertos serie virtuales (COM10, COM11) para pruebas de integración.

Crea pares de puertos COM virtuales usando sockets TCP en localhost, permitiendo
comunicación entre una aplicación cliente (simulada como puerto COM) y un
dispositivo ESP32 virtual sin necesidad de hardware físico real.

No requiere drivers adicionales ni derechos de administrador en Windows.
"""

import socket
import threading
import time
from typing import Optional, Callable, Dict
from threading import Thread, Event


class VirtualSerialPort:
    """
    Simula un puerto serie COM usando sockets TCP localhost.
    Permite abrir, escribir, leer y cerrar como si fuera un puerto serie real.
    """

    def __init__(self, port_name: str = "COM10", host: str = "127.0.0.1", port: int = 0, baudrate: int = 115200):
        self.port_name = port_name
        self.host = host
        self.port = port
        self.baudrate = baudrate
        self._socket: Optional[socket.socket] = None
        self._conn: Optional[socket.socket] = None
        self._is_open = False
        self._stop_event = Event()
        self._read_thread: Optional[threading.Thread] = None
        self._on_data_received: Optional[Callable[[bytes], None]] = None
        self._buffer = b""
        self._lock = threading.Lock()

    def open(self, baudrate: int = None, timeout: float = 1.0) -> bool:
        """Conecta al puerto virtual."""
        if baudrate is not None:
            self.baudrate = baudrate
        elif not hasattr(self, 'baudrate') or self.baudrate is None:
            self.baudrate = 115200
        if self._is_open:
            return True

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(timeout)
            self._socket.connect((self.host, self.port))
            self._socket.settimeout(None)
            self._is_open = True
            self._stop_event.clear()
            self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()
            return True
        except Exception:
            self._is_open = False
            return False

    def connect(self, baudrate: int = None, timeout: float = 1.0) -> bool:
        """Conecta al puerto virtual (alias de open())."""
        return self.open(baudrate=baudrate, timeout=timeout)

    def close(self) -> None:
        """Cierra la conexión simulada."""
        self._stop_event.set()
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
        self._is_open = False

    def disconnect(self) -> None:
        """Desconecta el puerto virtual (alias de close)."""
        self.close()

    def _read_loop(self) -> None:
        """Bucle de lectura en segundo plano."""
        while not self._stop_event.is_set() and self._is_open:
            try:
                if self._conn:
                    data = self._conn.recv(1024)
                    if data:
                        with self._lock:
                            self._buffer += data
                        if self._on_data_received:
                            self._on_data_received(data)
                    else:
                        # Conexión cerrada por el otro extremo
                        break
                else:
                    time.sleep(0.01)
            except Exception:
                break

    def write(self, data: bytes) -> int:
        """Escribe datos al puerto simulado."""
        if not self._is_open or not self._conn:
            raise IOError(f"Puerto {self.port_name} no está abierto")
        try:
            self._conn.sendall(data)
            return len(data)
        except Exception as exc:
            raise IOError(f"Error escribiendo a {self.port_name}: {exc}")

    def read(self, size: int = 1, timeout: float = 1.0) -> bytes:
        """Lee datos del puerto simulado."""
        if not self._is_open:
            raise IOError(f"Puerto {self.port_name} no está abierto")

        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._lock:
                if len(self._buffer) >= size:
                    data = self._buffer[:size]
                    self._buffer = self._buffer[size:]
                    return data
                elif len(self._buffer) > 0:
                    data = self._buffer
                    self._buffer = b""
                    return data
            time.sleep(0.01)
        return b""

    def in_waiting(self) -> int:
        """Retorna la cantidad de bytes disponibles para leer."""
        with self._lock:
            return len(self._buffer)

    def set_on_data_received(self, callback: Callable[[bytes], None]) -> None:
        """Registra un callback para cuando se reciben datos."""
        self._on_data_received = callback

    def accept_connection(self, timeout: float = 5.0) -> bool:
        """Espera a que un cliente se conecte al puerto (modo servidor)."""
        if not self._socket:
            return False
        try:
            self._socket.settimeout(timeout)
            self._conn, addr = self._socket.accept()
            self._socket.settimeout(None)
            self._is_open = True
            self._stop_event.clear()
            self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()
            return True
        except socket.timeout:
            return False
        except Exception:
            return False


class VirtualSerialPortManager:
    """Gestiona múltiples puertos COM virtuales para pruebas de integración."""

    def __init__(self):
        self._ports: Dict[str, VirtualSerialPort] = {}
        self._server_sockets: Dict[str, socket.socket] = {}

    def create_virtual_port_pair(self, name_a: str = "COM10", name_b: str = "COM11",
                                 port_a: int = 15010, port_b: int = 15011) -> tuple:
        """
        Crea un par de puertos COM virtuales conectados entre sí.
        Los datos escritos en COM10 aparecen en COM11 y viceversa.
        """
        # Crear sockets servidor para cada puerto
        server_a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_a.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_a.bind(("127.0.0.1", port_a))
        server_a.listen(1)

        server_b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_b.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_b.bind(("127.0.0.1", port_b))
        server_b.listen(1)

        # Crear puertos virtuales
        port_a_obj = VirtualSerialPort(name_a, "127.0.0.1", port_b)  # Conecta a B
        port_b_obj = VirtualSerialPort(name_b, "127.0.0.1", port_a)  # Conecta a A

        # Guardar referencias
        self._server_sockets[name_a] = server_a
        self._server_sockets[name_b] = server_b
        self._ports[name_a] = port_a_obj
        self._ports[name_b] = port_b_obj

        return port_a_obj, port_b_obj

    def get_port(self, name: str) -> Optional[VirtualSerialPort]:
        """Obtiene un puerto virtual por nombre."""
        return self._ports.get(name)

    def close_all(self) -> None:
        """Cierra todos los puertos y servidores."""
        for port in self._ports.values():
            port.close()
        for server in self._server_sockets.values():
            try:
                server.close()
            except Exception:
                pass
        self._ports.clear()
        self._server_sockets.clear()


# Instancia global del gestor de puertos virtuales
virtual_port_manager = VirtualSerialPortManager()


def create_esp32_virtual_pair(name_a: str = "COM10", name_b: str = "COM11",
                              port_a: int = 15010, port_b: int = 15011):
    """
    Crea un par de puertos virtuales listos para simular una placa ESP32.
    Retorna (puerto_pc, puerto_esp32) donde puerto_esp32 actúa como la placa.
    """
    return virtual_port_manager.create_virtual_port_pair(name_a, name_b, port_a, port_b)
