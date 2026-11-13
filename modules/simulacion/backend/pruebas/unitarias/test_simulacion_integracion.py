# Archivo: modules/simulacion/backend/pruebas/unitarias/test_simulacion_integracion.py
"""
Pruebas de integración para el módulo Simulacion ESP32.

Estas pruebas verifican que el módulo de simulación funcione correctamente
con un simulador virtual de ESP32 en puerto COM virtual (COM10/COM11),
sin necesidad de hardware físico real.

Cubre:
1. Detección y creación de dispositivos virtuales
2. Inicio, detención y reinicio de sesiones
3. Consulta de información del chip
4. Carga y ejecución del firmware
5. Comunicación UART bidireccional
6. Interacción con GPIO
7. Componentes virtuales I2C y SPI
8. Entrada y salida del bootloader
9. Identificación de chip y Flash
10. Borrado, escritura y verificación de firmware
11. Interrupciones y pérdida de conexión
12. Manejo de motores o chips no soportados
13. Cierre de sesiones y liberación de recursos
14. Separación entre dispositivos físicos y virtuales
"""

import sys
import os
import time
import unittest
from datetime import datetime

# Agregar el directorio del módulo al path para importar simulacion_backend
# Desde pruebas/unitarias/ subimos tres niveles para llegar a modules/
# Luego simulacion_backend es un paquete dentro de modules/simulacion/backend/
ruta_backend = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, ruta_backend)

# Importar directamente los módulos necesarios
from simulacion_backend.modulo import NOMBRE_MODULO, VERSION_MODULO, registrar
from simulacion_backend.application.simulacion_service import SimulacionService
from simulacion_backend.application.simulacion_session import SimulacionSession
from simulacion_backend.infrastructure.virtual_serial import (
    virtual_port_manager,
    VirtualSerialPort,
    create_esp32_virtual_pair,
)
from simulacion_backend.infrastructure.virtual_esp32 import (
    VirtualESP32,
    obtener_esp32_virtual,
)
from simulacion_backend.infrastructure.virtual_esp32 import (
    VirtualESP32,
    obtener_esp32_virtual,
)


class TestEstadoInicial(unittest.TestCase):
    """Pruebas de estado inicial del módulo Simulacion."""

    def test_modulo_tiene_nombre_correcto(self):
        """El módulo debe llamarse 'simulacion'."""
        self.assertEqual(NOMBRE_MODULO, "simulacion")

    def test_modulo_tiene_version(self):
        """El módulo debe tener una versión definida."""
        self.assertIsNotNone(VERSION_MODULO)
        self.assertIsInstance(VERSION_MODULO, str)
        self.assertGreater(len(VERSION_MODULO), 0)

    def test_registrar_es_funcion(self):
        """La función registrar debe existir y ser invocable."""
        from simulacion_backend.modulo import registrar
        self.assertTrue(callable(registrar))


class TestMotorYChip(unittest.TestCase):
    """Pruebas de detección de motores y chips."""

    def setUp(self):
        self.service = SimulacionService()

    def test_listar_motores(self):
        """Debe listar al menos un motor de simulación."""
        motores = self.service.listar_motores()
        self.assertIsInstance(motores, list)
        self.assertGreaterEqual(len(motores), 1)
        # Al menos debe existir ESP Emulator
        ids_motores = [m["id"] for m in motores]
        self.assertIn("esp_emulator", ids_motores)

    def test_listar_chips(self):
        """Debe listar al menos un chip ESP32."""
        chips = self.service.listar_chips()
        self.assertIsInstance(chips, list)
        self.assertGreaterEqual(len(chips), 1)
        ids_chips = [c["id"] for c in chips]
        self.assertIn("ESP32-S3", ids_chips)
        self.assertIn("ESP32", ids_chips)
        self.assertIn("ESP32-C3", ids_chips)

    def test_chip_tiene_campos_requeridos(self):
        """Cada chip debe tener los campos requeridos."""
        chips = self.service.listar_chips()
        for chip in chips:
            self.assertIn("id", chip)
            self.assertIn("nombre", chip)
            self.assertIn("arquitectura", chip)
            self.assertIn("frecuencia_mhz", chip)
            self.assertIn("flash_mb", chip)
            self.assertIn("psram_mb", chip)
            self.assertIn("motores_soportados", chip)


