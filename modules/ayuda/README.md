# Módulo de Ayuda y Documentación — ESP32 IDE

**Equipo:** Evelyn (Dev A / líder), Octavio (Dev B), Leonardo (Dev C)
**Rama de trabajo:** `feature/ayuda`
**Estado:** contenido y diseño terminados; menú y ventana implementados en Flutter, validados con `flutter analyze` y pruebas en verde, y replicados en el prototipo navegable.

Este módulo implementa el alcance del acta constitutiva: adaptar el menú
**Ayuda**, mostrar la ventana modal **Acerca de**, enrutar a documentación y
enlaces, y reunir la FAQ, la licencia MIT y los créditos del proyecto.

---

## 1. Qué incluye

| Elemento | Dónde vive | Estado |
|---|---|---|
| Menú `Ayuda` con Documentación, FAQ y Acerca de | `core/frontend/lib/ui/layout/layout_principal.dart` | Funcional |
| Ventana modal «Acerca de ESP32 IDE» | `lib/ui/ventana_acerca_de.dart` | Funcional |
| Preguntas frecuentes (6) | `lib/ui/dialogo_faq.dart` | Funcional |
| Licencia MIT con copiado al portapapeles | `lib/ui/dialogo_licencias.dart` | Funcional |
| Créditos por módulo y equipo base | `lib/ui/dialogo_creditos.dart` | Funcional |
| Centro de ayuda con 8 enlaces oficiales | `lib/ui/centro_ayuda.dart` | Funcional |
| Panel lateral del módulo | `lib/ui/vista_ayuda.dart` | Funcional |
| Punto de conexión con el shell | `lib/ui/acciones_ayuda.dart` + `AccionesAyuda` | Funcional |
| Prototipo navegable para presentación | `demo/index.html` | Listo |

La interfaz sigue la identidad visual del IDE: azul `#1B3A5C`, verde
`#008A00`, tipografía del sistema y tarjetas claras.

---

## 2. Estructura

```text
modules/ayuda/
├── README.md
├── demo/
│   └── index.html                 # Prototipo navegable (abre en cualquier navegador)
├── docs/
│   └── capturas/                  # Evidencias visuales de la demo
└── frontend/
    ├── pubspec.yaml               # Paquete ayuda_ui
    ├── analysis_options.yaml
    ├── lib/
    │   ├── ayuda_ui.dart          # API pública del paquete
    │   ├── modulo_ayuda.dart      # Implementa ModuloIde
    │   ├── contenido/
    │   │   └── contenido_ayuda.dart   # FAQ, enlaces, licencia y créditos
    │   └── ui/
    │       ├── acciones_ayuda.dart    # Conecta el módulo con el menú
    │       ├── centro_ayuda.dart
    │       ├── componentes.dart       # Paleta, logo, botones, avatares
    │       ├── dialogo_creditos.dart
    │       ├── dialogo_faq.dart
    │       ├── dialogo_licencias.dart
    │       ├── ventana_acerca_de.dart
    │       └── vista_ayuda.dart
    └── test/
        └── contenido_ayuda_test.dart
```

---

## 3. Cómo se integra con el shell

El core no importa módulos. Para evitar una dependencia circular se agregó el
contrato `AccionesAyuda` en `core/frontend/lib/nucleo/acciones_ayuda.dart`:

```dart
class AccionesAyuda {
  const AccionesAyuda({
    this.abrirDocumentacion,
    this.abrirPreguntasFrecuentes,
    this.abrirAcercaDe,
  });

  final AccionAyuda? abrirDocumentacion;
  final AccionAyuda? abrirPreguntasFrecuentes;
  final AccionAyuda? abrirAcercaDe;
}
```

`LayoutPrincipal` recibe estas acciones como parámetro opcional y el menú
`Ayuda` las invoca. La aplicación las construye con el módulo:

```dart
// apps/ide/lib/main.dart
home: LayoutPrincipal(
  registro: registro,
  accionesAyuda: crearAccionesAyuda(),
),
```

