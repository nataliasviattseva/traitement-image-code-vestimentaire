import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_app_ia/app.dart';

void main() {
  testWidgets('Home page shows main buttons', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());

    expect(find.text('Caméra (analyse live)'), findsOneWidget);
    expect(find.text('Alertes (temps réel)'), findsOneWidget);
  });
}
