import 'package:dio/dio.dart';

class ApiService {
  final Dio dio;

  ApiService({required String baseUrl})
      : dio = Dio(BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 2),
          receiveTimeout: const Duration(seconds: 4),
        ));

  Future<Map<String, dynamic>> detectImage(String path) async {
    final formData = FormData.fromMap({
      "file": await MultipartFile.fromFile(path, filename: "frame.jpg"),
    });

    final resp = await dio.post("/detect", data: formData);
    return (resp.data as Map).cast<String, dynamic>();
  }
}
