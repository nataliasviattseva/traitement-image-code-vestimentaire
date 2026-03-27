import 'dart:convert';
import 'package:http/http.dart' as http;

class CloudinaryService {
  static const String cloudName = 'dsmkw12jp';
  static const String uploadPreset = 'safewear_upload';

  static String get uploadUrl =>
      'https://api.cloudinary.com/v1_1/$cloudName/image/upload';

  Future<Map<String, String>> uploadImage(String imagePath) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse(uploadUrl),
    );

    request.fields['upload_preset'] = uploadPreset;
    request.files.add(
      await http.MultipartFile.fromPath('file', imagePath),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode != 200) {
      throw Exception(
        'Cloudinary upload failed: ${response.statusCode} ${response.body}',
      );
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;

    final secureUrl = data['secure_url'] as String?;
    final publicId = data['public_id'] as String?;

    if (secureUrl == null || secureUrl.isEmpty) {
      throw Exception('Cloudinary did not return secure_url');
    }

    if (publicId == null || publicId.isEmpty) {
      throw Exception('Cloudinary did not return public_id');
    }

    return {
      'url': secureUrl,
      'cloudinary_id': publicId,
    };
  }
}