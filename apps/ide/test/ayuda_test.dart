import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ide_app/main.dart';
import 'package:ide_app/nucleo/registro_modulos.dart';
import 'package:ide_core/ide_core.dart';

void main() {
  testWidgets('El menu Ayuda abre la ventana Acerca de', (tester) async {
    tester.view.physicalSize = const Size(1920, 1080);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final registro = RegistroModulos(construirModulos());
    await tester.pumpWidget(IdeApp(registro: registro));
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.text('Ayuda').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Acerca de'));
    await tester.pumpAndSettle();

    expect(find.text('Acerca de ESP32 IDE'), findsWidgets);
    expect(find.textContaining('1.0.0-beta'), findsWidgets);

    await tester.tap(find.text('Cerrar'));
    await tester.pumpAndSettle();
    expect(find.text('Acerca de ESP32 IDE'), findsNothing);
  });
}
