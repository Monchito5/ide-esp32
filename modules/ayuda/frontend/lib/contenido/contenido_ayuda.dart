// Archivo: modules/ayuda/frontend/lib/contenido/contenido_ayuda.dart
//
// Contenido editorial del modulo de Ayuda: FAQ, enlaces, licencia y creditos.
// Mantener este archivo separado de la UI permite actualizar textos sin tocar
// los widgets y facilita las pruebas de contenido.
import 'package:flutter/material.dart';

/// Pregunta frecuente mostrada en el centro de ayuda.
@immutable
class PreguntaFrecuente {
  const PreguntaFrecuente({
    required this.id,
    required this.pregunta,
    required this.respuesta,
    this.enlace,
    this.textoEnlace,
  });

  final String id;
  final String pregunta;
  final String respuesta;
  final String? enlace;
  final String? textoEnlace;
}

/// Enlace externo recomendado por el equipo de documentacion.
@immutable
class EnlaceAyuda {
  const EnlaceAyuda({
    required this.titulo,
    required this.descripcion,
    required this.url,
    required this.icono,
  });

  final String titulo;
  final String descripcion;
  final String url;
  final IconData icono;
}

/// Integrante mostrado en la ventana de creditos.
@immutable
class IntegranteEquipo {
  const IntegranteEquipo({required this.nombre, required this.rol});

  final String nombre;
  final String rol;
}

/// Grupo de creditos por modulo del IDE.
@immutable
class CreditosModulo {
  const CreditosModulo({
    required this.nombre,
    required this.descripcion,
    required this.estado,
    required this.integrantes,
  });

  final String nombre;
  final String descripcion;

  /// "Activo", "En desarrollo" o "Pendiente".
  final String estado;
  final List<IntegranteEquipo> integrantes;

  bool get activo => estado == 'Activo';
}

/// Fuente unica de verdad del contenido del modulo de Ayuda.
class ContenidoAyuda {
  ContenidoAyuda._();

  static const String producto = 'ESP32 IDE';
  static const String version = '1.0.0-beta';
  static const String descripcion =
      'Entorno de Desarrollo Integrado optimizado para microcontroladores '
      'de la familia ESP32.';
  static const String copyright = '© 2026 Proyecto de Simulación Empresarial';
  static const String repositorio = 'https://github.com/Monchito5/ide-esp32';

  static const List<PreguntaFrecuente> faq = <PreguntaFrecuente>[
    PreguntaFrecuente(
      id: 'puerto',
      pregunta: 'El IDE no detecta mi placa ESP32 (no aparece el puerto COM). '
          '¿Qué hago?',
      respuesta:
          'Normalmente falta el controlador USB-UART del sistema operativo. '
          'Identifica el chip serial de tu placa (los más comunes son CP2102 '
          'y CH340) e instala el driver oficial. Después reinicia el IDE y '
          'revisa Herramientas > Puerto para seleccionar el puerto correcto.',
      enlace:
          'https://www.silabs.com/software-and-tools/usb-to-uart-bridge-vcp-'
          'drivers',
      textoEnlace: 'Descargar drivers CP210x',
    ),
    PreguntaFrecuente(
      id: 'conexion',
      pregunta:
          'Al subir el código aparece: "A fatal error occurred: Failed to '
          'connect to ESP32".',
      respuesta:
          'La placa no entró en modo de programación. Pulsa "Subir" en el IDE '
          'y, cuando la consola muestre "Connecting...", mantén presionado el '
          'botón BOOT (o FLASH) de la placa hasta que aparezca el porcentaje '
          'de carga. Suelta el botón al terminar.',
      enlace: 'https://docs.espressif.com/projects/esptool/en/latest/esp32/'
          'troubleshooting.html',
      textoEnlace: 'Solución de problemas de esptool',
    ),
    PreguntaFrecuente(
      id: 'librerias',
      pregunta: '¿Cómo instalo librerías externas para mis sensores?',
      respuesta:
          'Abre el gestor de librerías del IDE y busca el componente que '
          'necesitas (por ejemplo, un driver para un sensor DHT11 o una '
          'pantalla OLED SSD1306). Elige la versión compatible y pulsa '
          'Instalar; quedará disponible para todos tus sketches.',
      enlace: 'https://docs.espressif.com/projects/idf-component-manager/en/'
          'latest/',
      textoEnlace: 'Guía del gestor de componentes',
    ),
    PreguntaFrecuente(
      id: 'monitor',
      pregunta: '¿Por qué el monitor serie muestra caracteres extraños?',
      respuesta:
          'La velocidad del monitor no coincide con la de tu sketch. Revisa '
          'la instrucción Serial.begin(115200); y ajusta el selector de '
          'baudios de la esquina inferior derecha del monitor exactamente al '
          'mismo valor.',
    ),
    PreguntaFrecuente(
      id: 'placa',
      pregunta: '¿Cómo selecciono la placa y la velocidad de carga?',
      respuesta: 'En la barra superior usa el selector de placa (por ejemplo '
          'ESP32-S31 Dev Module) y el selector de puerto. Para la velocidad '
          'de carga abre Herramientas > Velocidad de carga y elige 921600 '
          'baudios; si la carga falla, baja a 115200.',
    ),
    PreguntaFrecuente(
      id: 'reporte',
      pregunta: '¿Dónde reporto un error o sugiero una mejora?',
      respuesta:
          'Registra el problema en el repositorio del proyecto con el formato '
          'de reporte de bugs: describe los pasos para reproducirlo, la '
          'versión del IDE y el mensaje de la consola. Así el equipo de QA '
          'puede dar seguimiento.',
      enlace: 'https://github.com/Monchito5/ide-esp32/issues',
      textoEnlace: 'Abrir issues del proyecto',
    ),
  ];