Pasos que ya están aplicados en la rama:

1. `apps/ide/pubspec.yaml` declara `ayuda_ui` como dependencia de ruta.
2. `apps/ide/lib/nucleo/registro_modulos.dart` registra `ModuloAyuda()`.
3. `apps/ide/lib/main.dart` inyecta `crearAccionesAyuda()`.
4. `core/frontend/lib/ide_core.dart` exporta `AccionesAyuda`.
5. `layout_principal.dart` reemplaza el menú de prueba por el menú funcional.

---

## 4. Cómo ejecutar

```bash
cd apps/ide
flutter pub get
flutter run -d windows    # o -d chrome
```

Para analizar y probar solo el módulo:

```bash
cd modules/ayuda/frontend
flutter pub get
flutter analyze
flutter test
```

> Nota: `url_launcher` se agregó como dependencia del módulo para abrir los
> enlaces externos en el navegador del sistema.

---

## 5. Demo para la presentación

Abre `modules/ayuda/demo/index.html` con doble clic (Chrome, Edge o Firefox).
No requiere servidor ni conexión: todos los estilos e iconos están embebidos.

Recorrido sugerido:

1. **Menú Ayuda → Acerca de ESP32 IDE**: versión, descripción, licencia y
   botones a Créditos y Licencias.
2. **Créditos**: equipos por módulo, con estado y roles.
3. **Licencias**: texto MIT completo y botón Copiar.
4. **Preguntas frecuentes**: respuestas desplegables y enlaces de soporte.
5. **Documentación y guías**: centro de ayuda con los 8 enlaces oficiales.
6. **Módulo: Herramientas**: demuestra que el registro de módulos sigue
   funcionando y que Ayuda convive con los demás paneles.

Atajos: `F1` abre el centro de ayuda; `Esc` cierra la ventana superior.
Con `?tour=0` se oculta la pista inicial; con `?anim=0` se desactivan las
animaciones para capturas.

---

## 6. Contenido editorial

- **FAQ:** seis preguntas sobre puertos, drivers CP210x/CH340, modo BOOT,
  gestión de librerías, baudios y reporte de errores.
- **Licencia:** MIT 2026, con el texto de exención de responsabilidad.
- **Créditos:** Ayuda y documentación (Evelyn, Octavio, Leonardo), Editor
  (Víctor, César, Nathaniel), Compilación y carga (pendiente), Interfaz
  principal (pendiente) y Base del IDE (equipo GRIS).
- **Enlaces:** documentación de ESP-IDF, primeros pasos de ESP32, referencia
  de la API, drivers CP210x y CH340, esptool, repositorio y registro de
  componentes.

Todo el contenido está centralizado en `lib/contenido/contenido_ayuda.dart`
para que el equipo de documentación lo actualice sin tocar los widgets.

---

## 7. Criterios de aceptación del acta

| Criterio | Evidencia |
|---|---|
| Menú Ayuda integrado y visible | `layout_principal.dart` + captura `01_ide.png` |
| Enlaces web y documentación local sin 404 | 8 URLs oficiales verificadas + `url_launcher` |
| Ventana «Acerca de» con créditos y licencias | `02_acerca.png`, `03_creditos.png`, `04_licencias.png` |
| Pruebas de integración aprobadas | `flutter analyze` sin issues; `flutter test` 3/3 en la app (incluye abrir «Acerca de») y 5/5 en el módulo |

---

## 8. Siguientes pasos

1. **Hecho:** validar con Flutter 3.50.0 (`flutter analyze` sin issues y
   `flutter test` 3/3 en la app, 5/5 en el módulo).
2. Probar la apertura de enlaces en Windows y Chrome.
3. Validar el menú con el equipo de UI principal cuando integren su rama.
4. Agregar una prueba de widget para abrir el diálogo «Acerca de».
5. Reemplazar los estados «Pendiente» de los módulos cuando sus equipos
   publiquen avances.
