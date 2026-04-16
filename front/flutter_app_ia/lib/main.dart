import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Supabase.initialize(
    url: 'https://cewneqmispmvcgyhovht.supabase.co',
    anonKey: 'sb_publishable_-7nkM8BuemDH8f5yKjzbGA_g3Rk6T5I',
  );

  runApp(const MyApp());
}