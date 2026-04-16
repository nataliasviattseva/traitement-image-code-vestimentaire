import 'package:flutter/material.dart';
import '../services/supabase_service.dart';

class UploadsPage extends StatefulWidget {
  const UploadsPage({super.key});

  @override
  State<UploadsPage> createState() => _UploadsPageState();
}

class _UploadsPageState extends State<UploadsPage> {
  final supabaseService = SupabaseService();
  List<Map<String, dynamic>> uploads = [];
  bool loading = true;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    loadUploads();
  }

  Future<void> loadUploads() async {
    setState(() {
      loading = true;
      errorMessage = null;
    });
    try {
      final data = await supabaseService.getImages();
      if (!mounted) return;
      setState(() {
        uploads = data;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        errorMessage = e.toString();
        loading = false;
      });
    }
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
            child: Row(
              children: [
                Text(
                  "Historique",
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.w900,
                    letterSpacing: -0.5,
                    color: isDark ? Colors.white : const Color(0xFF0F172A),
                  ),
                ),
                if (uploads.isNotEmpty)
                  Container(
                    margin: const EdgeInsets.only(left: 10),
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 3),
                    decoration: BoxDecoration(
                      color: cs.primary.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      "${uploads.length}",
                      style: TextStyle(
                        color: cs.primary,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                const Spacer(),
                GestureDetector(
                  onTap: loadUploads,
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: isDark
                          ? Colors.white.withOpacity(0.06)
                          : Colors.black.withOpacity(0.05),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      Icons.refresh_rounded,
                      size: 20,
                      color: isDark ? Colors.white54 : Colors.black45,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 12),

        Expanded(
          child: loading
              ? const Center(child: CircularProgressIndicator())
              : errorMessage != null
                  ? _ErrorState(message: errorMessage!, onRetry: loadUploads)
                  : uploads.isEmpty
                      ? _EmptyState(isDark: isDark)
                      : RefreshIndicator(
                          onRefresh: loadUploads,
                          child: ListView.separated(
                            padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
                            itemCount: uploads.length,
                            separatorBuilder: (_, __) =>
                                const SizedBox(height: 12),
                            itemBuilder: (_, index) {
                              final item = uploads[index];
                              final imageUrl = (item['url'] ?? '').toString();
                              final createdAt =
                                  (item['uploaded_at'] ?? '').toString();
                              final traite = item['traite'];
                              final notifie = item['notifie'];
                              final cloudinaryId =
                                  (item['cloudinary_id'] ?? '').toString();

                              return _UploadCard(
                                imageUrl: imageUrl,
                                date: formatDate(createdAt),
                                traite: traite == true,
                                notifie: notifie == true,
                                cloudinaryId: cloudinaryId,
                                isDark: isDark,
                                cs: cs,
                              );
                            },
                          ),
                        ),
        ),
      ],
    );
  }
}

// ── Upload Card ───────────────────────────────────────────────────────────────

class _UploadCard extends StatelessWidget {
  final String imageUrl;
  final String date;
  final bool traite;
  final bool notifie;
  final String cloudinaryId;
  final bool isDark;
  final ColorScheme cs;

  const _UploadCard({
    required this.imageUrl,
    required this.date,
    required this.traite,
    required this.notifie,
    required this.cloudinaryId,
    required this.isDark,
    required this.cs,
  });

  void _showFullscreen(BuildContext context) {
    Navigator.of(context).push(
      PageRouteBuilder(
        opaque: false,
        barrierColor: Colors.black87,
        pageBuilder: (_, __, ___) =>
            _FullscreenImagePage(imageUrl: imageUrl, tag: 'upload_$imageUrl'),
        transitionsBuilder: (_, anim, __, child) =>
            FadeTransition(opacity: anim, child: child),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF111827) : Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isDark
              ? Colors.white.withOpacity(0.06)
              : Colors.black.withOpacity(0.06),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Image cliquable
          GestureDetector(
            onTap: () => _showFullscreen(context),
            child: Hero(
              tag: 'upload_$imageUrl',
              child: ClipRRect(
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(20),
                  topRight: Radius.circular(20),
                ),
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
                          child: Center(
                            child: Icon(
                              Icons.broken_image_outlined,
                              color: isDark ? Colors.white24 : Colors.black26,
                              size: 32,
                            ),
                          ),
                        ),
                      ),
                      // Icône loupe
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

          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      Icons.access_time_rounded,
                      size: 14,
                      color: isDark ? Colors.white38 : Colors.black38,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      date,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: isDark
                            ? Colors.white70
                            : const Color(0xFF374151),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 12),

                Row(
                  children: [
                    _Badge(
                      icon: traite
                          ? Icons.check_circle_outline_rounded
                          : Icons.hourglass_empty_rounded,
                      label: traite ? "Traitée" : "En attente",
                      color: traite
                          ? const Color(0xFF10B981)
                          : const Color(0xFFF59E0B),
                      isDark: isDark,
                    ),
                    const SizedBox(width: 8),
                    _Badge(
                      icon: notifie
                          ? Icons.notifications_active_rounded
                          : Icons.notifications_none_rounded,
                      label: notifie ? "Notifiée" : "Non notifiée",
                      color: notifie
                          ? const Color(0xFF2563EB)
                          : (isDark ? Colors.white38 : Colors.black38),
                      isDark: isDark,
                    ),
                  ],
                ),

                const SizedBox(height: 10),

                Text(
                  "ID : $cloudinaryId",
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 11,
                    color: isDark ? Colors.white24 : Colors.black26,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Fullscreen viewer ─────────────────────────────────────────────────────────

class _FullscreenImagePage extends StatelessWidget {
  final String imageUrl;
  final String tag;

  const _FullscreenImagePage({required this.imageUrl, required this.tag});

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
              Center(
                child: Hero(
                  tag: tag,
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

              // Hint
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

// ── Widgets ───────────────────────────────────────────────────────────────────

class _Badge extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final bool isDark;

  const _Badge({
    required this.icon,
    required this.label,
    required this.color,
    required this.isDark,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: color),
          const SizedBox(width: 5),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final bool isDark;
  const _EmptyState({required this.isDark});

  @override
  Widget build(BuildContext context) {
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
              Icons.photo_library_outlined,
              size: 36,
              color: isDark ? Colors.white30 : Colors.black26,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            "Aucune image",
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 16,
              color: isDark ? Colors.white54 : Colors.black45,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            "Les images envoyées apparaîtront ici",
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

class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorState({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline_rounded, color: cs.error, size: 40),
            const SizedBox(height: 16),
            Text(
              "Erreur de chargement",
              style: TextStyle(
                fontWeight: FontWeight.w800,
                fontSize: 16,
                color: cs.error,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12,
                color: cs.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 20),
            OutlinedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text("Réessayer"),
            ),
          ],
        ),
      ),
    );
  }
}