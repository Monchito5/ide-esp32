// Archivo: modules/editor/frontend/lib/ui/vistas/vista_editor.dart
import 'package:flutter/material.dart';
import '../../nucleo/editor_state.dart';
import '../../nucleo/shortcut_manager.dart';
import '../../servicios/api_editor.dart';
import '../componentes/dialogo_ir_a_linea.dart';
import '../componentes/dialogo_reemplazar_archivos.dart';
import '../componentes/find_replace_bar.dart';
import '../componentes/menu_edit_widget.dart';

/// Vista principal del modulo de edicion de codigo (Equipo Rojo).
///
/// Integra la barra de menus, atajos, resaltado de sintaxis, busqueda/reemplazo
/// y las utilidades completas requeridas para Arduino IDE 2.3.10.
class VistaEditor extends StatefulWidget {
  const VistaEditor({
    super.key,
    required this.editorState,
    required this.api,
  });

  final EditorState editorState;
  final ApiEditor api;

  @override
  State<VistaEditor> createState() => _VistaEditorState();
}

class _VistaEditorState extends State<VistaEditor> {
  final ScrollController _scrollControllerTexto = ScrollController();
  final ScrollController _scrollControllerLineas = ScrollController();

  @override
  void initState() {
    super.initState();
    // Sincronizar scroll entre el editor y la barra de números de línea
    _scrollControllerTexto.addListener(() {
      if (_scrollControllerLineas.hasClients &&
          _scrollControllerLineas.offset != _scrollControllerTexto.offset) {
        _scrollControllerLineas.jumpTo(_scrollControllerTexto.offset);
      }
    });
  }

  @override
  void dispose() {
    _scrollControllerTexto.dispose();
    _scrollControllerLineas.dispose();
    super.dispose();
  }

  void _abrirDialogoIrALinea() async {
    final linea = await DialogoIrALinea.mostrar(
      context,
      totalLineas: widget.editorState.totalLineas,
      lineaActual: widget.editorState.lineaActual,
    );
    if (linea != null) {
      widget.editorState.editManager.goToLine(linea);
    }
  }

