import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

/// Widget integrable en el shell Flutter existente. No crea un MaterialApp.
class PanelAzul extends StatefulWidget {
  final Uri apiBase;
  final ValueChanged<String>? onNavigate;
  const PanelAzul({super.key, required this.apiBase, this.onNavigate});
  @override
  State<PanelAzul> createState() => _PanelAzulState();
}

class _PanelAzulState extends State<PanelAzul> {
  static const sections = ['Archivo', 'Editar', 'Sketch', 'Herramientas', 'Ayuda'];
  final projectPath = TextEditingController();
  final messages = <Map<String, dynamic>>[];
  Timer? timer;
  String selected = 'Sketch';
  String filter = 'TODOS';
  String? jobId;
  String jobStatus = '';
  int lastId = 0;
  bool busy = false;

  Uri endpoint(String path, [Map<String, String>? query]) =>
      widget.apiBase.resolve('api/v1/azul/$path').replace(queryParameters: query);

  @override
  void initState() {
    super.initState();
    refresh();
    timer = Timer.periodic(const Duration(seconds: 2), (_) => refresh());
  }

  @override
  void dispose() {
    timer?.cancel();
    projectPath.dispose();
    super.dispose();
  }

  Future<void> refresh() async {
    try {
      final response = await http.get(endpoint('logs', {'after_id': '$lastId'}));
      if (response.statusCode != 200) return;
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      final items = (body['messages'] as List).cast<Map<String, dynamic>>();
      if (jobId != null) {
        final statusResponse = await http.get(endpoint('compile/$jobId'));
        if (statusResponse.statusCode == 200) {
          final status = (jsonDecode(statusResponse.body) as Map<String, dynamic>)['status'] as String;
          if (mounted) setState(() { jobStatus = status; busy = status == 'queued' || status == 'running'; });
          if (!busy) jobId = null;
        }
      }
      if (!mounted) return;
      setState(() {
        messages.addAll(items);
        if (messages.length > 1000) messages.removeRange(0, messages.length - 1000);
        if (items.isNotEmpty) lastId = items.last['id'] as int;
      });
    } catch (_) {
      // Se vuelve a intentar automáticamente; no bloquear la interfaz.
    }
  }

  Future<void> compile() async {
    if (busy || projectPath.text.trim().isEmpty) return;
    setState(() => busy = true);
    try {
      final response = await http.post(endpoint('compile'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'project_path': projectPath.text.trim()}));
      if (response.statusCode != 202) throw Exception('HTTP ${response.statusCode}: ${response.body}');
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      setState(() { jobId = data['job_id'] as String; jobStatus = 'queued'; });
    } catch (error) {
      if (mounted) {
        setState(() => busy = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final filtered = messages.where((m) => filter == 'TODOS' || m['level'] == filter).toList();
    return Row(children: [
      SizedBox(width: 180, child: ListView(children: sections.map((section) => ListTile(
        title: Text(section), selected: selected == section,
        onTap: () { setState(() => selected = section); widget.onNavigate?.call(section); },
      )).toList())),
      const VerticalDivider(width: 1),
      Expanded(child: Column(children: [
        Padding(padding: const EdgeInsets.all(12), child: Row(children: [
          Expanded(child: TextField(controller: projectPath,
              decoration: const InputDecoration(labelText: 'Ruta del proyecto en el servidor ESP-IDF'))),
          const SizedBox(width: 8),
          FilledButton(onPressed: busy ? null : compile, child: Text(busy ? 'Compilando...' : 'Compilar')),
        ])),
        if (jobStatus.isNotEmpty) Text('Estado: $jobStatus'),
        Row(children: [
          const SizedBox(width: 12), const Text('Log'), const SizedBox(width: 12),
          DropdownButton<String>(value: filter,
            items: ['TODOS', 'INFO', 'SUCCESS', 'WARNING', 'ERROR']
              .map((v) => DropdownMenuItem(value: v, child: Text(v))).toList(),
            onChanged: (v) { if (v != null) setState(() => filter = v); }),
          IconButton(onPressed: refresh, icon: const Icon(Icons.refresh), tooltip: 'Actualizar'),
          TextButton(onPressed: () => setState(() { messages.clear(); }), child: const Text('Limpiar vista')),
        ]),
        Expanded(child: ListView.builder(itemCount: filtered.length,
          itemBuilder: (_, i) => Padding(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
            child: SelectableText('[${filtered[i]['timestamp']}] [${filtered[i]['level']}] '
              '${filtered[i]['source']}: ${filtered[i]['message']}')))),
      ])),
    ]);
  }
}
