// Archivo: modules/ayuda/frontend/lib/ui/dialogo_faq.dart
import 'package:flutter/material.dart';

import '../contenido/contenido_ayuda.dart';
import 'componentes.dart';

/// Abre la ventana de preguntas frecuentes.
Future<void> mostrarFaq(BuildContext context) {
  return showDialog<void>(
    context: context,
    builder: (BuildContext contexto) => const DialogoFaq(),
  );
}

class DialogoFaq extends StatelessWidget {
  const DialogoFaq({super.key});

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      clipBehavior: Clip.antiAlias,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 600),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            const EncabezadoModal(
              titulo: 'Preguntas frecuentes',
              subtitulo: 'Solución de problemas y dudas del IDE',
              icono: Icons.quiz_outlined,
            ),
            Flexible(
              child: ListView.separated(
                shrinkWrap: true,
                padding: const EdgeInsets.fromLTRB(20, 18, 20, 18),
                itemCount: ContenidoAyuda.faq.length,
                separatorBuilder: (BuildContext context, int index) =>
                    const SizedBox(height: 10),
                itemBuilder: (BuildContext context, int index) {
                  return _ItemFaq(
                    numero: index + 1,
                    pregunta: ContenidoAyuda.faq[index],
                  );
                },
              ),
            ),
            Container(
              padding: const EdgeInsets.fromLTRB(20, 10, 20, 14),
              decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: PaletaAyuda.borde)),
              ),
              child: Row(
                children: <Widget>[
                  const Expanded(
                    child: Text(
                      '¿No encuentras tu respuesta? Consulta los enlaces del '
                      'centro de ayuda.',
                      style: TextStyle(
                        color: PaletaAyuda.textoSutil,
                        fontSize: 11.5,
                      ),
                    ),
                  ),
                  BotonModal(
                    texto: 'Cerrar',
                    primario: true,
                    alPresionar: () => Navigator.of(context).pop(),
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

class _ItemFaq extends StatelessWidget {
  const _ItemFaq({required this.numero, required this.pregunta});

  final int numero;
  final PreguntaFrecuente pregunta;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: PaletaAyuda.fondo,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: PaletaAyuda.borde),
      ),
      clipBehavior: Clip.antiAlias,
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
          childrenPadding: const EdgeInsets.fromLTRB(12, 0, 12, 14),
          iconColor: PaletaAyuda.azul,
          collapsedIconColor: PaletaAyuda.textoSutil,
          leading: Container(
            width: 28,
            height: 28,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: const Color(0xFFE8F0F8),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              '$numero',
              style: const TextStyle(
                color: PaletaAyuda.azul,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          title: Text(
            pregunta.pregunta,
            style: const TextStyle(
              color: PaletaAyuda.texto,
              fontSize: 13,
              fontWeight: FontWeight.w600,
              height: 1.35,
            ),
          ),
          children: <Widget>[
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                pregunta.respuesta,
                style: const TextStyle(
                  color: PaletaAyuda.textoSutil,
                  fontSize: 12.5,
                  height: 1.55,
                ),
              ),
            ),
            if (pregunta.enlace != null)
              Align(
                alignment: Alignment.centerLeft,
                child: Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: TextButton.icon(
                    onPressed: null,
                    icon: const Icon(Icons.open_in_new, size: 15),
                    label: Text(
                      pregunta.textoEnlace ?? 'Más información',
                      style: const TextStyle(fontSize: 12),
                    ),
                    style: TextButton.styleFrom(
                      foregroundColor: PaletaAyuda.azul,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
