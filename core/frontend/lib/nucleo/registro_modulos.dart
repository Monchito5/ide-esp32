// Archivo: core/frontend/lib/nucleo/registro_modulos.dart
import 'modulo_ide.dart';

/// Registro simple en memoria de los modulos cargados.
class RegistroModulos {
  RegistroModulos(this._modulos);

  final List<ModuloIde> _modulos;

  List<ModuloIde> get modulos => List.unmodifiable(_modulos);

  ModuloIde? porId(String id) {
    for (final m in _modulos) {
      if (m.id == id) return m;
    }
    return null;
  }
}
