// Archivo: modules/ayuda/frontend/test/contenido_ayuda_test.dart
import 'package:ayuda_ui/ayuda_ui.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Contenido del módulo de Ayuda', () {
    test('incluye al menos cinco preguntas frecuentes', () {
      expect(ContenidoAyuda.faq.length, greaterThanOrEqualTo(5));
    });

    test('todas las preguntas tienen respuesta', () {
      for (final PreguntaFrecuente pregunta in ContenidoAyuda.faq) {
        expect(
          pregunta.respuesta.trim(),
          isNotEmpty,
          reason: 'La pregunta ${pregunta.id} no tiene respuesta.',
        );
      }
    });

    test('los enlaces usan HTTPS', () {
      for (final EnlaceAyuda enlace in ContenidoAyuda.enlaces) {
        expect(
          enlace.url,
          startsWith('https://'),
          reason: 'El enlace "${enlace.titulo}" no es seguro.',
        );
      }
    });

    test('la licencia es MIT e incluye el aviso de copyright', () {
      expect(ContenidoAyuda.licencia, contains('Licencia MIT'));
      expect(ContenidoAyuda.licencia, contains('Copyright (c) 2026'));
    });

    test('los créditos incluyen al equipo de Ayuda', () {
      final CreditosModulo modulo = ContenidoAyuda.creditos.first;
      expect(modulo.nombre, contains('Ayuda'));
      expect(
        modulo.integrantes.map((IntegranteEquipo i) => i.nombre),
        containsAll(<String>['Evelyn', 'Octavio', 'Leonardo']),
      );
    });
  });
}
