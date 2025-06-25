import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:unibooks/presentation/screens/home_screen.dart';

/// 앱의 진입점 (Entry point)
/// - Riverpod ProviderScope로 앱을 감싸서 상태 관리 활성화
void main() {
  // Riverpod ProviderScope로 앱을 감싸서 실행
  runApp(const ProviderScope(child: MyApp()));
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
