// Archivo: modules/editor/frontend/lib/modulo_editor.dart
import 'package:flutter/material.dart';
import 'package:ide_core/ide_core.dart';

import 'nucleo/editor_state.dart';
import 'servicios/api_editor.dart';
import 'ui/vistas/vista_editor.dart';

/// Implementacion del contrato ModuloIde para el modulo Editor (Equipo Rojo).
class ModuloEditor implements ModuloIde {
  ModuloEditor({EditorState? estado, ApiEditor? api})
      : _estado = estado ?? EditorState(),
        _api = api ?? ApiEditor();

  final EditorState _estado;
  final ApiEditor _api;

  @override
  String get id => 'editor';

  @override
  String get nombre => 'Editor';

  @override
  IconData get icono => Icons.code;

  @override
  Widget construirVista(BuildContext context) =>
      VistaEditor(editorState: _estado, api: _api);
}
