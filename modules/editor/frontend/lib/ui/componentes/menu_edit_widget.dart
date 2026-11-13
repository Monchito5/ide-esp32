// Archivo: modules/editor/frontend/lib/ui/componentes/menu_edit_widget.dart
import 'package:flutter/material.dart';
import '../../nucleo/editor_state.dart';

/// Menu desplegable "Edit" conforme a la seccion 11 del documento de Equipo Rojo.
class MenuEditWidget extends StatelessWidget {
  const MenuEditWidget({
    super.key,
    required this.editorState,
    required this.onGoToLineRequested,
    required this.onReplaceInFilesRequested,
  });

  final EditorState editorState;
  final VoidCallback onGoToLineRequested;
  final VoidCallback onReplaceInFilesRequested;

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<String>(
      tooltip: 'Menú Editar',
      child: const Padding(
        padding: EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        child: Text(
          'Editar',
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
        ),
      ),
      onSelected: (accion) async {
        final em = editorState.editManager;
        final sm = editorState.searchManager;

        switch (accion) {
          case 'undo':
            em.undo();
            break;
          case 'redo':
            em.redo();
            break;
          case 'cut':
            await em.cut();
            break;
          case 'copy':
            await em.copy();
            break;
          case 'paste':
            await em.paste();
            break;
          case 'selectAll':
            em.selectAll();
            break;
          case 'goToLine':
            onGoToLineRequested();
            break;
          case 'copyForForum':
            await em.copyForForum();
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Código copiado en formato Markdown para foro.'),
                  duration: Duration(seconds: 2),
                ),
              );
            }
            break;
          case 'comment':
            em.toggleComment();
            break;
          case 'increaseIndent':
            em.increaseIndent();
            break;
          case 'decreaseIndent':
            em.decreaseIndent();
            break;
          case 'autoFormat':
            em.autoFormatLocal();
            break;
          case 'find':
            sm.setBarraVisible(true);
            break;
          case 'findNext':
            sm.findNext();
            break;
          case 'findPrevious':
            sm.findPrevious();
            break;
          case 'useSelectionForFind':
            sm.useSelectionForFind();
            break;
          case 'replaceInFiles':
            onReplaceInFilesRequested();
            break;
          case 'increaseFontSize':
            editorState.increaseFontSize();
            break;
          case 'decreaseFontSize':
            editorState.decreaseFontSize();
            break;
        }
      },
      itemBuilder: (context) => [
        _item('undo', 'Deshacer (Undo)', 'Ctrl+Z', Icons.undo),
        _item('redo', 'Rehacer (Redo)', 'Ctrl+Y', Icons.redo),
        const PopupMenuDivider(),
        _item('cut', 'Cortar (Cut)', 'Ctrl+X', Icons.content_cut),
        _item('copy', 'Copiar (Copy)', 'Ctrl+C', Icons.content_copy),
        _item('paste', 'Pegar (Paste)', 'Ctrl+V', Icons.content_paste),
        _item('selectAll', 'Seleccionar todo', 'Ctrl+A', Icons.select_all),
        _item('goToLine', 'Ir a la línea...', 'Ctrl+G', Icons.arrow_forward),
        _item('copyForForum', 'Copiar para foro (Markdown)', '', Icons.forum),
        const PopupMenuDivider(),
        _item('comment', 'Comentar / Descomentar', 'Ctrl+/', Icons.comment),
        _item('increaseIndent', 'Aumentar sangría', 'Ctrl+]', Icons.format_indent_increase),
        _item('decreaseIndent', 'Disminuir sangría', 'Ctrl+[', Icons.format_indent_decrease),
        _item('autoFormat', 'Formato automático (Auto Format)', 'Shift+Alt+F', Icons.format_align_left),
        const PopupMenuDivider(),
        _item('find', 'Buscar (Find)', 'Ctrl+F', Icons.search),
        _item('findNext', 'Buscar siguiente', 'F3', Icons.arrow_downward),
        _item('findPrevious', 'Buscar anterior', 'Shift+F3', Icons.arrow_upward),
        _item('useSelectionForFind', 'Usar selección para buscar', 'Ctrl+E', Icons.find_in_page),
        _item('replaceInFiles', 'Reemplazar en archivos...', 'Ctrl+Shift+F', Icons.find_replace),
        const PopupMenuDivider(),
        _item('increaseFontSize', 'Aumentar tamaño de fuente', 'Ctrl++', Icons.zoom_in),
        _item('decreaseFontSize', 'Disminuir tamaño de fuente', 'Ctrl+-', Icons.zoom_out),
      ],
    );
  }

  PopupMenuItem<String> _item(String valor, String titulo, String atajo, IconData icono) {
    return PopupMenuItem<String>(
      value: valor,
      height: 32,
      child: Row(
        children: [
          Icon(icono, size: 16, color: Colors.blueGrey),
          const SizedBox(width: 8),
          Expanded(child: Text(titulo, style: const TextStyle(fontSize: 12))),
          if (atajo.isNotEmpty)
            Text(
              atajo,
              style: const TextStyle(fontSize: 11, color: Colors.grey),
            ),
        ],
      ),
    );
  }
}
