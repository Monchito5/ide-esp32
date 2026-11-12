import 'package:flutter_test/flutter_test.dart';
import 'package:ide_core/ide_core.dart';

void main() {
  test('RegistroModulos arranca vacio', () {
    final registro = RegistroModulos([]);
    expect(registro.modulos, isEmpty);
  });
}
