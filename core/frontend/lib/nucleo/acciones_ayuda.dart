// Archivo: core/frontend/lib/nucleo/acciones_ayuda.dart
import 'package:flutter/widgets.dart';

/// Accion que recibe el contexto de la aplicacion y abre una vista de ayuda.
typedef AccionAyuda = void Function(BuildContext context);

/// Contrato de conexion entre el shell del IDE y el modulo de Ayuda.
///
/// El core no importa al modulo: la aplicacion inyecta estas acciones en
/// [LayoutPrincipal] y el modulo decide como implementarlas.
@immutable
class AccionesAyuda {
  const AccionesAyuda({
    this.abrirDocumentacion,
    this.abrirPreguntasFrecuentes,
    this.abrirAcercaDe,
  });

  /// Abre el centro de documentacion y enlaces.
  final AccionAyuda? abrirDocumentacion;

  /// Abre la lista de preguntas frecuentes.
  final AccionAyuda? abrirPreguntasFrecuentes;

  /// Abre la ventana modal "Acerca de".
  final AccionAyuda? abrirAcercaDe;

  /// Indica si al menos una accion esta disponible.
  bool get disponible =>
      abrirDocumentacion != null ||
      abrirPreguntasFrecuentes != null ||
      abrirAcercaDe != null;
}
