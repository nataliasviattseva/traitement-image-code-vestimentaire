import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../widgets/alert_form_sheet.dart';
import 'root_page.dart';

class AlertsPage extends StatefulWidget {
  const AlertsPage({super.key});

  @override
  State<AlertsPage> createState() => _AlertsPageState();
}

class _AlertsPageState extends State<AlertsPage> {
  final _supabase = Supabase.instance.client;

  final List<Map<String, dynamic>> alerts = [];
  String _connectionStatus = "Connexion...";
  RealtimeChannel? _channel;

  @override
  void initState() {
    super.initState();
    _loadExistingAlerts();
    _subscribeToAlerts();
  }

  Future<void> _loadExistingAlerts() async {
    try {
      // alertes → images → violations (via image_id)
      final data = await _supabase
          .from('alertes')
          .select('''
            *,
            images (
              url,
              cloudinary_id,
              violations (
                classe,
                confiance
              )
            )
          ''')
          .order('envoye_at', ascending: false)
          .limit(50);

      if (!mounted) return;
      setState(() {
        alerts.clear();
        alerts.addAll(List<Map<String, dynamic>>.from(data));
        _connectionStatus = "Connecté";
      });
    } catch (e) {
      print('❌ Erreur chargement alertes : $e');
      if (!mounted) return;
      setState(() => _connectionStatus = "Erreur : $e");
    }
  }

  void _subscribeToAlerts() {
    _channel = _supabase
        .channel('alertes_realtime')
        .onPostgresChanges(
          event: PostgresChangeEvent.all,
          schema: 'public',
          table: 'alertes',
          callback: (payload) async {
            print('🔴 Realtime reçu : ${payload.newRecord}');
            if (!mounted) return;

            final newAlert = Map<String, dynamic>.from(payload.newRecord);
            final imageId = newAlert['image_id'];

            if (imageId != null) {
              try {
                // Récupère image + violations en passant par images
                final imageData = await _supabase
                    .from('images')
                    .select('''
                      url,
                      cloudinary_id,
                      violations (
                        classe,
                        confiance
                      )
                    ''')
                    .eq('id', imageId)
                    .single();
                newAlert['images'] = imageData;
              } catch (e) {
                print('⚠️ Erreur enrichissement : $e');
              }
            }

            setState(() {
              alerts.insert(0, newAlert);
              _connectionStatus = "Connecté";
            });

            alertBadgeNotifier.increment();
            alertPopupNotifier.value = newAlert;
            _showAlertForm(newAlert);
          },
        )
        .subscribe((status, [error]) {
          print('📡 Realtime status : $status — error : $error');
          if (!mounted) return;
          setState(() {
            if (status == RealtimeSubscribeStatus.subscribed) {
              _connectionStatus = "Connecté";
            } else if (status == RealtimeSubscribeStatus.closed) {
              _connectionStatus = "Déconnecté";
            } else if (error != null) {
              _connectionStatus = "Erreur";
            }
          });
        });
  }