  static const List<EnlaceAyuda> enlaces = <EnlaceAyuda>[
    EnlaceAyuda(
      titulo: 'Documentación de ESP-IDF',
      descripcion: 'Guía completa: instalación, API, componentes y ejemplos.',
      url: 'https://docs.espressif.com/projects/esp-idf/en/latest/esp32/',
      icono: Icons.menu_book_outlined,
    ),
    EnlaceAyuda(
      titulo: 'Primeros pasos con ESP32',
      descripcion: 'Instalación, toolchain y primer proyecto con ESP-IDF.',
      url: 'https://docs.espressif.com/projects/esp-idf/en/latest/esp32/'
          'get-started/',
      icono: Icons.memory,
    ),
    EnlaceAyuda(
      titulo: 'Referencia de la API ESP-IDF',
      descripcion: 'Periféricos, red, Bluetooth y sistema.',
      url: 'https://docs.espressif.com/projects/esp-idf/en/latest/esp32/'
          'api-reference/index.html',
      icono: Icons.code,
    ),
    EnlaceAyuda(
      titulo: 'Drivers USB CP210x',
      descripcion: 'Controlador oficial de Silicon Labs para placas ESP32.',
      url: 'https://www.silabs.com/software-and-tools/usb-to-uart-bridge-vcp-'
          'drivers',
      icono: Icons.usb,
    ),
    EnlaceAyuda(
      titulo: 'Driver CH340 / CH341',
      descripcion: 'Controlador de WCH para placas con chip serial CH340.',
      url: 'https://www.wch-ic.com/downloads/CH341SER_ZIP.html',
      icono: Icons.usb,
    ),
    EnlaceAyuda(
      titulo: 'esptool: carga de firmware',
      descripcion: 'Herramienta oficial para flashear y recuperar la placa.',
      url: 'https://docs.espressif.com/projects/esptool/en/latest/esp32/',
      icono: Icons.system_update_alt,
    ),
    EnlaceAyuda(
      titulo: 'Repositorio del proyecto',
      descripcion: 'Código fuente, issues y documentación del equipo.',
      url: 'https://github.com/Monchito5/ide-esp32',
      icono: Icons.hub,
    ),
    EnlaceAyuda(
      titulo: 'Registro de componentes ESP',
      descripcion: 'Librerías y componentes listos para ESP-IDF.',
      url: 'https://components.espressif.com/',
      icono: Icons.extension_outlined,
    ),
  ];

