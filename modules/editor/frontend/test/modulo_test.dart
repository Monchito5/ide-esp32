// Archivo: modules/editor/frontend/test/modulo_test.dart
import 'package:editor_ui/editor_ui.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('ModuloEditor - Contrato e Identificación', () {
    test('expone id, nombre e icono correctos', () {
      final m = ModuloEditor();
      expect(m.id, 'editor');
      expect(m.nombre, 'Editor');
    });
  });

  group('EditManager - Pruebas Unitarias de Edición', () {
    late CppSyntaxHighlighterController controller;
    late EditManager editManager;

    setUp(() {
      controller = CppSyntaxHighlighterController(text: 'int led = 2;\nvoid setup() {}');
      editManager = EditManager(controller: controller);
    });

    test('TC-001 / REQ-001: Undo revierte la última modificación', () {
      editManager.registrarCambio();
      controller.text = 'int led = 4;\nvoid setup() {}';

      expect(editManager.canUndo(), isTrue);
      editManager.undo();
      expect(controller.text, 'int led = 2;\nvoid setup() {}');
    });

    test('TC-002 / REQ-002: Redo recupera el cambio deshecho', () {
      editManager.registrarCambio();
      controller.text = 'int led = 10;';
      editManager.undo();
      expect(controller.text, 'int led = 2;\nvoid setup() {}');

      expect(editManager.canRedo(), isTrue);
      editManager.redo();
      expect(controller.text, 'int led = 10;');
    });

    test('TC-009, TC-010 / REQ-010: Comment y Uncomment alternan //', () {
      controller.text = 'digitalWrite(LED, HIGH);';
      controller.selection = const TextSelection(baseOffset: 0, extentOffset: 24);

      // Comentar
      editManager.toggleComment();
      expect(controller.text.startsWith('//'), isTrue);

      // Descomentar
      editManager.toggleComment();
      expect(controller.text, 'digitalWrite(LED, HIGH);');
    });

    test('TC-011, TC-012 / REQ-011, REQ-012: Increase y Decrease Indent', () {
      controller.text = 'linea1\nlinea2';
      controller.selection = const TextSelection(baseOffset: 0, extentOffset: 12);

      // Aumentar sangría (+2 espacios)
      editManager.increaseIndent();
      expect(controller.text, '  linea1\n  linea2');

      // Disminuir sangría (-2 espacios)
      editManager.decreaseIndent();
      expect(controller.text, 'linea1\nlinea2');
    });

    test('TC-007, TC-024 / REQ-008, REQ-022: Go to Line con límites', () {
      controller.text = 'linea1\nlinea2\nlinea3';

      expect(editManager.goToLine(2), isTrue);
      expect(editManager.goToLine(0), isFalse); // Fuera de rango inferior
      expect(editManager.goToLine(5), isFalse); // Fuera de rango superior
    });

    test('TC-013 / REQ-013: Auto Format aplica indentación por llaves', () {
      controller.text = 'void loop(){\ndigitalWrite(LED, HIGH);\n}';
      editManager.autoFormatLocal();

      expect(controller.text.contains('  digitalWrite(LED, HIGH);'), isTrue);
    });
  });

  group('SearchManager - Pruebas de Búsqueda', () {
    late CppSyntaxHighlighterController controller;
    late SearchManager searchManager;

    setUp(() {
      controller = CppSyntaxHighlighterController(text: 'Serial.print("hola"); Serial.println("hola");');
      searchManager = SearchManager(controller: controller);
    });

    test('TC-014 / REQ-004: Encuentra todas las coincidencias', () {
      searchManager.buscar('Serial');
      expect(searchManager.totalCoincidencias, 2);
      expect(searchManager.indiceActual, 0);
    });

    test('TC-015, TC-016 / REQ-014, REQ-015: Find Next y Find Previous circulan', () {
      searchManager.buscar('Serial');
      expect(searchManager.indiceActual, 0);

      searchManager.findNext();
      expect(searchManager.indiceActual, 1);

      searchManager.findNext(); // Debe regresar al primero
      expect(searchManager.indiceActual, 0);

      searchManager.findPrevious(); // Debe ir al último
      expect(searchManager.indiceActual, 1);
    });

    test('Reemplazo simple y Reemplazo total', () {
      searchManager.buscar('Serial');
      searchManager.replaceAll('MiSerial');
      expect(controller.text.contains('MiSerial'), isTrue);
      expect(controller.text.contains('Serial.'), isFalse);
    });
  });

  group('EditorState - Control de Fuente y Zoom', () {
    test('TC-019, TC-020 / REQ-018, REQ-019: Ajuste visual de tamaño de fuente', () {
      final state = EditorState();
      final double inicial = state.tamanioFuente;

      state.increaseFontSize();
      expect(state.tamanioFuente, inicial + 2.0);

      state.decreaseFontSize();
      expect(state.tamanioFuente, inicial);

      // Respetar límite mínimo
      for (int i = 0; i < 20; i++) {
        state.decreaseFontSize();
      }
      expect(state.tamanioFuente, EditorState.tamanioMinimo);

      // Respetar límite máximo
      for (int i = 0; i < 30; i++) {
        state.increaseFontSize();
      }
      expect(state.tamanioFuente, EditorState.tamanioMaximo);
    });
  });
}
