// Archivo: modules/ayuda/frontend/lib/ui/acciones_ayuda.dart
import 'package:ide_core/ide_core.dart';

import 'centro_ayuda.dart';
import 'dialogo_creditos.dart' as creditos;
import 'dialogo_faq.dart';
import 'ventana_acerca_de.dart';

/// Conecta las acciones del modulo con el menu Ayuda del shell del IDE.
///
/// La aplicacion llama a esta funcion al construir [LayoutPrincipal]; asi el
/// core no necesita conocer la implementacion del modulo.
void mostrarCreditos(BuildContext context) {
  creditos.mostrarCreditos(context);
}

void mostrarEnlacesRapidos(BuildContext context) {
  mostrarCentroAyuda(context);
}

AccionesAyuda crearAccionesAyuda() {
  return const AccionesAyuda(
    abrirDocumentacion: mostrarCentroAyuda,
    abrirPreguntasFrecuentes: mostrarFaq,
    abrirAcercaDe: mostrarAcercaDe,
    abrirCreditos: mostrarCreditos,
    abrirEnlacesRapidos: mostrarEnlacesRapidos,
  );
}
