import 'package:supabase_flutter/supabase_flutter.dart';

class SupabaseService {
  final supabase = Supabase.instance.client;

  Future<void> insertImage({
    required String url,
    required String cloudinaryId,
  }) async {
    await supabase.from('images').insert({
      'url': url,
      'cloudinary_id': cloudinaryId,
      'traite': false,
      'notifie': false,
    });
  }

  Future<List<Map<String, dynamic>>> getImages() async {
    final data = await supabase
        .from('images')
        .select()
        .order('uploaded_at', ascending: false);

    return List<Map<String, dynamic>>.from(data);
  }
}