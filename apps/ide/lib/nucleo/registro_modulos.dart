// Archivo: apps/ide/lib/nucleo/registro_modulos.dart
//
// PUNTO CENTRAL donde se declaran los modulos activos del IDE.
// Cada equipo agrega aqui su modulo importandolo desde modules/.

import 'package:herramientas_ui/herramientas_ui.dart';
import 'package:ide_core/ide_core.dart';

/// Devuelve la lista de modulos activos del IDE.
///
/// Para agregar un nuevo modulo:
///   1. Importar su paquete desde modules/<nombre>/frontend/
///   2. Agregar una instancia a la lista.
List<ModuloIde> construirModulos() {
  return <ModuloIde>[
    ModuloHerramientas(),
    // ModuloOtroEquipo(),
  ];
}