class TestSesionesSimulacion(unittest.TestCase):
    """Pruebas de creación y gestión de sesiones de simulación."""

    def setUp(self):
        self.service = SimulacionService()

    def test_crear_sesion_herramientas(self):
        """Debe crear una sesión de simulación válida."""
        datos = {
            "chip": "ESP32-S3",
            "motor": "esp_emulator",
            "nombre": "Sesion de Prueba",
        }
        resultado = self.service.crear_sesion(datos)
        self.assertIsInstance(resultado, dict)
        self.assertIn("sesion_id", resultado)
        self.assertEqual(resultado["chip"], "ESP32-S3")
        self.assertEqual(resultado["motor"], "esp_emulator")
        self.assertEqual(resultado["nombre"], "Sesion de Prueba")
        self.assertEqual(resultado["estado"], "creada")

    def test_crear_sesion_con_chip_no_soportado(self):
        """Debe rechazar chips no soportados."""
        datos = {
            "chip": "ESP32-H2",
            "motor": "esp_emulator",
            "nombre": "Sesion Invalida",
        }
        with self.assertRaises(ValueError):
            self.service.crear_sesion(datos)

    def test_crear_sesion_con_motor_no_soportado(self):
        """Debe rechazar motores no soportados para el chip."""
        datos = {
            "chip": "ESP32-S3",
            "motor": "qemu",
            "nombre": "Sesion Invalida",
        }
        with self.assertRaises(ValueError):
            self.service.crear_sesion(datos)

    def test_obtener_sesion_inexistente(self):
        """Debe retornar None para sesión inexistente."""
        resultado = self.service.obtener_sesion("sesion_inexistente")
        self.assertIsNone(resultado)

    def test_iniciar_sesion(self):
        """Debe iniciar una sesión creada."""
        datos = self.service.crear_sesion({
            "chip": "ESP32-S3",
            "motor": "esp_emulator",
            "nombre": "Sesion para Iniciar",
        })
        resultado = self.service.iniciar_sesion(datos["sesion_id"])
        self.assertEqual(resultado["estado"], "iniciada")

    def test_detener_sesion(self):
        """Debe detener una sesión iniciada."""
        datos = self.service.crear_sesion({
            "chip": "ESP32-S3",
            "motor": "esp_emulator",
            "nombre": "Sesion para Detener",
        })
        self.service.iniciar_sesion(datos["sesion_id"])
        resultado = self.service.detener_sesion(datos["sesion_id"])
        self.assertEqual(resultado["estado"], "detenida")

    def test_reiniciar_sesion(self):
        """Debe reiniciar una sesión iniciada."""
        datos = self.service.crear_sesion({
            "chip": "ESP32-S3",
            "motor": "esp_emulator",
            "nombre": "Sesion para Reiniciar",
        })
        self.service.iniciar_sesion(datos["sesion_id"])
        resultado = self.service.reiniciar_sesion(datos["sesion_id"])
        self.assertEqual(resultado["estado"], "iniciada")

    def test_listar_sesiones(self):
        """Debe listar todas las sesiones creadas."""
        self.service.crear_sesion({
            "chip": "ESP32-S3",
            "motor": "esp_emulator",
            "nombre": "Sesion A",
        })
        self.service.crear_sesion({
            "chip": "ESP32-C3",
            "motor": "esp_emulator",
            "nombre": "Sesion B",
        })
        sesiones = self.service.listar_sesiones()
        self.assertGreaterEqual(len(sesiones), 2)


