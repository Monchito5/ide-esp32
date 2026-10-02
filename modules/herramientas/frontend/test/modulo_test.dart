import 'package:flutter_test/flutter_test.dart';
import 'package:herramientas_ui/herramientas_ui.dart';

void main() {
  test('ModuloHerramientas expone id correcto', () {
    final m = ModuloHerramientas();
    expect(m.id, 'herramientas');
    expect(m.nombre, 'Herramientas');
  });
}
