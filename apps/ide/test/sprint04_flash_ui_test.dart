import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ide_app/main.dart';
import 'package:ide_app/nucleo/registro_modulos.dart';
import 'package:ide_core/ide_core.dart';

void main() {
  testWidgets(
      'Sprint 4: El menu Herramientas abre Editor de Particiones, Certificados SSL y Flasheo Completo',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1920, 1080);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final registro = RegistroModulos(construirModulos());
    await tester.pumpWidget(IdeApp(registro: registro));
    await tester.pump(const Duration(milliseconds: 150));

    // 1. Abrir menu Herramientas -> Tabla de Particiones
    await tester.tap(find.text('Herramientas').first);
    await tester.pumpAndSettle();

    expect(find.text('Grabar Bootloader'), findsOneWidget);
    expect(find.text('Tabla de Particiones'), findsOneWidget);
    expect(find.text('Certificados SSL (NVS)'), findsOneWidget);
    expect(find.text('Flasheo Completo'), findsOneWidget);

    await tester.tap(find.text('Tabla de Particiones'));
    await tester.pumpAndSettle();

    expect(
      find.text('Editor de Tabla de Particiones ESP-IDF (0x8000)'),
      findsOneWidget,
    );
    await tester.tap(find.text('Cerrar'));
    await tester.pumpAndSettle();

    // 2. Abrir Certificados SSL (NVS)
    await tester.tap(find.text('Herramientas').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Certificados SSL (NVS)'));
    await tester.pumpAndSettle();

    expect(
      find.text('Certificados SSL/TLS en Partición NVS'),
      findsOneWidget,
    );
    await tester.tap(find.text('Cancelar'));
    await tester.pumpAndSettle();

    // 3. Abrir Wizard de Flasheo Completo
    await tester.tap(find.text('Herramientas').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Flasheo Completo'));
    await tester.pumpAndSettle();

    expect(
      find.textContaining('Flasheo Completo Orquestado'),
      findsOneWidget,
    );
    await tester.tap(find.text('Cancelar'));
    await tester.pumpAndSettle();
  });
}
