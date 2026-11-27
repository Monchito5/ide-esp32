// Archivo: modules/ayuda/frontend/lib/ui/dialogo_licencias.dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../contenido/contenido_ayuda.dart';
import 'componentes.dart';

/// Muestra el texto completo de la licencia MIT del proyecto.
Future<void> mostrarLicencias(BuildContext context) {
  return showDialog<void>(
    context: context,
    builder: (BuildContext contexto) => const DialogoLicencias(),
  );
}

class DialogoLicencias extends StatelessWidget {
  const DialogoLicencias({super.key});

  Future<void> _copiar(BuildContext context) async {
    await Clipboard.setData(
      const ClipboardData(text: ContenidoAyuda.licencia),
    );
    if (!context.mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Licencia copiada al portapapeles.'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      clipBehavior: Clip.antiAlias,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 560),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            const EncabezadoModal(
              titulo: 'Licencias',
              subtitulo: 'Licencia MIT · Código abierto',
              icono: Icons.description_outlined,
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 18, 24, 20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const Text(
                    'El proyecto ESP32 IDE se distribuye bajo la licencia MIT. '
                    'Puedes usar, modificar y compartir el código siempre que '
                    'conserves el aviso de copyright.',
                    style: TextStyle(
                      color: PaletaAyuda.textoSutil,
                      fontSize: 12.5,
                      height: 1.45,
                    ),
                  ),
                  const SizedBox(height: 14),
                  Container(
                    height: 290,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: const Color(0xFF0F172A),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(0xFF1E293B)),
                    ),
                    child: const SingleChildScrollView(
                      padding: EdgeInsets.all(14),
                      child: SelectableText(
                        ContenidoAyuda.licencia,
                        style: TextStyle(
                          color: Color(0xFFE2E8F0),
                          fontFamily: 'monospace',
                          fontSize: 11.5,
                          height: 1.55,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: <Widget>[
                      const Expanded(
                        child: Text(
                          'Copyright © 2026',
                          style: TextStyle(
                            color: PaletaAyuda.textoSutil,
                            fontSize: 11.5,
                          ),
                        ),
                      ),
                      BotonModal(
                        texto: 'Copiar',
                        icono: Icons.copy,
                        alPresionar: () => _copiar(context),
                      ),
                      const SizedBox(width: 8),
                      BotonModal(
                        texto: 'Cerrar',
                        primario: true,
                        alPresionar: () => Navigator.of(context).pop(),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
