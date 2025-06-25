import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:unibooks/screens/home_screen.dart';

/// 앱의 진입점 (Entry point)
/// - 환경 변수(.env) 파일을 로드하여 API 키 등을 사용할 수 있도록 초기화
/// - Flutter 위젯 바인딩을 초기화하여 비동기 작업을 main에서 수행 가능
void main() async {
  // Flutter 위젯 바인딩 초기화 (비동기 작업을 위해 필요)
  WidgetsFlutterBinding.ensureInitialized();

  // .env 파일에서 환경 변수 로드 (OpenAI API 키 등)
  await dotenv.load(fileName: ".env");

  // 앱 실행
  runApp(const MyApp());
}

/// 앱의 루트 위젯
/// - Material Design 3을 사용한 앱 테마 설정
/// - 홈 화면을 초기 화면으로 설정
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'UniBooks',
      // Material Design 3 테마 설정
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.red),
        useMaterial3: true,
      ),
      // 앱의 첫 화면을 홈 스크린으로 설정
      home: const HomeScreen(),
    );
  }
}
