// Archivo: modules/editor/frontend/lib/ui/componentes/find_replace_bar.dart
import 'package:flutter/material.dart';
import '../../nucleo/search_manager.dart';

/// Barra flotante de busqueda y reemplazo (Find & Replace).
///
/// Responsabilidad asignada a Dev C (Nathaniel).
class FindReplaceBar extends StatefulWidget {
  const FindReplaceBar({
    super.key,
    required this.searchManager,
  });

  final SearchManager searchManager;

  @override
  State<FindReplaceBar> createState() => _FindReplaceBarState();
}

class _FindReplaceBarState extends State<FindReplaceBar> {
  final TextEditingController _findController = TextEditingController();
  final TextEditingController _replaceController = TextEditingController();
  bool _mostrarReemplazo = false;

  @override
  void initState() {
    super.initState();
    _findController.text = widget.searchManager.terminoBusqueda;
    _replaceController.text = widget.searchManager.terminoReemplazo;
  }

  @override
  void didUpdateWidget(covariant FindReplaceBar oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.searchManager.terminoBusqueda != _findController.text) {
      _findController.text = widget.searchManager.terminoBusqueda;
    }
  }

  @override
  void dispose() {
    _findController.dispose();
    _replaceController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final sm = widget.searchManager;

    return Container(
      margin: const EdgeInsets.only(top: 8, right: 16),
      padding: const EdgeInsets.all(8),
      width: 440,
      decoration: BoxDecoration(
        color: const Color(0xFF252526),
        borderRadius: BorderRadius.circular(6),
        boxShadow: const [
          BoxShadow(
            color: Colors.black38,
            blurRadius: 8,
            offset: Offset(0, 4),
          ),
        ],
        border: Border.all(color: const Color(0xFF454545)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Fila de búsqueda
          Row(
            children: [
              IconButton(
                icon: Icon(
                  _mostrarReemplazo
                      ? Icons.keyboard_arrow_down
                      : Icons.keyboard_arrow_right,
                  color: Colors.white70,
                  size: 18,
                ),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
                tooltip: 'Alternar reemplazo',
                onPressed: () {
                  setState(() => _mostrarReemplazo = !_mostrarReemplazo);
                },
              ),
              Expanded(
                child: SizedBox(
                  height: 28,
                  child: TextField(
                    controller: _findController,
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                    decoration: InputDecoration(
                      hintText: 'Buscar (Find)...',
                      hintStyle: const TextStyle(color: Colors.white38, fontSize: 12),
                      filled: true,
                      fillColor: const Color(0xFF3C3C3C),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 0),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(3),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    onChanged: (val) => sm.buscar(val),
                  ),
                ),
              ),
              const SizedBox(width: 6),
              // Conteo de coincidencias
              Text(
                sm.terminoBusqueda.isEmpty
                    ? ''
                    : (sm.totalCoincidencias > 0
                        ? '${sm.indiceActual + 1} de ${sm.totalCoincidencias}'
                        : 'Sin resultados'),
                style: TextStyle(
                  color: sm.totalCoincidencias > 0
                      ? Colors.white70
                      : Colors.orangeAccent,
                  fontSize: 11,
                ),
              ),
              const SizedBox(width: 6),
              // Botón mayúsculas
              IconButton(
                icon: Icon(
                  Icons.text_format,
                  size: 16,
                  color: sm.sensibleMayusculas ? Colors.blueAccent : Colors.white54,
                ),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
                tooltip: 'Coincidir mayúsculas / minúsculas',
                onPressed: () => sm.setSensibleMayusculas(!sm.sensibleMayusculas),
              ),
              // Botón palabra completa
              IconButton(
                icon: Icon(
                  Icons.space_bar,
                  size: 16,
                  color: sm.palabraCompleta ? Colors.blueAccent : Colors.white54,
                ),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
                tooltip: 'Solo palabras completas',
                onPressed: () => sm.setPalabraCompleta(!sm.palabraCompleta),
              ),
              // Botón Anterior
              IconButton(
                icon: const Icon(Icons.arrow_upward, size: 16, color: Colors.white70),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
                tooltip: 'Coincidencia anterior (Shift+F3)',
                onPressed: sm.findPrevious,
              ),
              // Botón Siguiente
              IconButton(
                icon: const Icon(Icons.arrow_downward, size: 16, color: Colors.white70),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
                tooltip: 'Siguiente coincidencia (F3)',
                onPressed: sm.findNext,
              ),
              // Botón Cerrar
              IconButton(
                icon: const Icon(Icons.close, size: 16, color: Colors.white54),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
                tooltip: 'Cerrar (Esc)',
                onPressed: () => sm.setBarraVisible(false),
              ),
            ],
          ),

          // Fila de reemplazo (opcional)
          if (_mostrarReemplazo) ...[
            const SizedBox(height: 6),
            Row(
              children: [
                const SizedBox(width: 24),
                Expanded(
                  child: SizedBox(
                    height: 28,
                    child: TextField(
                      controller: _replaceController,
                      style: const TextStyle(color: Colors.white, fontSize: 12),
                      decoration: InputDecoration(
                        hintText: 'Reemplazar por...',
                        hintStyle: const TextStyle(color: Colors.white38, fontSize: 12),
                        filled: true,
                        fillColor: const Color(0xFF3C3C3C),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 0),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(3),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      onChanged: (val) => sm.setTerminoReemplazo(val),
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                ElevatedButton(
                  onPressed: () => sm.replace(_replaceController.text),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0E639C),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    minimumSize: const Size(60, 26),
                  ),
                  child: const Text('Reemplazar', style: TextStyle(fontSize: 10)),
                ),
                const SizedBox(width: 4),
                ElevatedButton(
                  onPressed: () => sm.replaceAll(_replaceController.text),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0E639C),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    minimumSize: const Size(60, 26),
                  ),
                  child: const Text('Todo', style: TextStyle(fontSize: 10)),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
