import 'package:flutter_test/flutter_test.dart';
import 'package:ide_app/main.dart';
import 'package:ide_app/nucleo/registro_modulos.dart';
import 'package:ide_core/ide_core.dart';

void main() {
  testWidgets(
      'El IDE arranca con modulos y muestra texto real en LayoutPrincipal',
      (tester) async {
    final registro = RegistroModulos(construirModulos());
    await tester.pumpWidget(IdeApp(registro: registro));
    expect(find.text('Herramientas'), findsWidgets);
    expect(find.text('Verificando backend...'), findsOneWidget);
  });
}