  void _showAlertForm(Map<String, dynamic> alert) {
    Future.delayed(const Duration(milliseconds: 600), () {
      if (!mounted) return;
      showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        backgroundColor: Colors.transparent,
        builder: (_) => AlertFormSheet(alert: alert),
      );
    });
  }

  void _simulateAlert() {
    final fakeAlert = {
      "type": "email",
      "statut": "sent",
      "envoye_at": DateTime.now().toIso8601String(),
      "images": {
        "url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400",
        "violations": [
          {"classe": "Short", "confiance": 0.92}
        ],
      },
    };
    setState(() => alerts.insert(0, fakeAlert));
    alertBadgeNotifier.increment();
    alertPopupNotifier.value = fakeAlert;
    _showAlertForm(fakeAlert);
  }

  @override
  void dispose() {
    _channel?.unsubscribe();
    super.dispose();
  }

  Color get _statusColor {
    if (_connectionStatus == "Connecté") return const Color(0xFF10B981);
    if (_connectionStatus.contains("Erreur") ||
        _connectionStatus == "Déconnecté") return const Color(0xFFEF4444);
    return const Color(0xFFF59E0B);
  }

  String formatDate(String? iso) {
    if (iso == null || iso.isEmpty) return "–";
    final dt = DateTime.tryParse(iso);
    if (dt == null) return iso;
    return "${dt.day.toString().padLeft(2, '0')}/"
        "${dt.month.toString().padLeft(2, '0')}/"
        "${dt.year}  "
        "${dt.hour.toString().padLeft(2, '0')}:"
        "${dt.minute.toString().padLeft(2, '0')}";
  }

  static String getClasse(Map<String, dynamic> alert) {
    final img = alert['images'];
    if (img is! Map) return '';
    final v = img['violations'];
    if (v is List && v.isNotEmpty) return (v.first['classe'] ?? '').toString();
    if (v is Map) return (v['classe'] ?? '').toString();
    return '';
  }

  static double? getConfiance(Map<String, dynamic> alert) {
    final img = alert['images'];
    if (img is! Map) return null;
    final v = img['violations'];
    if (v is List && v.isNotEmpty && v.first['confiance'] != null) {
      return (v.first['confiance'] as num).toDouble();
    }
    if (v is Map && v['confiance'] != null) {
      return (v['confiance'] as num).toDouble();
    }
    return null;
  }

  static String getImageUrl(Map<String, dynamic> alert) {
    final img = alert['images'];
    if (img is Map) return (img['url'] ?? '').toString();
    return '';
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Column(
      children: [
        SafeArea(
          bottom: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
            child: Column(
              children: [
                Row(
                  children: [
                    Text(
                      "Alertes",
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.5,
                        color: isDark ? Colors.white : const Color(0xFF0F172A),
                      ),
                    ),
                    if (alerts.isNotEmpty)
                      Container(
                        margin: const EdgeInsets.only(left: 10),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 3),
                        decoration: BoxDecoration(
                          color: cs.error,
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          "${alerts.length}",
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    const Spacer(),

                    GestureDetector(
                      onTap: _simulateAlert,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: const Color(0xFFEF4444).withOpacity(0.12),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(
                            color: const Color(0xFFEF4444).withOpacity(0.3),
                          ),
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.play_arrow_rounded,
                                size: 16, color: Color(0xFFEF4444)),
                            SizedBox(width: 4),
                            Text(
                              "Simuler",
                              style: TextStyle(
                                color: Color(0xFFEF4444),
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    if (alerts.isNotEmpty) ...[
                      const SizedBox(width: 8),
                      GestureDetector(
                        onTap: () => setState(() => alerts.clear()),
                        child: Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: isDark
                                ? Colors.white.withOpacity(0.06)
                                : Colors.black.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Icon(
                            Icons.delete_outline_rounded,
                            size: 20,
                            color: isDark ? Colors.white54 : Colors.black45,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),

                const SizedBox(height: 14),

                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF111827) : Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: _statusColor.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      _StatusDot(
                        color: _statusColor,
                        animate: _connectionStatus == "Connexion...",
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          "Supabase Realtime · $_connectionStatus",
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: isDark
                                ? Colors.white.withOpacity(0.7)
                                : const Color(0xFF374151),
                          ),
                        ),
                      ),
                      GestureDetector(
                        onTap: () {
                          _channel?.unsubscribe();
                          _loadExistingAlerts();
                          _subscribeToAlerts();
                        },
                        child: Icon(
                          Icons.refresh_rounded,
                          size: 18,
                          color: isDark
                              ? Colors.white.withOpacity(0.3)
                              : Colors.black26,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 12),

        Expanded(
          child: alerts.isEmpty
              ? _EmptyState(connected: _connectionStatus == "Connecté")
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
                  itemCount: alerts.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (_, i) => _AlertCard(
                    alert: alerts[i],
                    index: i,
                    formatDate: formatDate,
                    getClasse: getClasse,
                    getConfiance: getConfiance,
                    getImageUrl: getImageUrl,
                    onReport: () => _showAlertForm(alerts[i]),
                  ),
                ),
        ),
      ],
    );
  }
}

// ── Widgets ──────────────────────────────────────────────────────────────────

class _StatusDot extends StatefulWidget {
  final Color color;
  final bool animate;
  const _StatusDot({required this.color, required this.animate});

  @override
  State<_StatusDot> createState() => _StatusDotState();
}

class _StatusDotState extends State<_StatusDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c;
  late final Animation<double> _a;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 900));
    _a = Tween<double>(begin: 0.4, end: 1.0)
        .animate(CurvedAnimation(parent: _c, curve: Curves.easeInOut));
    if (widget.animate) _c.repeat(reverse: true);
  }

  @override
  void didUpdateWidget(_StatusDot old) {
    super.didUpdateWidget(old);
    if (widget.animate && !_c.isAnimating) {
      _c.repeat(reverse: true);
    } else if (!widget.animate && _c.isAnimating) {
      _c.stop();
      _c.value = 1.0;
    }
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _a,
      child: Container(
        width: 8,
        height: 8,
        decoration:
            BoxDecoration(color: widget.color, shape: BoxShape.circle),
      ),
    );
  }
}

