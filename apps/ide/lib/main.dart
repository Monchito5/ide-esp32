// Archivo: apps/ide/lib/main.dart
//
// PUNTO DE ENTRADA UNICO del IDE.
// Arranca el shell Flutter y registra los modulos activos.

import 'package:flutter/material.dart';
import 'package:ide_core/ide_core.dart';

import 'nucleo/registro_modulos.dart';

void main() {
  final registro = RegistroModulos(construirModulos());
  runApp(IdeApp(registro: registro));
}

class IdeApp extends StatelessWidget {
  const IdeApp({super.key, required this.registro});

  final RegistroModulos registro;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IDE ESP32',
      debugShowCheckedModeBanner: false,
      theme: TemaIde.claro(),
      darkTheme: TemaIde.oscuro(),
      home: LayoutPrincipal(registro: registro),
    );
  }
}
