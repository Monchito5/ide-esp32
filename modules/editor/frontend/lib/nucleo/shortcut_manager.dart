// Archivo: modules/editor/frontend/lib/nucleo/shortcut_manager.dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'editor_state.dart';

/// Intentos para acciones del editor.
class DeshacerIntent extends Intent {
  const DeshacerIntent();
}

class RehacerIntent extends Intent {
  const RehacerIntent();
}

class CortarIntent extends Intent {
  const CortarIntent();
}

class CopiarIntent extends Intent {
  const CopiarIntent();
}

class PegarIntent extends Intent {
  const PegarIntent();
}

class SeleccionarTodoIntent extends Intent {
  const SeleccionarTodoIntent();
}

class BuscarIntent extends Intent {
  const BuscarIntent();
}

class BuscarSiguienteIntent extends Intent {
  const BuscarSiguienteIntent();
}

class BuscarAnteriorIntent extends Intent {
  const BuscarAnteriorIntent();
}

class IrALineaIntent extends Intent {
  const IrALineaIntent();
}

class ComentarIntent extends Intent {
  const ComentarIntent();
}

class AumentarSangriaIntent extends Intent {
  const AumentarSangriaIntent();
}

class DisminuirSangriaIntent extends Intent {
  const DisminuirSangriaIntent();
}

class FormatearIntent extends Intent {
  const FormatearIntent();
}

class AumentarFuenteIntent extends Intent {
  const AumentarFuenteIntent();
}

class DisminuirFuenteIntent extends Intent {
  const DisminuirFuenteIntent();
}

/// Envoltorio que vincula atajos de teclado con las operaciones del editor.
///
/// Responsabilidad asignada a Dev C (Nathaniel).
/// Garantiza REQ-020 (Shortcuts) y REQ-021 (Consistencia menú/atajo).
class EditorShortcutWrapper extends StatelessWidget {
  const EditorShortcutWrapper({
    super.key,
    required this.editorState,
    required this.onGoToLineRequested,
    required this.child,
  });

  final EditorState editorState;
  final VoidCallback onGoToLineRequested;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final em = editorState.editManager;
    final sm = editorState.searchManager;

    return Shortcuts(
      shortcuts: <ShortcutActivator, Intent>{
        // Ctrl+Z: Undo
        const SingleActivator(LogicalKeyboardKey.keyZ, control: true):
            const DeshacerIntent(),
        // Ctrl+Y: Redo
        const SingleActivator(LogicalKeyboardKey.keyY, control: true):
            const RehacerIntent(),
        // Ctrl+Shift+Z: Redo alternativo
        const SingleActivator(LogicalKeyboardKey.keyZ, control: true, shift: true):
            const RehacerIntent(),
        // Ctrl+X: Cut
        const SingleActivator(LogicalKeyboardKey.keyX, control: true):
            const CortarIntent(),
        // Ctrl+C: Copy
        const SingleActivator(LogicalKeyboardKey.keyC, control: true):
            const CopiarIntent(),
        // Ctrl+V: Paste
        const SingleActivator(LogicalKeyboardKey.keyV, control: true):
            const PegarIntent(),
        // Ctrl+A: Select All
        const SingleActivator(LogicalKeyboardKey.keyA, control: true):
            const SeleccionarTodoIntent(),
        // Ctrl+F: Find
        const SingleActivator(LogicalKeyboardKey.keyF, control: true):
            const BuscarIntent(),
        // F3: Find Next
        const SingleActivator(LogicalKeyboardKey.f3):
            const BuscarSiguienteIntent(),
        // Shift+F3: Find Previous
        const SingleActivator(LogicalKeyboardKey.f3, shift: true):
            const BuscarAnteriorIntent(),
        // Ctrl+G: Go to Line
        const SingleActivator(LogicalKeyboardKey.keyG, control: true):
            const IrALineaIntent(),
        // Ctrl+/: Comment / Uncomment
        const SingleActivator(LogicalKeyboardKey.slash, control: true):
            const ComentarIntent(),
        // Ctrl+]: Increase Indent
        const SingleActivator(LogicalKeyboardKey.bracketRight, control: true):
            const AumentarSangriaIntent(),
        // Ctrl+[: Decrease Indent
        const SingleActivator(LogicalKeyboardKey.bracketLeft, control: true):
            const DisminuirSangriaIntent(),
        // Shift+Alt+F: Auto Format
        const SingleActivator(LogicalKeyboardKey.keyF, alt: true, shift: true):
            const FormatearIntent(),
        // Ctrl+= / Ctrl++: Increase Font Size
        const SingleActivator(LogicalKeyboardKey.equal, control: true):
            const AumentarFuenteIntent(),
        // Ctrl+-: Decrease Font Size
        const SingleActivator(LogicalKeyboardKey.minus, control: true):
            const DisminuirFuenteIntent(),
      },
      child: Actions(
        actions: <Type, Action<Intent>>{
          DeshacerIntent: CallbackAction<DeshacerIntent>(onInvoke: (_) => em.undo()),
          RehacerIntent: CallbackAction<RehacerIntent>(onInvoke: (_) => em.redo()),
          CortarIntent: CallbackAction<CortarIntent>(onInvoke: (_) => em.cut()),
          CopiarIntent: CallbackAction<CopiarIntent>(onInvoke: (_) => em.copy()),
          PegarIntent: CallbackAction<PegarIntent>(onInvoke: (_) => em.paste()),
          SeleccionarTodoIntent: CallbackAction<SeleccionarTodoIntent>(onInvoke: (_) => em.selectAll()),
          BuscarIntent: CallbackAction<BuscarIntent>(onInvoke: (_) => sm.useSelectionForFind()),
          BuscarSiguienteIntent: CallbackAction<BuscarSiguienteIntent>(onInvoke: (_) => sm.findNext()),
          BuscarAnteriorIntent: CallbackAction<BuscarAnteriorIntent>(onInvoke: (_) => sm.findPrevious()),
          IrALineaIntent: CallbackAction<IrALineaIntent>(onInvoke: (_) => onGoToLineRequested()),
          ComentarIntent: CallbackAction<ComentarIntent>(onInvoke: (_) => em.toggleComment()),
          AumentarSangriaIntent: CallbackAction<AumentarSangriaIntent>(onInvoke: (_) => em.increaseIndent()),
          DisminuirSangriaIntent: CallbackAction<DisminuirSangriaIntent>(onInvoke: (_) => em.decreaseIndent()),
          FormatearIntent: CallbackAction<FormatearIntent>(onInvoke: (_) => em.autoFormatLocal()),
          AumentarFuenteIntent: CallbackAction<AumentarFuenteIntent>(onInvoke: (_) => editorState.increaseFontSize()),
          DisminuirFuenteIntent: CallbackAction<DisminuirFuenteIntent>(onInvoke: (_) => editorState.decreaseFontSize()),
        },
        child: child,
      ),
    );
  }
}
