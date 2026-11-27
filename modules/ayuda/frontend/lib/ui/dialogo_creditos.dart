// Archivo: modules/ayuda/frontend/lib/ui/dialogo_creditos.dart
import 'package:flutter/material.dart';

import '../contenido/contenido_ayuda.dart';
import 'componentes.dart';

/// Muestra el listado de equipos y personas que construyen el IDE.
Future<void> mostrarCreditos(BuildContext context) {
  return showDialog<void>(
    context: context,
    builder: (BuildContext contexto) => const DialogoCreditos(),
  );
}

class DialogoCreditos extends StatelessWidget {
  const DialogoCreditos({super.key});

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      clipBehavior: Clip.antiAlias,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 580),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            const EncabezadoModal(
              titulo: 'Créditos del proyecto',
              subtitulo: 'Equipos y personas que construyen el IDE',
              icono: Icons.groups_outlined,
            ),
            Flexible(
              child: ListView.separated(
                shrinkWrap: true,
                padding: const EdgeInsets.fromLTRB(20, 18, 20, 18),
                itemCount: ContenidoAyuda.creditos.length,
                separatorBuilder: (BuildContext context, int index) =>
                    const SizedBox(height: 12),
                itemBuilder: (BuildContext context, int index) {
                  return _TarjetaModulo(
                    modulo: ContenidoAyuda.creditos[index],
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
                      'El orden de los módulos no implica jerarquía.',
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

class _TarjetaModulo extends StatelessWidget {
  const _TarjetaModulo({required this.modulo});

  final CreditosModulo modulo;

  @override
  Widget build(BuildContext context) {
    final (Color fondo, Color texto) = _coloresEstado(modulo.estado);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: PaletaAyuda.fondo,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: PaletaAyuda.borde),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(
                child: Text(
                  modulo.nombre,
                  style: const TextStyle(
                    color: PaletaAyuda.texto,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Etiqueta(
                texto: modulo.estado,
                colorFondo: fondo,
                colorTexto: texto,
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            modulo.descripcion,
            style: const TextStyle(
              color: PaletaAyuda.textoSutil,
              fontSize: 11.5,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 10),
          for (final IntegranteEquipo integrante in modulo.integrantes)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 3),
              child: Row(
                children: <Widget>[
                  AvatarInicial(nombre: integrante.nombre, tamano: 30),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          integrante.nombre,
                          style: const TextStyle(
                            color: PaletaAyuda.texto,
                            fontSize: 12.5,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Text(
                          integrante.rol,
                          style: const TextStyle(
                            color: PaletaAyuda.textoSutil,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  (Color, Color) _coloresEstado(String estado) {
    switch (estado) {
      case 'Activo':
        return (const Color(0xFFE7F6E7), const Color(0xFF1B7A1B));
      case 'En desarrollo':
        return (const Color(0xFFFEF3C7), const Color(0xFF92400E));
      default:
        return (const Color(0xFFEEF2F7), const Color(0xFF475569));
    }
  }
}
