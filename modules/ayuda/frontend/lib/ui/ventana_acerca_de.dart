// Archivo: modules/ayuda/frontend/lib/ui/ventana_acerca_de.dart
import 'package:flutter/material.dart';

import '../contenido/contenido_ayuda.dart';
import 'componentes.dart';
import 'dialogo_creditos.dart';
import 'dialogo_licencias.dart';

/// Abre la ventana modal "Acerca de ESP32 IDE".
Future<void> mostrarAcercaDe(BuildContext context) {
  return showDialog<void>(
    context: context,
    barrierColor: const Color(0x99000000),
    builder: (BuildContext contexto) => const DialogoAcercaDe(),
  );
}

/// Ventana modal nativa con la identidad del producto, su version y accesos
/// directos a creditos y licencias.
class DialogoAcercaDe extends StatelessWidget {
  const DialogoAcercaDe({super.key});

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      clipBehavior: Clip.antiAlias,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 520),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            const EncabezadoModal(
              titulo: 'Acerca de ESP32 IDE',
              subtitulo: 'Módulo de Ayuda y Documentación',
              icono: Icons.memory,
              conLogo: true,
            ),
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 22, 24, 18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    const Row(
                      children: <Widget>[
                        Expanded(
                          child: Text(
                            ContenidoAyuda.producto,
                            style: TextStyle(
                              color: PaletaAyuda.texto,
                              fontSize: 23,
                              fontWeight: FontWeight.w800,
                              letterSpacing: -0.3,
                            ),
                          ),
                        ),
                        Etiqueta(
                          texto: 'v${ContenidoAyuda.version}',
                          colorFondo: Color(0xFFE8F0F8),
                          colorTexto: PaletaAyuda.azul,
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      ContenidoAyuda.descripcion,
                      style: TextStyle(
                        color: PaletaAyuda.textoSutil,
                        fontSize: 13.5,
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 18),
                    const Divider(height: 1, color: PaletaAyuda.borde),
                    const SizedBox(height: 16),
                    const _FilaInfo(
                      icono: Icons.tag,
                      etiqueta: 'Versión',
                      valor: ContenidoAyuda.version,
                    ),
                    const SizedBox(height: 10),
                    const _FilaInfo(
                      icono: Icons.verified_user_outlined,
                      etiqueta: 'Licencia',
                      valor: 'MIT (código abierto)',
                    ),
                    const SizedBox(height: 10),
                    const _FilaInfo(
                      icono: Icons.extension_outlined,
                      etiqueta: 'Módulo',
                      valor: 'Ayuda y documentación',
                    ),
                    const SizedBox(height: 10),
                    const _FilaInfo(
                      icono: Icons.memory,
                      etiqueta: 'Plataforma',
                      valor: 'ESP32 · ESP32-S31',
                    ),
                    const SizedBox(height: 20),
                    const Text(
                      'Este proyecto se distribuye con fines académicos. '
                      'El código, la documentación y los recursos gráficos '
                      'pueden reutilizarse bajo los términos de la licencia '
                      'MIT.',
                      style: TextStyle(
                        color: PaletaAyuda.textoSutil,
                        fontSize: 12,
                        height: 1.45,
                      ),
                    ),
                    const SizedBox(height: 20),
                    Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: <Widget>[
                        BotonModal(
                          texto: 'Créditos',
                          icono: Icons.groups_outlined,
                          alPresionar: () => mostrarCreditos(context),
                        ),
                        BotonModal(
                          texto: 'Licencias',
                          icono: Icons.description_outlined,
                          alPresionar: () => mostrarLicencias(context),
                        ),
                        BotonModal(
                          texto: 'Cerrar',
                          icono: Icons.check,
                          primario: true,
                          alPresionar: () => Navigator.of(context).pop(),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const PieDialogo(
              texto: '${ContenidoAyuda.copyright} · Todos los derechos '
                  'reservados.',
            ),
          ],
        ),
      ),
    );
  }
}

class _FilaInfo extends StatelessWidget {
  const _FilaInfo({
    required this.icono,
    required this.etiqueta,
    required this.valor,
  });

  final IconData icono;
  final String etiqueta;
  final String valor;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Icon(icono, size: 17, color: PaletaAyuda.textoSutil),
        const SizedBox(width: 10),
        SizedBox(
          width: 92,
          child: Text(
            etiqueta,
            style: const TextStyle(
              color: PaletaAyuda.textoSutil,
              fontSize: 12.5,
            ),
          ),
        ),
        Expanded(
          child: Text(
            valor,
            style: const TextStyle(
              color: PaletaAyuda.texto,
              fontSize: 12.5,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    );
  }
}