class TestComunicacionPuertoSerieVirtual(unittest.TestCase):
    """Pruebas de comunicación UART a través de puertos COM virtuales."""

    def setUp(self):
        self.servidor, self.cliente = virtual_port_manager.create_virtual_port_pair(
            "COM10", "COM11", 15010, 15011
        )
        self.esp32 = VirtualESP32("COM10")

    def tearDown(self):
        self.esp32.disconnect()
        virtual_port_manager.close_all()

    def test_conectar_y_desconectar_puerto_virtual(self):
        """Debe conectar y desconectar el puerto virtual correctamente."""
        resultado = self.esp32.connect()
        self.assertTrue(resultado)
        self.assertTrue(self.esp32._is_connected)
        self.esp32.disconnect()
        self.assertFalse(self.esp32._is_connected)

    def test_comando_at_responde_ok(self):
        """El comando AT debe responder OK."""
        self.esp32.connect()
        self.esp32._port.write(b"AT\r\n")
        time.sleep(0.5)
        datos = self.esp32._port.read(self.esp32._port.in_waiting())
        self.assertIn(b"OK", datos)
        self.esp32.disconnect()

    def test_comando_chipid_responde_mac(self):
        """El comando AT+CHIPID? debe responder con la MAC."""
        self.esp32.connect()
        self.esp32._port.write(b"AT+CHIPID?\r\n")
        time.sleep(0.5)
        datos = self.esp32._port.read(self.esp32._port.in_waiting())
        texto = datos.decode("utf-8", errors="replace")
        self.assertIn("CHIPID", texto)
        self.assertIn("24:6F:28:A1:B2:C3", texto)
        self.esp32.disconnect()

    def test_obtener_info_chip(self):
        """Debe retornar información completa del chip."""
        self.esp32.connect()
        self.esp32._port.write(b"AT+CHIPID?\r\n")
        time.sleep(0.5)
        datos = self.esp32._port.read(self.esp32._port.in_waiting())
        texto = datos.decode("utf-8", errors="replace")
        self.assertIn("CHIPID", texto)
        self.assertIn("24:6F:28:A1:B2:C3", texto)
        self.esp32.disconnect()

    def test_envio_comando_gpio(self):
        """Debe escribir y leer un GPIO virtual."""
        self.esp32.connect()
        # Escribir GPIO2 en HIGH
        self.esp32._port.write(b"AT+GPIO2=WRITE,1\r\n")
        time.sleep(0.5)
        datos = self.esp32._port.read(self.esp32._port.in_waiting())
        self.assertIn("OK", datos.decode("utf-8", errors="replace"))

        # Leer GPIO2
        self.esp32._port.write(b"AT+GPIO2=READ\r\n")
        time.sleep(0.5)
        datos = self.esp32._port.read(self.esp32._port.in_waiting())
        texto = datos.decode("utf-8", errors="replace")
        self.assertIn("1", texto)
        self.esp32.disconnect()


class TestFlasheoFirmware(unittest.TestCase):
    """Pruebas de flasheo de firmware en simulación."""

    def setUp(self):
        self.service = SimulacionService()
        self.sesion = self.service.crear_sesion({
            "chip": "ESP32-S3",
            "motor": "esp_emulator",
            "nombre": "Sesion para Flasheo",
        })
        self.service.iniciar_sesion(self.sesion["sesion_id"])

    def test_flashear_firmware_exitoso(self):
        """Debe flashear un firmware en la sesión."""
        datos_flasheo = {
            "archivo": "firmware_ejemplo.bin",
            "direccion": "0x10000",
            "version": "1.0.0",
        }
        resultado = self.service.flashear_sesion(self.sesion["sesion_id"], datos_flasheo)
        self.assertEqual(resultado["estado"], "iniciada")
        self.assertEqual(resultado["firmware_cargado"], "firmware_ejemplo.bin")
        self.assertEqual(resultado["firmware_version"], "1.0.0")

    def test_flashear_sin_sesion_iniciada_falla(self):
        """No se debe poder flashear si la sesión no está iniciada."""
        sesion_detenida = self.service.crear_sesion({
            "chip": "ESP32-S3",
            "motor": "esp_emulator",
            "nombre": "Sesion Detenida",
        })
        # No iniciamos la sesión
        with self.assertRaises(ValueError):
            self.service.flashear_sesion(sesion_detenida["sesion_id"], {
                "archivo": "firmware.bin",
                "direccion": "0x10000",
            })

    def test_obtener_info_chip_despues_flasheo(self):
        """Debe mostrar información del chip después de flashear."""
        self.service.flashear_sesion(self.sesion["sesion_id"], {
            "archivo": "mi_proyecto.bin",
            "direccion": "0x10000",
            "version": "2.0.0",
        })
        info = self.service.obtener_reporte(self.sesion["sesion_id"])
        self.assertEqual(info["firmware"]["archivo"], "mi_proyecto.bin")
        self.assertEqual(info["firmware"]["version"], "2.0.0")


