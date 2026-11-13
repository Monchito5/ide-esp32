// Archivo: modules/ayuda/frontend/lib/ui/vista_ayuda.dart
import 'package:flutter/material.dart';

import '../contenido/contenido_ayuda.dart';
import 'centro_ayuda.dart';
import 'componentes.dart';
import 'dialogo_creditos.dart';
import 'dialogo_faq.dart';
import 'ventana_acerca_de.dart';

/// Panel del módulo de Ayuda dentro del layout principal del IDE.
class VistaAyuda extends StatelessWidget {
  const VistaAyuda({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          const Row(
            children: <Widget>[
              LogoEsp32(tamano: 44),
              SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      'Ayuda y documentación',
                      style: TextStyle(
                        color: PaletaAyuda.texto,
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        letterSpacing: -0.2,
                      ),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'ESP32 IDE v${ContenidoAyuda.version}',
                      style: TextStyle(
                        color: PaletaAyuda.textoSutil,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _AccionTile(
            icono: Icons.menu_book_outlined,
            titulo: 'Centro de ayuda',
            detalle: 'Guías y enlaces oficiales',
            alPresionar: () => mostrarCentroAyuda(context),
          ),
          const SizedBox(height: 8),
          _AccionTile(
            icono: Icons.quiz_outlined,
            titulo: 'Preguntas frecuentes',
            detalle: '${ContenidoAyuda.faq.length} respuestas rápidas',
            alPresionar: () => mostrarFaq(context),
          ),
          const SizedBox(height: 8),
          _AccionTile(
            icono: Icons.groups_outlined,
            titulo: 'Créditos',
            detalle: 'Equipos y módulos del proyecto',
            alPresionar: () => mostrarCreditos(context),
          ),
          const SizedBox(height: 8),
          _AccionTile(
            icono: Icons.info_outline,
            titulo: 'Acerca de ESP32 IDE',
            detalle: 'Versión, licencia y descripción',
            alPresionar: () => mostrarAcercaDe(context),
          ),
          const SizedBox(height: 18),
          const Divider(height: 1, color: PaletaAyuda.borde),
          const SizedBox(height: 14),
          Row(
            children: <Widget>[
              const Expanded(
                child: Text(
                  'Enlaces rápidos',
                  style: TextStyle(
                    color: PaletaAyuda.texto,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              TextButton(
                onPressed: () => mostrarCentroAyuda(context),
                style: TextButton.styleFrom(
                  foregroundColor: PaletaAyuda.azul,
                  padding: EdgeInsets.zero,
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                child: const Text('Ver todos', style: TextStyle(fontSize: 11)),
              ),
            ],
          ),
          const SizedBox(height: 6),
          for (final EnlaceAyuda enlace in ContenidoAyuda.enlaces.take(4))
            _EnlaceCompacto(enlace: enlace),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: PaletaAyuda.fondo,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: PaletaAyuda.borde),
            ),
            child: const Row(
              children: <Widget>[
                Icon(
                  Icons.verified_user_outlined,
                  size: 16,
                  color: PaletaAyuda.verde,
                ),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Software libre bajo licencia MIT · ${ContenidoAyuda.copyright}',
                    style: TextStyle(
                      color: PaletaAyuda.textoSutil,
                      fontSize: 10,
                      height: 1.35,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _AccionTile extends StatelessWidget {
  const _AccionTile({
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
      color: Colors.white,
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        onTap: alPresionar,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: PaletaAyuda.borde),
          ),
          child: Row(
            children: <Widget>[
              Icon(icono, size: 18, color: PaletaAyuda.azul),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      titulo,
                      style: const TextStyle(
                        color: PaletaAyuda.texto,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Text(
                      detalle,
                      style: const TextStyle(
                        color: PaletaAyuda.textoSutil,
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(
                Icons.chevron_right,
                size: 16,
                color: Color(0xFF94A3B8),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EnlaceCompacto extends StatelessWidget {
  const _EnlaceCompacto({required this.enlace});

  final EnlaceAyuda enlace;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => abrirEnlaceExterno(context, enlace.url),
      borderRadius: BorderRadius.circular(6),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          children: <Widget>[
            Icon(enlace.icono, size: 14, color: PaletaAyuda.textoSutil),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                enlace.titulo,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: PaletaAyuda.texto,
                  fontSize: 11.5,
                ),
              ),
            ),
            const Icon(
              Icons.open_in_new,
              size: 12,
              color: Color(0xFF94A3B8),
            ),
          ],
        ),
      ),
    );
  }
}
