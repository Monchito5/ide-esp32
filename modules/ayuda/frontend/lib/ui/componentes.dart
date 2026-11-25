// Archivo: modules/ayuda/frontend/lib/ui/componentes.dart
//
// Componentes visuales compartidos por las ventanas del modulo de Ayuda.
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

/// Paleta del modulo, alineada con el tema base del IDE.
class PaletaAyuda {
  PaletaAyuda._();

  static const Color azul = Color(0xFF1B3A5C);
  static const Color azulOscuro = Color(0xFF16293F);
  static const Color verde = Color(0xFF008A00);
  static const Color fondo = Color(0xFFF8FAFC);
  static const Color borde = Color(0xFFE2E8F0);
  static const Color texto = Color(0xFF1F2937);
  static const Color textoSutil = Color(0xFF64748B);
}

/// Logotipo estilizado de la placa ESP32.
class LogoEsp32 extends StatelessWidget {
  const LogoEsp32({super.key, this.tamano = 64});

  final double tamano;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: tamano,
      height: tamano,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: <Color>[Color(0xFF2B5580), PaletaAyuda.azulOscuro],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(tamano * 0.24),
        border: Border.all(color: Colors.white24),
        boxShadow: const <BoxShadow>[
          BoxShadow(
            color: Color(0x40000000),
            blurRadius: 16,
            offset: Offset(0, 6),
          ),
        ],
      ),
      child: Stack(
        alignment: Alignment.center,
        children: <Widget>[
          Icon(
            Icons.memory,
            color: Colors.white,
            size: tamano * 0.52,
          ),
          Positioned(
            right: tamano * 0.12,
            top: tamano * 0.12,
            child: Container(
              width: tamano * 0.13,
              height: tamano * 0.13,
              decoration: const BoxDecoration(
                color: Color(0xFF8DC63F),
                shape: BoxShape.circle,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Encabezado oscuro reutilizado por las ventanas modales.
class EncabezadoModal extends StatelessWidget {
  const EncabezadoModal({
    super.key,
    required this.titulo,
    required this.icono,
    this.subtitulo,
    this.conLogo = false,
    this.alCerrar,
  });

  final String titulo;
  final String? subtitulo;
  final IconData icono;
  final bool conLogo;
  final VoidCallback? alCerrar;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 22, 12, 22),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: <Color>[PaletaAyuda.azul, PaletaAyuda.azulOscuro],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          if (conLogo)
            const LogoEsp32(tamano: 52)
          else
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                color: Colors.white12,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.white24),
              ),
              child: Icon(icono, color: Colors.white, size: 24),
            ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  titulo,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 19,
                    fontWeight: FontWeight.w700,
                    height: 1.2,
                  ),
                ),
                if (subtitulo != null) ...<Widget>[
                  const SizedBox(height: 4),
                  Text(
                    subtitulo!,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 12.5,
                      height: 1.35,
                    ),
                  ),
                ],
              ],
            ),
          ),
          IconButton(
            onPressed: alCerrar ?? () => Navigator.of(context).maybePop(),
            tooltip: 'Cerrar',
            icon: const Icon(Icons.close, color: Colors.white70, size: 20),
          ),
        ],
      ),
    );
  }
}

/// Boton de accion usado en los pies de las ventanas.
class BotonModal extends StatelessWidget {
  const BotonModal({
    super.key,
    required this.texto,
    this.icono,
    this.alPresionar,
    this.primario = false,
  });

  final String texto;
  final IconData? icono;
  final VoidCallback? alPresionar;
  final bool primario;

  @override
  Widget build(BuildContext context) {
    final Widget contenido = Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        if (icono != null) ...<Widget>[
          Icon(icono, size: 18),
          const SizedBox(width: 8),
        ],
        Text(texto),
      ],
    );

    if (primario) {
      return FilledButton(
        onPressed: alPresionar,
        style: FilledButton.styleFrom(
          backgroundColor: PaletaAyuda.verde,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
        child: contenido,
      );
    }

    return OutlinedButton(
      onPressed: alPresionar,
      style: OutlinedButton.styleFrom(
        foregroundColor: PaletaAyuda.azul,
        side: const BorderSide(color: Color(0xFFCBD5E1)),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
      ),
      child: contenido,
    );
  }
}

/// Etiqueta compacta para versiones y estados.
class Etiqueta extends StatelessWidget {
  const Etiqueta({
    super.key,
    required this.texto,
    required this.colorFondo,
    required this.colorTexto,
  });

  final String texto;
  final Color colorFondo;
  final Color colorTexto;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: colorFondo,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        texto,
        style: TextStyle(
          color: colorTexto,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

/// Avatar circular con la inicial del integrante.
class AvatarInicial extends StatelessWidget {
  const AvatarInicial({super.key, required this.nombre, this.tamano = 36});

  final String nombre;
  final double tamano;

  static const List<Color> _colores = <Color>[
    Color(0xFF1B3A5C),
    Color(0xFF008A00),
    Color(0xFF7C3AED),
    Color(0xFFB45309),
    Color(0xFF0E7490),
  ];

  @override
  Widget build(BuildContext context) {
    final String limpio = nombre.trim();
    final String inicial =
        limpio.isEmpty ? '?' : limpio.substring(0, 1).toUpperCase();
    final int suma = limpio.codeUnits.fold<int>(0, (int a, int b) => a + b);
    final Color color = _colores[suma % _colores.length];

    return Container(
      width: tamano,
      height: tamano,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: color,
        shape: BoxShape.circle,
      ),
      child: Text(
        inicial,
        style: TextStyle(
          color: Colors.white,
          fontSize: tamano * 0.42,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

/// Abre un enlace externo y avisa si el sistema no pudo hacerlo.
Future<void> abrirEnlaceExterno(BuildContext context, String url) async {
  final ScaffoldMessengerState? messenger = ScaffoldMessenger.maybeOf(context);
  bool abierto = false;
  try {
    abierto = await launchUrl(
      Uri.parse(url),
      mode: LaunchMode.platformDefault,
    );
  } catch (_) {
    abierto = false;
  }

  if (!abierto) {
    messenger?.showSnackBar(
      SnackBar(
        content: Text('No se pudo abrir el enlace: $url'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}

/// Pie de ventana con la nota legal del proyecto.
class PieDialogo extends StatelessWidget {
  const PieDialogo({super.key, required this.texto});

  final String texto;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: const BoxDecoration(
        color: PaletaAyuda.fondo,
        border: Border(top: BorderSide(color: PaletaAyuda.borde)),
      ),
      child: Text(
        texto,
        textAlign: TextAlign.center,
        style: const TextStyle(
          color: PaletaAyuda.textoSutil,
          fontSize: 11.5,
        ),
      ),
    );
  }
}
