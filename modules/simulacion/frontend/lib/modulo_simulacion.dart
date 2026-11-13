// Archivo: modules/simulacion/frontend/lib/modulo_simulacion.dart
import 'package:flutter/material.dart';
import 'package:ide_core/ide_core.dart';

import 'api_simulacion.dart';
import 'services/simulation_api.dart';
import 'ui/screens/simulacion_screen.dart';

/// Implementacion del contrato ModuloIde para el modulo Simulacion.
class ModuloSimulacion implements ModuloIde {
  ModuloSimulacion({ApiSimulacion? api})
      : _api = api ?? ApiSimulacion();

  final ApiSimulacion _api;

  @override
  String get id => 'simulacion';

  @override
  String get nombre => 'Simulacion';

  @override
  IconData get icono => Icons.sim_card;

  @override
  Widget construirVista(BuildContext context) =>
      SimulacionScreen(api: _api);
}
