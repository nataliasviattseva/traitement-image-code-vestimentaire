import 'dart:io';

class AppConfig {
  // iOS Simulator: localhost OK
  // Android Emulator: 10.0.2.2
  // Real device: mets l'IP du Mac/serveur (ex: 192.168.x.x)
  static String apiBaseUrl = Platform.isAndroid
      ? "http://10.0.2.2:8000"
      : "http://localhost:8000";

  static String wsUrl = Platform.isAndroid
      ? "ws://10.0.2.2:8000/ws/alerts"
      : "ws://localhost:8000/ws/alerts";
}
