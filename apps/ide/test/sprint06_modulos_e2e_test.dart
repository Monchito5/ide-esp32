import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ide_app/main.dart';
import 'package:ide_app/nucleo/registro_modulos.dart';
import 'package:ide_core/ide_core.dart';

void main() {
  testWidgets(
      'Sprint 6 (S6-08): construirModulos registra los 7 modulos frontend y renderiza sus vistas',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1920, 1080);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final modulos = construirModulos();
    final ids = modulos.map((m) => m.id).toSet();
    expect(
      ids,
      containsAll(<String>{
        'archivo',
        'editor',
        'sketch',
        'herramientas',
        'menu-log',
        'ayuda',
        'simulacion',
      }),
    );

    // Renderizar vistas individuales de Sketch y Menu-Log sin crash
    for (final idObjetivo in <String>['sketch', 'menu-log']) {
      final modulo = modulos.firstWhere((m) => m.id == idObjetivo);
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(builder: (ctx) => modulo.construirVista(ctx)),
          ),
        ),
      );
      await tester.pump(const Duration(milliseconds: 100));
    }

    // Desmontar cualquier Timer periodico (ej. PanelMenuLog) antes de cerrar
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
  });

  testWidgets(
      'Sprint 6 (S6-11): Smoke test completo de navegacion por destinos del IDE sin errores',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1920, 1080);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final registro = RegistroModulos(construirModulos());
    await tester.pumpWidget(IdeApp(registro: registro));
    await tester.pump(const Duration(milliseconds: 150));

    // 1. Destino Sketch (por defecto)
    expect(find.textContaining('app_main'), findsOneWidget);

    // 2. Cambiar modo Físico <-> Simulación
    await tester.tap(find.text('Modo Físico'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Modo Simulación').last);
    await tester.pumpAndSettle();
    expect(find.text('Simulación'), findsOneWidget);

    // 3. Navegar a Monitor Serie
    await tester.tap(find.byIcon(Icons.computer).first);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('monitor_btn_conectar')), findsOneWidget);

    // 4. Navegar a Plotter Serie
    await tester.tap(find.byIcon(Icons.show_chart).first);
    await tester.pumpAndSettle();
    expect(find.text('Plotter Serie Multicanal'), findsOneWidget);

    // 5. Volver a Sketch
    await tester.tap(find.byIcon(Icons.code).first);
    await tester.pumpAndSettle();
    expect(find.textContaining('app_main'), findsOneWidget);
  });
}