  static const List<CreditosModulo> creditos = <CreditosModulo>[
    CreditosModulo(
      nombre: 'Ayuda y documentación',
      descripcion:
          'Menú de ayuda, ventana Acerca de, FAQ, licencias y enlaces.',
      estado: 'Activo',
      integrantes: <IntegranteEquipo>[
        IntegranteEquipo(
          nombre: 'Evelyn',
          rol: 'Líder · Arquitectura UI y módulo',
        ),
        IntegranteEquipo(
          nombre: 'Octavio',
          rol: 'Documentación técnica y enrutamiento',
        ),
        IntegranteEquipo(
          nombre: 'Leonardo',
          rol: 'Diseño UX e integración frontend',
        ),
      ],
    ),
    CreditosModulo(
      nombre: 'Editor de código',
      descripcion: 'Editor, resaltado de sintaxis, undo/redo y atajos.',
      estado: 'En desarrollo',
      integrantes: <IntegranteEquipo>[
        IntegranteEquipo(nombre: 'Víctor', rol: 'Core y Undo/Redo'),
        IntegranteEquipo(nombre: 'César', rol: 'Sintaxis y búsqueda'),
        IntegranteEquipo(nombre: 'Nathaniel', rol: 'Atajos e interfaz'),
      ],
    ),
    CreditosModulo(
      nombre: 'Compilación y carga',
      descripcion: 'Toolchain, compilación y flasheo hacia la placa.',
      estado: 'Pendiente',
      integrantes: <IntegranteEquipo>[
        IntegranteEquipo(
          nombre: 'Equipo asignado',
          rol: 'En desarrollo',
        ),
      ],
    ),
    CreditosModulo(
      nombre: 'Interfaz principal',
      descripcion: 'Shell, layout maestro y paneles del IDE.',
      estado: 'Pendiente',
      integrantes: <IntegranteEquipo>[
        IntegranteEquipo(
          nombre: 'Equipo asignado',
          rol: 'En desarrollo',
        ),
      ],
    ),
    CreditosModulo(
      nombre: 'Base del IDE (equipo GRIS)',
      descripcion: 'Arquitectura inicial, shell y contratos compartidos.',
      estado: 'Activo',
      integrantes: <IntegranteEquipo>[
        IntegranteEquipo(
          nombre: 'Ing. Guillermo',
          rol: 'Líder técnico · Core backend',
        ),
        IntegranteEquipo(
          nombre: 'Ing. Neri',
          rol: 'Shell del IDE · Core frontend',
        ),
        IntegranteEquipo(
          nombre: 'Ing. Erick',
          rol: 'QA y DevOps',
        ),
      ],
    ),
  ];

  static const String licencia = '''Licencia MIT

Copyright (c) 2026 - Proyecto de Simulación Empresarial ESP32 IDE

Se concede permiso, de forma gratuita, a cualquier persona que obtenga una copia de este software y de los archivos de documentación asociados (el "Software"), para utilizar el Software sin restricción, incluyendo sin limitación los derechos a usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar y/o vender copias del Software, y a permitir a las personas a las que se les proporcione el Software a hacer lo mismo, sujeto a las siguientes condiciones:

El aviso de copyright anterior y este aviso de permiso se incluirán en todas las copias o partes sustanciales del Software.

EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO, EXPRESA O IMPLÍCITA, INCLUYENDO PERO NO LIMITADO A LAS GARANTÍAS DE COMERCIABILIDAD, IDONEIDAD PARA UN PROPÓSITO PARTICULAR Y NO INFRACCIÓN. EN NINGÚN CASO LOS AUTORES O TITULARES DEL COPYRIGHT SERÁN RESPONSABLES DE NINGUNA RECLAMACIÓN, DAÑOS U OTRA RESPONSABILIDAD, YA SEA EN UNA ACCIÓN DE CONTRATO, AGRAVIO O DE OTRO MODO, QUE SURJA DE, FUERA DE O EN CONEXIÓN CON EL SOFTWARE O EL USO U OTROS TRATOS EN EL SOFTWARE.
''';
}
