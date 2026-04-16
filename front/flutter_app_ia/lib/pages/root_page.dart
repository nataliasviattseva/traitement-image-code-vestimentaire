import 'package:flutter/material.dart';
import 'home_page.dart';
import 'camera_page.dart';
import 'alerts_page.dart';
import 'uploads_page.dart';

/// Badge counter for the Alertes tab
class AlertBadgeNotifier extends ChangeNotifier {
  int _count = 0;
  int get count => _count;

  void increment() {
    _count++;
    notifyListeners();
  }

  void reset() {
    _count = 0;
    notifyListeners();
  }
}

final alertBadgeNotifier = AlertBadgeNotifier();

/// Déclenche la bannière in-app depuis n'importe où (ex: alerts_page)
final alertPopupNotifier = ValueNotifier<Map<String, dynamic>?>(null);

class RootPage extends StatefulWidget {
  const RootPage({super.key});

  @override
  State<RootPage> createState() => _RootPageState();
}

class _RootPageState extends State<RootPage> {
  int _currentIndex = 0;
  Map<String, dynamic>? _pendingAlert;
  bool _showNotif = false;

  @override
  void initState() {
    super.initState();
    alertBadgeNotifier.addListener(_onBadgeChanged);
    alertPopupNotifier.addListener(_onNewAlert);
  }

  @override
  void dispose() {
    alertBadgeNotifier.removeListener(_onBadgeChanged);
    alertPopupNotifier.removeListener(_onNewAlert);
    super.dispose();
  }

  void _onBadgeChanged() {
    if (mounted) setState(() {});
  }

  void _onNewAlert() {
    final alert = alertPopupNotifier.value;
    if (alert == null) return;
    if (_currentIndex == 2) return; // déjà sur l'onglet Alertes

    setState(() {
      _pendingAlert = alert;
      _showNotif = true;
    });

    Future.delayed(const Duration(seconds: 4), () {
      if (mounted) setState(() => _showNotif = false);
    });
  }

  final List<Widget> _pages = const [
    HomePage(),
    CameraPage(),
    AlertsPage(),
    UploadsPage(),
  ];

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      body: Stack(
        children: [
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 280),
            transitionBuilder: (child, animation) => FadeTransition(
              opacity: animation,
              child: SlideTransition(
                position: Tween<Offset>(
                  begin: const Offset(0.02, 0),
                  end: Offset.zero,
                ).animate(animation),
                child: child,
              ),
            ),
            child: KeyedSubtree(
              key: ValueKey(_currentIndex),
              child: _pages[_currentIndex],
            ),
          ),

          // Bannière in-app
          AnimatedPositioned(
            duration: const Duration(milliseconds: 350),
            curve: Curves.easeOutBack,
            top: _showNotif ? 0 : -140,
            left: 0,
            right: 0,
            child: _AlertNotificationBanner(
              alert: _pendingAlert,
              onTap: () {
                setState(() {
                  _showNotif = false;
                  _currentIndex = 2;
                });
                alertBadgeNotifier.reset();
              },
              onDismiss: () => setState(() => _showNotif = false),
            ),
          ),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(
            top: BorderSide(
              color: isDark
                  ? Colors.white.withOpacity(0.07)
                  : Colors.black.withOpacity(0.07),
            ),
          ),
        ),
        child: NavigationBar(
          selectedIndex: _currentIndex,
          height: 70,
          backgroundColor: isDark ? const Color(0xFF0A0E1A) : Colors.white,
          indicatorColor: cs.primary.withOpacity(0.12),
          onDestinationSelected: (index) {
            setState(() => _currentIndex = index);
            if (index == 2) alertBadgeNotifier.reset();
          },
          destinations: [
            const NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home_rounded),
              label: 'Accueil',
            ),
            const NavigationDestination(
              icon: Icon(Icons.videocam_outlined),
              selectedIcon: Icon(Icons.videocam_rounded),
              label: 'Caméra',
            ),
            NavigationDestination(
              icon: ListenableBuilder(
                listenable: alertBadgeNotifier,
                builder: (_, __) => Badge(
                  isLabelVisible: alertBadgeNotifier.count > 0,
                  label: Text("${alertBadgeNotifier.count}"),
                  backgroundColor: cs.error,
                  child: const Icon(Icons.notifications_outlined),
                ),
              ),
              selectedIcon: const Icon(Icons.notifications_rounded),
              label: 'Alertes',
            ),
            const NavigationDestination(
              icon: Icon(Icons.photo_library_outlined),
              selectedIcon: Icon(Icons.photo_library_rounded),
              label: 'Historique',
            ),
          ],
        ),
      ),
    );
  }
}

class _AlertNotificationBanner extends StatelessWidget {
  final Map<String, dynamic>? alert;
  final VoidCallback onTap;
  final VoidCallback onDismiss;

  const _AlertNotificationBanner({
    this.alert,
    required this.onTap,
    required this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    if (alert == null) return const SizedBox.shrink();

    final type = (alert!["type"] ?? "ALERT").toString();
    final reason = (alert!["reason"] ?? "Non-conformité détectée").toString();
    final isAlert = type.toUpperCase() == "ALERT";

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
        child: GestureDetector(
          onTap: onTap,
          child: Material(
            borderRadius: BorderRadius.circular(18),
            elevation: 12,
            shadowColor: Colors.black38,
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(
                color: isAlert
                    ? const Color(0xFFEF4444)
                    : const Color(0xFF2563EB),
                borderRadius: BorderRadius.circular(18),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      isAlert
                          ? Icons.warning_amber_rounded
                          : Icons.info_outline,
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          isAlert
                              ? "⚠️ Non-conformité détectée"
                              : "Information",
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w800,
                            fontSize: 14,
                          ),
                        ),
                        Text(
                          reason,
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.85),
                            fontSize: 12,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  GestureDetector(
                    onTap: onDismiss,
                    child: Icon(
                      Icons.close_rounded,
                      color: Colors.white.withOpacity(0.7),
                      size: 20,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}