  void _abrirDialogoReemplazarArchivos() {
    DialogoReemplazarArchivos.mostrar(
      context,
      api: widget.api,
      terminoInicial: widget.editorState.searchManager.terminoBusqueda,
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: widget.editorState,
      builder: (context, _) {
        final state = widget.editorState;
        final sm = state.searchManager;
        final em = state.editManager;
        final int totalLineas = state.totalLineas;

        return EditorShortcutWrapper(
          editorState: state,
          onGoToLineRequested: _abrirDialogoIrALinea,
          child: Scaffold(
            backgroundColor: const Color(0xFF1E1E1E), // Fondo oscuro VSCode
            body: Column(
              children: [
                // Barra de herramientas superior con menu Edit y botones rapidos
                Container(
                  color: const Color(0xFF2D2D2D),
                  height: 34,
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: Row(
                    children: [
                      // Menu desplegable Edit
                      MenuEditWidget(
                        editorState: state,
                        onGoToLineRequested: _abrirDialogoIrALinea,
                        onReplaceInFilesRequested: _abrirDialogoReemplazarArchivos,
                      ),
                      const VerticalDivider(width: 12, indent: 6, endIndent: 6, color: Colors.white24),
                      // Botones rápidos con tooltips y atajos
                      IconButton(
                        icon: const Icon(Icons.undo, size: 16, color: Colors.white70),
                        tooltip: 'Deshacer (Ctrl+Z)',
                        onPressed: em.canUndo() ? em.undo : null,
                      ),
                      IconButton(
                        icon: const Icon(Icons.redo, size: 16, color: Colors.white70),
                        tooltip: 'Rehacer (Ctrl+Y)',
                        onPressed: em.canRedo() ? em.redo : null,
                      ),
                      IconButton(
                        icon: const Icon(Icons.content_cut, size: 16, color: Colors.white70),
                        tooltip: 'Cortar (Ctrl+X)',
                        onPressed: em.cut,
                      ),
                      IconButton(
                        icon: const Icon(Icons.content_copy, size: 16, color: Colors.white70),
                        tooltip: 'Copiar (Ctrl+C)',
                        onPressed: em.copy,
                      ),
                      IconButton(
                        icon: const Icon(Icons.content_paste, size: 16, color: Colors.white70),
                        tooltip: 'Pegar (Ctrl+V)',
                        onPressed: em.paste,
                      ),
                      const VerticalDivider(width: 12, indent: 6, endIndent: 6, color: Colors.white24),
                      IconButton(
                        icon: const Icon(Icons.comment, size: 16, color: Colors.white70),
                        tooltip: 'Comentar / Descomentar (Ctrl+/)',
                        onPressed: em.toggleComment,
                      ),
                      IconButton(
                        icon: const Icon(Icons.format_indent_increase, size: 16, color: Colors.white70),
                        tooltip: 'Aumentar sangría (Ctrl+])',
                        onPressed: em.increaseIndent,
                      ),
                      IconButton(
                        icon: const Icon(Icons.format_indent_decrease, size: 16, color: Colors.white70),
                        tooltip: 'Disminuir sangría (Ctrl+[)',
                        onPressed: em.decreaseIndent,
                      ),
                      IconButton(
                        icon: const Icon(Icons.format_align_left, size: 16, color: Colors.greenAccent),
                        tooltip: 'Formato automático (Shift+Alt+F)',
                        onPressed: em.autoFormatLocal,
                      ),
                      const VerticalDivider(width: 12, indent: 6, endIndent: 6, color: Colors.white24),
                      IconButton(
                        icon: const Icon(Icons.search, size: 16, color: Colors.white70),
                        tooltip: 'Buscar / Reemplazar (Ctrl+F)',
                        onPressed: () => sm.setBarraVisible(!sm.barraVisible),
                      ),
                      IconButton(
                        icon: const Icon(Icons.arrow_forward, size: 16, color: Colors.white70),
                        tooltip: 'Ir a línea... (Ctrl+G)',
                        onPressed: _abrirDialogoIrALinea,
                      ),
                      const Spacer(),
                      // Control visual de tamaño de fuente
                      IconButton(
                        icon: const Icon(Icons.remove, size: 14, color: Colors.white70),
                        tooltip: 'Reducir tamaño de fuente (Ctrl+-)',
                        onPressed: state.decreaseFontSize,
                      ),
                      Text(
                        '${state.tamanioFuente.toInt()} pt',
                        style: const TextStyle(fontSize: 11, color: Colors.white70),
                      ),
                      IconButton(
                        icon: const Icon(Icons.add, size: 14, color: Colors.white70),
                        tooltip: 'Aumentar tamaño de fuente (Ctrl++)',
                        onPressed: state.increaseFontSize,
                      ),
                      const SizedBox(width: 8),
                    ],
                  ),
                ),

                const Divider(height: 1, thickness: 1, color: Color(0xFF333333)),

                // Área de edición con barra de números de línea sincronizada
                Expanded(
                  child: Stack(
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Columna de números de línea dinámica
                          Container(
                            width: 46,
                            color: const Color(0xFF1E1E1E),
                            child: ListView.builder(
                              controller: _scrollControllerLineas,
                              padding: const EdgeInsets.only(top: 8, bottom: 8),
                              physics: const NeverScrollableScrollPhysics(),
                              itemCount: totalLineas,
                              itemBuilder: (context, index) {
                                final int numLinea = index + 1;
                                final bool esLineaActiva = numLinea == state.lineaActual;

                                return Container(
                                  height: state.tamanioFuente * 1.5,
                                  alignment: Alignment.centerRight,
                                  padding: const EdgeInsets.only(right: 8),
                                  child: Text(
                                    '$numLinea',
                                    style: TextStyle(
                                      color: esLineaActiva
                                          ? Colors.white
                                          : const Color(0xFF858585),
                                      fontSize: state.tamanioFuente * 0.85,
                                      fontFamily: 'monospace',
                                      fontWeight: esLineaActiva
                                          ? FontWeight.bold
                                          : FontWeight.normal,
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),

                          const VerticalDivider(width: 1, thickness: 1, color: Color(0xFF333333)),

                          // Editor de texto enriquecido con resaltado de sintaxis
                          Expanded(
                            child: SingleChildScrollView(
                              controller: _scrollControllerTexto,
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                              child: TextField(
                                controller: state.controller,
                                maxLines: null,
                                keyboardType: TextInputType.multiline,
                                style: TextStyle(
                                  fontFamily: 'monospace',
                                  fontSize: state.tamanioFuente,
                                  height: 1.5,
                                  color: const Color(0xFFD4D4D4),
                                ),
                                decoration: const InputDecoration(
                                  isDense: true,
                                  border: InputBorder.none,
                                  contentPadding: EdgeInsets.zero,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),

                      // Barra flotante de búsqueda y reemplazo (si está visible)
                      if (sm.barraVisible)
                        Positioned(
                          top: 0,
                          right: 12,
                          child: FindReplaceBar(searchManager: sm),
                        ),
                    ],
                  ),
                ),

                const Divider(height: 1, thickness: 1, color: Color(0xFF333333)),

                // Barra inferior de estado del editor
                Container(
                  color: const Color(0xFF007ACC), // Azul estilo VS Code
                  height: 22,
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: Row(
                    children: [
                      Text(
                        'Ln ${state.lineaActual}, Col ${state.columnaActual}',
                        style: const TextStyle(fontSize: 11, color: Colors.white),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        '${state.totalCaracteres} caracteres',
                        style: const TextStyle(fontSize: 11, color: Colors.white70),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        'Espacios: ${em.tamanoTabulacion}',
                        style: const TextStyle(fontSize: 11, color: Colors.white70),
                      ),
                      const Spacer(),
                      Text(
                        'Zoom: ${(state.tamanioFuente / 14.0 * 100).toInt()}%',
                        style: const TextStyle(fontSize: 11, color: Colors.white70),
                      ),
                      const SizedBox(width: 12),
                      const Text(
                        'UTF-8',
                        style: TextStyle(fontSize: 11, color: Colors.white70),
                      ),
                      const SizedBox(width: 12),
                      const Text(
                        'C/C++ (ESP32-S3)',
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