class _AlertCard extends StatefulWidget {
  final Map<String, dynamic> alert;
  final int index;
  final String Function(String?) formatDate;
  final String Function(Map<String, dynamic>) getClasse;
  final double? Function(Map<String, dynamic>) getConfiance;
  final String Function(Map<String, dynamic>) getImageUrl;
  final VoidCallback onReport;

  const _AlertCard({
    required this.alert,
    required this.index,
    required this.formatDate,
    required this.getClasse,
    required this.getConfiance,
    required this.getImageUrl,
    required this.onReport,
  });

  @override
  State<_AlertCard> createState() => _AlertCardState();
}

class _AlertCardState extends State<_AlertCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c;
  late final Animation<double> _fade;
  late final Animation<Offset> _slide;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 400));
    _fade = CurvedAnimation(parent: _c, curve: Curves.easeOut);
    _slide = Tween<Offset>(
      begin: const Offset(0, -0.1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _c, curve: Curves.easeOut));

    if (widget.index == 0) {
      _c.forward();
    } else {
      _c.value = 1.0;
    }
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  void _showFullscreenImage(BuildContext ctx, String url) {
    Navigator.of(ctx).push(PageRouteBuilder(
      opaque: false,
      barrierColor: Colors.black87,
      pageBuilder: (_, __, ___) => _FullscreenImagePage(imageUrl: url),
      transitionsBuilder: (_, anim, __, child) =>
          FadeTransition(opacity: anim, child: child),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final type = (widget.alert["type"] ?? "email").toString();
    final statut = (widget.alert["statut"] ?? "").toString();
    final envoyeAt = (widget.alert["envoye_at"] ?? "").toString();
    final classe = widget.getClasse(widget.alert);
    final confiance = widget.getConfiance(widget.alert);
    final imageUrl = widget.getImageUrl(widget.alert);

    const color = Color(0xFFEF4444);

    return FadeTransition(
      opacity: _fade,
      child: SlideTransition(
        position: _slide,
        child: Container(
          decoration: BoxDecoration(
            color: isDark ? const Color(0xFF111827) : Colors.white,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: color.withOpacity(0.25)),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.warning_amber_rounded,
                        color: color,
                        size: 22,
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  "Non-conformité détectée",
                                  style: TextStyle(
                                    fontWeight: FontWeight.w800,
                                    fontSize: 14,
                                    color: isDark
                                        ? Colors.white
                                        : const Color(0xFF0F172A),
                                  ),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: color.withOpacity(0.12),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  type.toUpperCase(),
                                  style: const TextStyle(
                                    color: color,
                                    fontSize: 10,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 0.5,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          if (classe.isNotEmpty)
                            _InfoRow(
                              icon: Icons.category_outlined,
                              label: "Violation",
                              value: classe,
                              isDark: isDark,
                            ),
                          if (confiance != null)
                            _InfoRow(
                              icon: Icons.speed_outlined,
                              label: "Confiance",
                              value: "${(confiance * 100).toStringAsFixed(0)}%",
                              isDark: isDark,
                            ),
                          _InfoRow(
                            icon: Icons.check_circle_outline,
                            label: "Statut",
                            value: statut,
                            isDark: isDark,
                          ),
                          _InfoRow(
                            icon: Icons.access_time_rounded,
                            label: "Envoyée",
                            value: widget.formatDate(envoyeAt),
                            isDark: isDark,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),

                if (imageUrl.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  GestureDetector(
                    onTap: () => _showFullscreenImage(context, imageUrl),
                    child: Hero(
                      tag: imageUrl,
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: AspectRatio(
                          aspectRatio: 16 / 9,
                          child: Stack(
                            fit: StackFit.expand,
                            children: [
                              Image.network(
                                imageUrl,
                                fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => Container(
                                  color: isDark
                                      ? Colors.white.withOpacity(0.05)
                                      : Colors.black12,
                                  child: const Center(
                                    child: Icon(Icons.broken_image_outlined,
                                        color: Colors.white38),
                                  ),
                                ),
                              ),
                              // Overlay loupe
                              Positioned(
                                bottom: 8,
                                right: 8,
                                child: Container(
                                  padding: const EdgeInsets.all(6),
                                  decoration: BoxDecoration(
                                    color: Colors.black.withOpacity(0.5),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: const Icon(
                                    Icons.zoom_in_rounded,
                                    color: Colors.white,
                                    size: 18,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ],

                const SizedBox(height: 12),

                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: widget.onReport,
                    icon: const Icon(Icons.send_rounded, size: 16),
                    label: const Text("Signaler à l'admin"),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: color,
                      side: BorderSide(color: color.withOpacity(0.4)),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 10),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final bool isDark;

  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.isDark,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon,
              size: 13,
              color: isDark ? Colors.white30 : Colors.black26),
          const SizedBox(width: 5),
          Text(
            "$label : ",
            style: TextStyle(
              fontSize: 12,
              color: isDark ? Colors.white38 : Colors.black38,
              fontWeight: FontWeight.w500,
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                fontSize: 12,
                color: isDark
                    ? Colors.white.withOpacity(0.6)
                    : const Color(0xFF374151),
                fontWeight: FontWeight.w600,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final bool connected;
  const _EmptyState({required this.connected});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: isDark
                  ? Colors.white.withOpacity(0.05)
                  : Colors.black.withOpacity(0.04),
              shape: BoxShape.circle,
            ),
            child: Icon(
              connected
                  ? Icons.notifications_none_rounded
                  : Icons.wifi_off_rounded,
              size: 40,
              color: isDark ? Colors.white30 : Colors.black26,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            connected ? "Aucune alerte" : "Connexion en cours...",
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 16,
              color: isDark ? Colors.white54 : Colors.black45,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            connected
                ? "Les alertes apparaîtront ici en temps réel"
                : "Connexion à Supabase Realtime...",
            style: TextStyle(
              fontSize: 13,
              color: isDark ? Colors.white30 : Colors.black26,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Fullscreen image viewer ───────────────────────────────────────────────────

class _FullscreenImagePage extends StatelessWidget {
  final String imageUrl;
  const _FullscreenImagePage({required this.imageUrl});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: GestureDetector(
        onTap: () => Navigator.of(context).pop(),
        child: Container(
          color: Colors.black87,
          width: double.infinity,
          height: double.infinity,
          child: Stack(
            children: [
              // Image centrée avec Hero
              Center(
                child: Hero(
                  tag: imageUrl,
                  child: InteractiveViewer(
                    minScale: 0.8,
                    maxScale: 4.0,
                    child: Image.network(
                      imageUrl,
                      fit: BoxFit.contain,
                      errorBuilder: (_, __, ___) => const Icon(
                        Icons.broken_image_outlined,
                        color: Colors.white38,
                        size: 60,
                      ),
                    ),
                  ),
                ),
              ),

              // Bouton fermer
              SafeArea(
                child: Align(
                  alignment: Alignment.topRight,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: GestureDetector(
                      onTap: () => Navigator.of(context).pop(),
                      child: Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.black.withOpacity(0.5),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.close_rounded,
                          color: Colors.white,
                          size: 22,
                        ),
                      ),
                    ),
                  ),
                ),
              ),

              // Hint pinch to zoom
              SafeArea(
                child: Align(
                  alignment: Alignment.bottomCenter,
                  child: Padding(
                    padding: const EdgeInsets.only(bottom: 32),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 7),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.4),
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: const Text(
                        "Pincez pour zoomer · Appuyez pour fermer",
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}