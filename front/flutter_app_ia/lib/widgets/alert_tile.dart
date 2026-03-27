import 'package:flutter/material.dart';

class AlertTile extends StatelessWidget {
  final Map<String, dynamic> alert;

  const AlertTile({super.key, required this.alert});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    final type = (alert["type"] ?? "ALERT").toString();
    final reason = (alert["reason"] ?? "unknown").toString();
    final confidence = alert["confidence"];
    final filename = (alert["filename"] ?? "").toString();

    final isAlert = type.toUpperCase() == "ALERT";

    return Card(
      child: ListTile(
        leading: Icon(
          isAlert ? Icons.warning_amber_rounded : Icons.info_outline,
          color: isAlert ? cs.error : cs.primary,
        ),
        title: Text(isAlert ? "Non-conformité détectée" : "Info"),
        subtitle: Text(
          "Raison: $reason\nConfiance: ${confidence ?? "-"}\nFichier: ${filename.isEmpty ? "-" : filename}",
        ),
        isThreeLine: true,
      ),
    );
  }
}
