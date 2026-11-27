import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ide_app/main.dart';
import 'package:ide_app/nucleo/registro_modulos.dart';
import 'package:ide_core/ide_core.dart';

void main() {
  testWidgets('IDE app smoke test', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1920, 1080);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final registro = RegistroModulos(construirModulos());
    await tester.pumpWidget(IdeApp(registro: registro));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Herramientas'), findsWidgets);
    expect(find.text('Ayuda'), findsWidgets);
  });
}
