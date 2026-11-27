import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ide_app/main.dart';
import 'package:ide_app/nucleo/registro_modulos.dart';
import 'package:ide_core/ide_core.dart';

void main() {
  testWidgets(
      'Sprint 5: Monitor Serie permite filtrar por nivel/regex y exportar logs CSV',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1920, 1080);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PanelMonitorSerie(
            apiBase: 'http://127.0.0.1:59999/api/v1',
            puertoSugerido: 'VIRTUAL',
            modoSimulacion: true,
            eventosIniciales: const [
              EventoMonitorSerie(
                seq: 1,
                fecha: '2026-11-27T15:00:01.000Z',
                puerto: 'VIRTUAL',
                baudrate: 115200,
                direccion: 'RX',
                nivel: 'INFO',
                linea: 'I (100) ESP32S3: temp:26.4,hum:58.1',
              ),
              EventoMonitorSerie(
                seq: 2,
                fecha: '2026-11-27T15:00:02.000Z',
                puerto: 'VIRTUAL',
                baudrate: 115200,
                direccion: 'RX',
                nivel: 'ERROR',
                linea: 'E (200) i2c: timeout en sensor principal',
              ),
            ],
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('temp:26.4,hum:58.1'), findsOneWidget);
    expect(find.textContaining('timeout en sensor principal'), findsOneWidget);

    // Filtrar solo ERROR
    await tester.tap(find.byKey(const Key('monitor_chip_nivel_ERROR')));
    await tester.pumpAndSettle();

    expect(find.textContaining('temp:26.4,hum:58.1'), findsNothing);
    expect(find.textContaining('timeout en sensor principal'), findsOneWidget);

    // Restaurar TODOS y aplicar filtro regex
    await tester.tap(find.byKey(const Key('monitor_chip_nivel_TODOS')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('monitor_regex_input')),
      r'temp:\d+\.\d+',
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('temp:26.4,hum:58.1'), findsOneWidget);
    expect(find.textContaining('timeout en sensor principal'), findsNothing);

    // Exportar logs filtrados en CSV
    await tester.tap(find.byKey(const Key('monitor_btn_exportar')));
    await tester.pumpAndSettle();

    expect(find.text('Exportación de Logs (CSV)'), findsOneWidget);
    expect(find.textContaining('seq,fecha,puerto,baudrate'), findsOneWidget);
    await tester.tap(find.text('Cerrar'));
    await tester.pumpAndSettle();
  });

  testWidgets(
      'Sprint 5: LayoutPrincipal navega a Monitor y Plotter multicanal sin desbordes',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1920, 1080);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final registro = RegistroModulos(construirModulos());
    await tester.pumpWidget(IdeApp(registro: registro));
    await tester.pump(const Duration(milliseconds: 150));

    // Abrir Monitor Serie desde el menu Herramientas
    await tester.tap(find.text('Herramientas').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Monitor Serie'));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('monitor_btn_conectar')), findsOneWidget);
    expect(find.text('115200 baud'), findsOneWidget);

    // Navegar al Plotter Serie desde el NavigationRail
    await tester.tap(find.byIcon(Icons.show_chart).first);
    await tester.pumpAndSettle();

    expect(find.text('Plotter Serie Multicanal'), findsOneWidget);

    // Generar muestras multicanal en modo autonomo y validar canales y lienzo
    await tester.tap(find.byKey(const Key('plotter_btn_muestra')));
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('plotter_canvas')), findsOneWidget);
    expect(find.byKey(const Key('plotter_canal_temp')), findsOneWidget);
    expect(find.byKey(const Key('plotter_canal_hum')), findsOneWidget);
    expect(find.byKey(const Key('plotter_canal_volt')), findsOneWidget);
  });
}
