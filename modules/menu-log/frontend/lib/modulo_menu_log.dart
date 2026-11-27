import 'package:flutter/material.dart';
import 'package:ide_core/ide_core.dart';

import 'panel_menu_log.dart';

/// Implementacion del contrato ModuloIde para el modulo Menu-Log.
class ModuloMenuLog implements ModuloIde {
  ModuloMenuLog({Uri? apiBase})
    : _apiBase = apiBase ?? Uri.parse('http://127.0.0.1:8765/');

  final Uri _apiBase;

  @override
  String get id => 'menu-log';

  @override
  String get nombre => 'Menú y Log';

  @override
  IconData get icono => Icons.receipt_long;

  @override
  Widget construirVista(BuildContext context) {
    return PanelMenuLog(apiBase: _apiBase);
  }
}
