import 'package:flutter/material.dart';


class AlertFormSheet extends StatefulWidget {
  final Map<String, dynamic> alert;

  const AlertFormSheet({super.key, required this.alert});

  @override
  State<AlertFormSheet> createState() => _AlertFormSheetState();
}

class _AlertFormSheetState extends State<AlertFormSheet> {
  final _formKey = GlobalKey<FormState>();
  final _nomController = TextEditingController();
  final _prenomController = TextEditingController();
  final _classeController = TextEditingController();

  bool _sending = false;
  bool _sent = false;
  String? _errorMessage;

  

  @override
  void dispose() {
    _nomController.dispose();
    _prenomController.dispose();
    _classeController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _sending = true;
      _errorMessage = null;
    });

    try {
      final violation = (widget.alert['classe'] ??
              widget.alert['reason'] ??
              widget.alert['type'] ??
              'Inconnue')
          .toString();

      final imageUrl = (widget.alert['image_url'] ?? '').toString();

      double? confiance;
      final rawConf = widget.alert['confiance'] ?? widget.alert['confidence'];
      if (rawConf != null) confiance = (rawConf as num).toDouble();

     

      if (!mounted) return;
      setState(() {
        _sending = false;
        _sent = true;
      });

      await Future.delayed(const Duration(seconds: 2));
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _sending = false;
        _errorMessage = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final violation = (widget.alert['classe'] ??
            widget.alert['reason'] ??
            widget.alert['type'] ??
            'Inconnue')
        .toString();

    final confiance = widget.alert['confiance'] ?? widget.alert['confidence'];
    final imageUrl = (widget.alert['image_url'] ?? '').toString();

    return Container(
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF0F172A) : Colors.white,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(28),
          topRight: Radius.circular(28),
        ),
      ),
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 24,
        bottom: MediaQuery.of(context).viewInsets.bottom + 32,
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              // Handle
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: isDark
                        ? Colors.white.withOpacity(0.15)
                        : Colors.black.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(999),
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // Header
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFEF4444).withOpacity(0.12),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.warning_amber_rounded,
                      color: Color(0xFFEF4444),
                      size: 22,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Signaler une violation",
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w900,
                            color:
                                isDark ? Colors.white : const Color(0xFF0F172A),
                          ),
                        ),
                        Text(
                          "Un email sera envoyé à l'administrateur",
                          style: TextStyle(
                            fontSize: 12,
                            color: isDark
                                ? Colors.white38
                                : const Color(0xFF64748B),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 20),

              // Violation recap card
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFEF4444).withOpacity(0.08),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: const Color(0xFFEF4444).withOpacity(0.2),
                  ),
                ),
                child: Column(
                  children: [
                    _RecapRow(
                      label: "Violation",
                      value: violation,
                      isDark: isDark,
                    ),
                    if (confiance != null)
                      _RecapRow(
                        label: "Confiance",
                        value:
                            "${((confiance as num).toDouble() * 100).toStringAsFixed(0)}%",
                        isDark: isDark,
                      ),
                    if (imageUrl.isNotEmpty)
                      _RecapRow(
                        label: "Image",
                        value: imageUrl,
                        isDark: isDark,
                        isUrl: true,
                      ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Success state
              if (_sent) ...[
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF10B981).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: const Color(0xFF10B981).withOpacity(0.3),
                    ),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.check_circle_outline_rounded,
                          color: Color(0xFF10B981)),
                      SizedBox(width: 10),
                      Text(
                        "Email envoyé avec succès !",
                        style: TextStyle(
                          color: Color(0xFF10B981),
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ] else ...[
                // Form fields
                _FieldLabel(label: "Nom", isDark: isDark),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _nomController,
                  textCapitalization: TextCapitalization.words,
                  textInputAction: TextInputAction.next,
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? "Champ requis" : null,
                  decoration: _inputDeco(
                    hint: "Dupont",
                    icon: Icons.person_outline_rounded,
                    isDark: isDark,
                    cs: cs,
                  ),
                ),

                const SizedBox(height: 16),

                _FieldLabel(label: "Prénom", isDark: isDark),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _prenomController,
                  textCapitalization: TextCapitalization.words,
                  textInputAction: TextInputAction.next,
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? "Champ requis" : null,
                  decoration: _inputDeco(
                    hint: "Jean",
                    icon: Icons.badge_outlined,
                    isDark: isDark,
                    cs: cs,
                  ),
                ),

                const SizedBox(height: 16),

                _FieldLabel(label: "Classe", isDark: isDark),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _classeController,
                  textCapitalization: TextCapitalization.characters,
                  textInputAction: TextInputAction.done,
                  onFieldSubmitted: (_) => _submit(),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? "Champ requis" : null,
                  decoration: _inputDeco(
                    hint: "B2",
                    icon: Icons.school_outlined,
                    isDark: isDark,
                    cs: cs,
                  ),
                ),

                // Error
                if (_errorMessage != null) ...[
                  const SizedBox(height: 14),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: cs.error.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: cs.error.withOpacity(0.3)),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.error_outline, color: cs.error, size: 16),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _errorMessage!,
                            style: TextStyle(
                                color: cs.error,
                                fontSize: 12,
                                fontWeight: FontWeight.w500),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],

                const SizedBox(height: 24),

                // Buttons
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: _sending
                            ? null
                            : () => Navigator.of(context).pop(),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                          side: BorderSide(
                            color: isDark
                                ? Colors.white.withOpacity(0.15)
                                : Colors.black.withOpacity(0.12),
                          ),
                        ),
                        child: Text(
                          "Annuler",
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            color: isDark ? Colors.white54 : Colors.black45,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      flex: 2,
                      child: FilledButton(
                        onPressed: _sending ? null : _submit,
                        style: FilledButton.styleFrom(
                          backgroundColor: const Color(0xFFEF4444),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                        child: _sending
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.send_rounded,
                                      size: 16, color: Colors.white),
                                  SizedBox(width: 8),
                                  Text(
                                    "Envoyer à l'admin",
                                    style: TextStyle(
                                      fontWeight: FontWeight.w700,
                                      color: Colors.white,
                                    ),
                                  ),
                                ],
                              ),
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDeco({
    required String hint,
    required IconData icon,
    required bool isDark,
    required ColorScheme cs,
  }) {
    return InputDecoration(
      hintText: hint,
      hintStyle: TextStyle(
        color: isDark ? Colors.white.withOpacity(0.25) : Colors.black26,
      ),
      prefixIcon: Icon(
        icon,
        color: isDark ? Colors.white.withOpacity(0.4) : Colors.black38,
      ),
      filled: true,
      fillColor: isDark ? const Color(0xFF1C2333) : const Color(0xFFEEF2FF),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide.none,
      ),
    );
  }
}

class _FieldLabel extends StatelessWidget {
  final String label;
  final bool isDark;
  const _FieldLabel({required this.label, required this.isDark});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: isDark ? Colors.white.withOpacity(0.6) : const Color(0xFF374151),
        letterSpacing: 0.3,
      ),
    );
  }
}

class _RecapRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isDark;
  final bool isUrl;

  const _RecapRow({
    required this.label,
    required this.value,
    required this.isDark,
    this.isUrl = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "$label : ",
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: isDark ? Colors.white38 : Colors.black38,
            ),
          ),
          Expanded(
            child: Text(
              value,
              maxLines: isUrl ? 1 : 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: isUrl
                    ? const Color(0xFFEF4444)
                    : (isDark ? Colors.white70 : const Color(0xFF0F172A)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}