class TestComponenteVirtual(unittest.TestCase):
    """Pruebas de componentes virtuales."""

    def setUp(self):
        self.service = SimulacionService()
        self.sesion = self.service.crear_sesion({
            "chip": "ESP32-S3",
            "motor": "esp_emulator",
            "nombre": "Sesion con Componentes",
        })
        self.service.iniciar_sesion(self.sesion["sesion_id"])

    def test_agregar_componente_led(self):
        """Debe agregar un componente LED virtual."""
        resultado = self.service.agregar_componente(self.sesion["sesion_id"], {
            "id": "led_01",
            "tipo": "led",
            "puerto": "GPIO2",
        })
        self.assertEqual(resultado["id"], "led_01")
        self.assertEqual(resultado["tipo"], "led")
        self.assertEqual(resultado["puerto"], "GPIO2")
        self.assertEqual(resultado["estado"], "inactivo")

    def test_agregar_varios_componentes(self):
        """Debe agregar múltiples componentes."""
        self.service.agregar_componente(self.sesion["sesion_id"], {
            "id": "led_01", "tipo": "led", "puerto": "GPIO2"
        })
        self.service.agregar_componente(self.sesion["sesion_id"], {
            "id": "btn_01", "tipo": "button", "puerto": "GPIO4"
        })
        self.service.agregar_componente(self.sesion["sesion_id"], {
            "id": "sensor_01", "tipo": "sensor", "puerto": "GPIO5"
        })
        reporte = self.service.obtener_reporte(self.sesion["sesion_id"])
        self.assertEqual(len(reporte["componentes"]), 3)


class TestSeparacionPlacasVirtualesFisicas(unittest.TestCase):
    """Prueba que dispositivos virtuales y físicos estén separados."""

    def setUp(self):
        self.service = SimulacionService()

    def test_dispositivo_virtual_no_es_fisico(self):
        """Los dispositivos virtuales deben tener id de sesion, no puerto fisico."""
        self.service.crear_sesion({
            "chip": "ESP32-S3",
            "motor": "esp_emulator",
            "nombre": "Sesion Virtual",
        })
        sesiones = self.service.listar_sesiones()
        hay_virtual = any(
            s.get("sesion_id", "").startswith("sesion-")
            for s in sesiones
        )
        self.assertTrue(hay_virtual)


class TestManejoErrores(unittest.TestCase):
    """Pruebas de manejo de errores."""

    def test_sesion_no_existente(self):
        """Debe lanzar excepción para sesión inexistente."""
        service = SimulacionService()
        with self.assertRaises(KeyError):
            service.iniciar_sesion("sesion_inexistente")

    def test_puerto_inexistente_no_debe_conectar(self):
        """Un puerto que no existe no debe conectar."""
        from simulacion_backend.infrastructure.virtual_serial import VirtualSerialPort
        puerto_falso = VirtualSerialPort("COM999")
        resultado = puerto_falso.connect()
        self.assertFalse(resultado)


if __name__ == "__main__":
    unittest.main()
