import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ide_app/main.dart';
import 'package:ide_app/nucleo/registro_modulos.dart';
import 'package:ide_core/ide_core.dart';

void main() {
  testWidgets(
      'Sprint 3: El IDE carga plantilla nativa ESP-IDF (app_main) y permite seleccionar ESP32-C3',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1920, 1080);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final registro = RegistroModulos(construirModulos());
    await tester.pumpWidget(IdeApp(registro: registro));
    await tester.pump(const Duration(milliseconds: 150));

    // Verifica que la barra de estado muestre el perfil Espressif por defecto (ESP32-S3 DevKitC-1)
    expect(find.textContaining('ESP32-S3 DevKitC-1 (esp32s3)'), findsOneWidget);

    // Verifica que el editor use codigo nativo de ESP-IDF (app_main) y no setup/loop
    expect(find.textContaining('void app_main(void)'), findsOneWidget);

    // Abre el selector de Placas desde el NavigationRail y elige ESP32-C3 DevKitM-1
    await tester.tap(find.text('Placas'));
    await tester.pumpAndSettle();

    expect(find.text('ESP32-C3 DevKitM-1'), findsOneWidget);
    await tester.tap(find.text('ESP32-C3 DevKitM-1'));
    await tester.pumpAndSettle();

    // Confirma que el target ESP-IDF cambio a esp32c3
    expect(find.textContaining('ESP32-C3 DevKitM-1 (esp32c3)'), findsOneWidget);
    expect(find.text('SALIDA ESP-IDF (ESP32C3)'), findsOneWidget);
  });
}
