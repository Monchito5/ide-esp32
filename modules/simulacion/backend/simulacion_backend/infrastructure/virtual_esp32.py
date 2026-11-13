# Archivo: modules/simulacion/backend/simulacion_backend/infrastructure/virtual_esp32.py
"""
Simulador de placa ESP32 virtual sobre puerto COM virtual.

Implementa un ESP32 virtual que responde a comandos AT/ESP simples a través
de un puerto serie virtual (COM10/COM11), permitiendo pruebas de integración
sin hardware físico real.
"""

import threading
import time
import json
from typing import Optional, Dict, List, Callable
from .virtual_serial import VirtualSerialPort


class VirtualESP32:
    """
    Simula una placa ESP32 conectada a un puerto COM virtual.
    Responde a comandos AT básicos y permite simular GPIO, UART y flasheo.
    """

    def __init__(self, port_name: str = "COM10", baudrate: int = 115200):
        self.port_name = port_name
        self.baudrate = baudrate
        self._port: Optional[VirtualSerialPort] = None
        self._is_connected = False
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Estado del dispositivo virtual
        self.chip_id = "ESP32-S3-DEVKITC-1"
        self.chip_revision = "v1.2"
        self.flash_size_mb = 16
        self.psram_mb = 8
        self.mac_address = "24:6F:28:A1:B2:C3"
        self.firmware_version = "1.0.0"
        self.firmware_loaded = False
        self.gpio_pins: Dict[int, bool] = {i: False for i in range(0, 48)}
        self.uart_rx_buffer: List[str] = []
        self.uart_tx_buffer: List[str] = []
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Conecta al puerto virtual."""
        if self._is_connected:
            return True

        self._port = VirtualSerialPort(self.port_name, baudrate=self.baudrate)
        try:
            self._port.open(baudrate=self.baudrate)
            self._is_connected = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            return True
        except Exception:
            self._is_connected = False
            return False

    def disconnect(self) -> None:
        """Desconecta del puerto virtual."""
        self._stop_event.set()
        self._is_running = False
        if self._port:
            self._port.close()
        self._is_connected = False

    def _read_loop(self) -> None:
        """Bucle de lectura del puerto serial virtual."""
        while not self._stop_event.is_set() and self._is_connected:
            try:
                if self._port and self._port.in_waiting() > 0:
                    data = self._port.read(self._port.in_waiting())
                    if data:
                        self._process_uart_data(data)
                else:
                    time.sleep(0.01)
            except Exception:
                break

    def _process_uart_data(self, data: bytes) -> None:
        """Procesa datos recibidos por UART virtual."""
        try:
            text = data.decode("utf-8", errors="replace").strip()
            if not text:
                return

            self.uart_rx_buffer.append(text)
            response = self._process_command(text)
            if response:
                self.send_uart(response + "\r\n")
        except Exception:
            pass

    def _process_command(self, command: str) -> str:
        """Procesa un comando AT/ESP y retorna la respuesta."""
        cmd = command.strip().upper()

        if cmd == "AT":
            return "OK"
        elif cmd == "AT+GMR":
            return f"ESP32-S3 DevKitC-1\nChip: {self.chip_id}\nRevision: {self.chip_revision}\nFirmware: {self.firmware_version}\nOK"
        elif cmd == "AT+CHIPID?":
            return f"+CHIPID:{self.mac_address}\nOK"
        elif cmd == "AT+FLASHINFO?":
            return f"+FLASH:{self.flash_size_mb}MB\n+PSRAM:{self.psram_mb}MB\nOK"
        elif cmd.startswith("AT+GPIO"):
            return self._handle_gpio_command(cmd)
        elif cmd.startswith("AT+FLASH"):
            return self._handle_flash_command(cmd)
        elif cmd == "AT+REBOOT":
            self.firmware_loaded = False
            self.gpio_pins = {i: False for i in range(0, 48)}
            return "OK"
        else:
            return "ERROR"

    def _handle_gpio_command(self, cmd: str) -> str:
        """Procesa comandos de GPIO."""
        parts = cmd.split()
        if len(parts) < 3:
            return "ERROR"

        gpio_num = int(parts[1].replace("GPIO", "")) if parts[1].startswith("GPIO") else int(parts[1])

        if parts[2] == "READ":
            val = self.gpio_pins.get(gpio_num, False)
            return f"+GPIO{self.gpio_pins.get(gpio_num, False)}\nOK"
        elif parts[2] == "WRITE":
            if len(parts) >= 4:
                val = parts[3].upper() in ("1", "HIGH", "TRUE")
                self.gpio_pins[gpio_num] = val
                return "OK"
            return "ERROR"
        return "ERROR"

    def _handle_flash_command(self, cmd: str) -> str:
        """Procesa comandos de flasheo."""
        if "WRITE" in cmd:
            self.firmware_loaded = True
            self._agregar_evento("flasheo", "Firmware cargado en ESP32 virtual")
            return "OK"
        elif "ERASE" in cmd:
            self.firmware_loaded = False
            self._agregar_evento("flasheo", "Flash borrado")
            return "OK"
        elif "READ" in cmd:
            return f"+FW:{self.firmware_cargado or 'NINGUNO'}\nOK"
        return "ERROR"

    def _agregar_evento(self, tipo: str, mensaje: str, datos: dict = None) -> None:
        """Agrega un evento al historial de la sesión."""
        evento = {
            "tipo": tipo,
            "mensaje": mensaje,
            "timestamp": datetime.now().isoformat(),
            "datos": datos or {},
        }
        if not hasattr(self, '_eventos'):
            self._eventos = []
        self._eventos.append(evento)
        if len(self._eventos) > 100:
            self._eventos = self._eventos[-100:]

    def send_uart(self, data: str) -> None:
        """Envía datos por UART virtual."""
        if self._port and self._is_connected:
            try:
                self._port.write(data.encode("utf-8"))
            except Exception:
                pass

    def simular_lectura_sensor(self, sensor_id: str, valor: float) -> None:
        """Simula la lectura de un sensor y la envía por UART."""
        mensaje = f"SENSOR:{sensor_id}:{valor:.2f}"
        self.send_uart(mensaje + "\r\n")

    def get_estado(self) -> dict:
        """Retorna el estado actual de la placa virtual."""
        return {
            "sesion_id": self.sesion_id if hasattr(self, 'sesion_id') else "desconocido",
            "chip": self.chip_id,
            "revision": self.chip_revision,
            "estado": "iniciada" if self._is_connected else "detenida",
            "firmware_cargado": self.firmware_cargado,
            "firmware_version": self.firmware_version,
            "mac": self.mac_address,
            "flash_mb": self.flash_size_mb,
            "psram_mb": self.psram_mb,
            "gpio": {str(k): v for k, v in self.gpio_pins.items() if v},
            "uart_tx": self.uart_tx_buffer[-10:] if self.uart_tx_buffer else [],
            "uart_rx": self.uart_rx_buffer[-10:] if self.uart_rx_buffer else [],
        }


# Instancia global del simulador ESP32
esp32_virtual = VirtualESP32("COM10")


def obtener_esp32_virtual() -> VirtualESP32:
    """Retorna la instancia del ESP32 virtual."""
    return esp32_virtual
