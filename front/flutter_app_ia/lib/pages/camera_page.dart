import 'dart:async';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import '../services/cloudinary_service.dart';
import '../services/supabase_service.dart';

class CameraPage extends StatefulWidget {
  const CameraPage({super.key});

  @override
  State<CameraPage> createState() => _CameraPageState();
}

class _CameraPageState extends State<CameraPage>
    with SingleTickerProviderStateMixin {
  CameraController? _controller;
  Timer? _timer;

  final cloudinary = CloudinaryService();
  final supabaseService = SupabaseService();

  bool _busy = false;
  bool _running = false;

  String _status = "Initialisation...";
  String? _lastUploadedUrl;
  int _uploadCount = 0;

  late final AnimationController _pulseController;
  late final Animation<double> _pulse;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _pulse = Tween<double>(begin: 1.0, end: 1.12).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    _pulseController.repeat(reverse: true);
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        setState(() => _status = "Aucune caméra détectée");
        return;
      }
      final backCam = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );
      final controller = CameraController(
        backCam,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );
      await controller.initialize();
      setState(() {
        _controller = controller;
        _status = "Caméra prête";
      });
    } catch (e) {
      setState(() => _status = "Erreur : $e");
    }
  }

  void _startAutoUpload() {
    if (_controller == null || !_controller!.value.isInitialized) return;
    _timer?.cancel();
    _timer = Timer.periodic(
      const Duration(seconds: 1),
      (_) => _captureAndUpload(),
    );
    setState(() {
      _running = true;
      _status = "Upload auto actif";
    });
  }

  void _pauseAutoUpload() {
    _timer?.cancel();
    setState(() {
      _running = false;
      _status = "Upload mis en pause";
    });
  }

  Future<void> _captureAndUpload() async {
    final c = _controller;
    if (c == null || !c.value.isInitialized || _busy) return;
    _busy = true;
    try {
      final shot = await c.takePicture();
      final uploadResult = await cloudinary.uploadImage(shot.path);
      final secureUrl = uploadResult['url']!;
      final cloudinaryId = uploadResult['cloudinary_id']!;
      await supabaseService.insertImage(
        url: secureUrl,
        cloudinaryId: cloudinaryId,
      );
      if (!mounted) return;
      setState(() {
        _lastUploadedUrl = secureUrl;
        _uploadCount += 1;
        _status = "Upload réussi ✓";
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _status = "Erreur : $e");
    } finally {
      _busy = false;
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _controller?.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final c = _controller;
    final size = MediaQuery.of(context).size;

    return Stack(
      children: [
        // Full screen camera preview
        SizedBox(
          width: size.width,
          height: size.height,
          child: (c == null || !c.value.isInitialized)
              ? Container(
                  color: Colors.black,
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const CircularProgressIndicator(color: Colors.white38),
                        const SizedBox(height: 16),
                        Text(
                          _status,
                          style: const TextStyle(
                            color: Colors.white54,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                )
              : CameraPreview(c),
        ),

        // Top overlay — header
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          child: Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.black54, Colors.transparent],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
            child: SafeArea(
              bottom: false,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 16),
                child: Row(
                  children: [
                    const Text(
                      "Caméra",
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.5,
                      ),
                    ),
                    const Spacer(),
                    // LIVE badge
                    ScaleTransition(
                      scale: _running ? _pulse : const AlwaysStoppedAnimation(1.0),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: _running
                              ? const Color(0xFFEF4444)
                              : Colors.white.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(
                            color: _running
                                ? Colors.transparent
                                : Colors.white.withOpacity(0.25),
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (_running)
                              Container(
                                width: 6,
                                height: 6,
                                margin: const EdgeInsets.only(right: 6),
                                decoration: const BoxDecoration(
                                  color: Colors.white,
                                  shape: BoxShape.circle,
                                ),
                              ),
                            Text(
                              _running ? "LIVE" : "PAUSE",
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 1,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),

        // Scan frame overlay (visible only when running)
        if (_running)
          Center(
            child: Container(
              width: 240,
              height: 240,
              decoration: BoxDecoration(
                border: Border.all(
                  color: const Color(0xFF2563EB).withOpacity(0.7),
                  width: 2,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Stack(
                children: [
                  // Corner decorations
                  ...[ // TL, TR, BL, BR
                    Alignment.topLeft,
                    Alignment.topRight,
                    Alignment.bottomLeft,
                    Alignment.bottomRight,
                  ].map((align) => Align(
                    alignment: align,
                    child: Container(
                      width: 20,
                      height: 20,
                      decoration: BoxDecoration(
                        border: Border(
                          top: align == Alignment.topLeft || align == Alignment.topRight
                              ? const BorderSide(color: Color(0xFF2563EB), width: 3)
                              : BorderSide.none,
                          bottom: align == Alignment.bottomLeft || align == Alignment.bottomRight
                              ? const BorderSide(color: Color(0xFF2563EB), width: 3)
                              : BorderSide.none,
                          left: align == Alignment.topLeft || align == Alignment.bottomLeft
                              ? const BorderSide(color: Color(0xFF2563EB), width: 3)
                              : BorderSide.none,
                          right: align == Alignment.topRight || align == Alignment.bottomRight
                              ? const BorderSide(color: Color(0xFF2563EB), width: 3)
                              : BorderSide.none,
                        ),
                      ),
                    ),
                  )),
                ],
              ),
            ),
          ),

        // Bottom panel
        Positioned(
          bottom: 0,
          left: 0,
          right: 0,
          child: Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.transparent, Colors.black87],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
            child: SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Stats row
                    Row(
                      children: [
                        _StatChip(
                          icon: Icons.upload_rounded,
                          value: "$_uploadCount",
                          label: "uploads",
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _status,
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.65),
                              fontSize: 12,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),

                    if (_lastUploadedUrl != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        _lastUploadedUrl!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.35),
                          fontSize: 11,
                        ),
                      ),
                    ],

                    const SizedBox(height: 20),

                    // Action buttons
                    Row(
                      children: [
                        // Capture button
                        GestureDetector(
                          onTap: _busy ? null : _captureAndUpload,
                          child: Container(
                            width: 64,
                            height: 64,
                            decoration: BoxDecoration(
                              color: Colors.white,
                              shape: BoxShape.circle,
                              border: Border.all(
                                color: Colors.white.withOpacity(0.5),
                                width: 3,
                              ),
                            ),
                            child: _busy
                                ? const Padding(
                                    padding: EdgeInsets.all(18),
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.black54,
                                    ),
                                  )
                                : const Icon(
                                    Icons.camera_alt_rounded,
                                    color: Colors.black87,
                                    size: 28,
                                  ),
                          ),
                        ),

                        const SizedBox(width: 16),

                        // Auto button
                        Expanded(
                          child: GestureDetector(
                            onTap: _running ? _pauseAutoUpload : _startAutoUpload,
                            child: Container(
                              height: 52,
                              decoration: BoxDecoration(
                                color: _running
                                    ? const Color(0xFFEF4444)
                                    : const Color(0xFF2563EB),
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: Center(
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(
                                      _running ? Icons.pause_rounded : Icons.play_arrow_rounded,
                                      color: Colors.white,
                                      size: 22,
                                    ),
                                    const SizedBox(width: 8),
                                    Text(
                                      _running ? "Pause auto" : "Démarrer auto",
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.w700,
                                        fontSize: 14,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _StatChip extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;

  const _StatChip({
    required this.icon,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.15),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: Colors.white70, size: 14),
          const SizedBox(width: 5),
          Text(
            "$value $label",
            style: const TextStyle(
              color: Colors.white,
              fontSize: 13,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}