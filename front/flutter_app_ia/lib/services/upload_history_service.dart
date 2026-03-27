import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class UploadHistoryService {
  static const String _key = 'upload_history';

  Future<List<Map<String, dynamic>>> getUploads() async {
    final prefs = await SharedPreferences.getInstance();
    final rawList = prefs.getStringList(_key) ?? [];

    return rawList
        .map((e) => jsonDecode(e) as Map<String, dynamic>)
        .toList()
        .reversed
        .toList();
  }

  Future<void> addUpload({
    required String imageUrl,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final rawList = prefs.getStringList(_key) ?? [];

    final item = {
      'image_url': imageUrl,
      'created_at': DateTime.now().toIso8601String(),
    };

    rawList.add(jsonEncode(item));
    await prefs.setStringList(_key, rawList);
  }

  Future<void> clearUploads() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }

  Future<void> deleteUpload(String imageUrl) async {
    final prefs = await SharedPreferences.getInstance();
    final rawList = prefs.getStringList(_key) ?? [];

    final updated = rawList.where((raw) {
      final item = jsonDecode(raw) as Map<String, dynamic>;
      return item['image_url'] != imageUrl;
    }).toList();

    await prefs.setStringList(_key, updated);
  }
}