// Archivo: modules/ayuda/frontend/lib/ui/centro_ayuda.dart
import 'package:flutter/material.dart';

import '../contenido/contenido_ayuda.dart';
import 'componentes.dart';
import 'dialogo_faq.dart';
import 'ventana_acerca_de.dart';

/// Abre el centro de ayuda: guías, enlaces oficiales y accesos rápidos.
Future<void> mostrarCentroAyuda(BuildContext context) {
  return showDialog<void>(
    context: context,
    builder: (BuildContext contexto) => const CentroAyuda(),
  );
}

class CentroAyuda extends StatelessWidget {
  const CentroAyuda({super.key});

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      clipBehavior: Clip.antiAlias,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 720),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            const EncabezadoModal(
              titulo: 'Centro de ayuda',
              subtitulo: 'Documentación, guías y soporte del IDE',
              icono: Icons.menu_book_outlined,
              conLogo: true,
            ),
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 22, 24, 22),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    const Text(
                      '¿En qué podemos ayudarte?',
                      style: TextStyle(
                        color: PaletaAyuda.texto,
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Encuentra respuestas a los problemas más comunes, '
                      'consulta la documentación oficial de ESP32 y ESP-IDF '
                      'o revisa los créditos y la licencia del proyecto.',
                      style: TextStyle(
                        color: PaletaAyuda.textoSutil,
                        fontSize: 12.5,
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 18),
                    LayoutBuilder(
                      builder: (BuildContext context, BoxConstraints c) {
                        final double ancho = c.maxWidth >= 560
                            ? (c.maxWidth - 12) / 2
                            : c.maxWidth;
                        return Wrap(
                          spacing: 12,
                          runSpacing: 12,
                          children: <Widget>[
                            SizedBox(
                              width: ancho,
                              child: _AccionRapida(
                                icono: Icons.quiz_outlined,
                                titulo: 'Preguntas frecuentes',
                                detalle:
                                    '${ContenidoAyuda.faq.length} respuestas '
                                    'sobre puertos, carga y librerías.',
                                alPresionar: () => mostrarFaq(context),
                              ),
                            ),
                            SizedBox(
                              width: ancho,
                              child: _AccionRapida(
                                icono: Icons.info_outline,
                                titulo: 'Acerca de ESP32 IDE',
                                detalle: 'Versión ${ContenidoAyuda.version}, '
                                    'licencia y créditos del equipo.',
                                alPresionar: () => mostrarAcercaDe(context),
                              ),
                            ),
                          ],
                        );
                      },
                    ),
                    const SizedBox(height: 24),
                    Row(
                      children: <Widget>[
                        const Text(
                          'Guías y enlaces oficiales',
                          style: TextStyle(
                            color: PaletaAyuda.texto,
                            fontSize: 14,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const Spacer(),
                        Text(
                          '${ContenidoAyuda.enlaces.length} recursos',
                          style: const TextStyle(
                            color: PaletaAyuda.textoSutil,
                            fontSize: 11.5,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Los enlaces se abren en tu navegador predeterminado.',
                      style: TextStyle(
                        color: PaletaAyuda.textoSutil,
                        fontSize: 11.5,
                      ),
                    ),
                    const SizedBox(height: 12),
                    LayoutBuilder(
                      builder: (BuildContext context, BoxConstraints c) {
                        final double ancho = c.maxWidth >= 560
                            ? (c.maxWidth - 12) / 2
                            : c.maxWidth;
                        return Wrap(
                          spacing: 12,
                          runSpacing: 12,
                          children: <Widget>[
                            for (final EnlaceAyuda enlace
                                in ContenidoAyuda.enlaces)
                              SizedBox(
                                width: ancho,
                                child: _TarjetaEnlace(enlace: enlace),
                              ),
                          ],
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
            const PieDialogo(
              texto: 'Documentación del módulo de Ayuda · '
                  'ESP32 IDE ${ContenidoAyuda.version}',
            ),
          ],
        ),
      ),
    );
  }
}

class _AccionRapida extends StatelessWidget {
  const _AccionRapida({
    required this.icono,
    required this.titulo,
    required this.detalle,
    required this.alPresionar,
  });

  final IconData icono;
  final String titulo;
  final String detalle;
  final VoidCallback alPresionar;

  @override
  Widget build(BuildContext context) {
    return Material(
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: alPresionar,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: PaletaAyuda.borde),
          ),
          child: Row(
            children: <Widget>[
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F0F8),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icono, color: PaletaAyuda.azul, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      titulo,
                      style: const TextStyle(
                        color: PaletaAyuda.texto,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      detalle,
                      style: const TextStyle(
                        color: PaletaAyuda.textoSutil,
                        fontSize: 11,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(
                Icons.chevron_right,
                color: PaletaAyuda.textoSutil,
                size: 18,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TarjetaEnlace extends StatelessWidget {
  const _TarjetaEnlace({required this.enlace});

  final EnlaceAyuda enlace;

  @override
  Widget build(BuildContext context) {
    return Material(
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: PaletaAyuda.borde),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Icon(enlace.icono, size: 18, color: PaletaAyuda.azul),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      enlace.titulo,
                      style: const TextStyle(
                        color: PaletaAyuda.texto,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        height: 1.3,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      enlace.descripcion,
                      style: const TextStyle(
                        color: PaletaAyuda.textoSutil,
                        fontSize: 10.5,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(
                Icons.open_in_new,
                size: 14,
                color: Color(0xFF94A3B8),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
