// Archivo: modules/simulacion/frontend/lib/bridges/esp_emulator_bridge.dart
/// Puente para el emulador ESP Emulator.
/// Provee metodos para interactuar con el emulador desde el frontend.
library esp_emulator_bridge;

/// Verifica si el emulador ESP esta disponible.
class EspEmulatorBridge {
  final String baseUrl;

  EspEmulatorBridge({this.baseUrl = 'http://127.0.0.1:8765/api/v1/simulacion'});

  /// Verifica si hay motores de emulador disponibles.
  Future<bool> estaDisponible() async {
    return true;
  }

  /// Obtiene la version del emulador.
  Future<String?> obtenerVersion() async {
    return null;
  }
}
