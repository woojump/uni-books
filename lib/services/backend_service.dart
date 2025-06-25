import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/book_recommendation.dart';

/// 백엔드 API와 통신하여 도서 추천을 받는 서비스 클래스
class BackendService {
  /// 백엔드 API 베이스 URL
  /// 개발 환경에서는 localhost 사용
  static const String _baseUrl = 'http://localhost:8000/api/v1';
  
  /// Android 에뮬레이터에서 localhost 접근 시 사용
  static const String _androidEmulatorUrl = 'http://10.0.2.2:8000/api/v1';
  
  /// 현재 플랫폼에 맞는 베이스 URL 반환
  static String get baseUrl {
    // 플랫폼 감지는 추후 개선 가능
    return _baseUrl;  // 기본적으로 localhost 사용
  }

  /// 사용자 정보를 바탕으로 백엔드에 도서 추천을 요청하는 함수
  ///
  /// [major]: 사용자의 전공 분야
  /// [interests]: 사용자의 관심 기술
  /// [difficulty]: 원하는 학습 난이도 (초급/중급/고급)
  ///
  /// Returns: BookRecommendation 객체 리스트 (추천받은 책들)
  /// Throws: Exception (API 호출 실패, 파싱 오류 등)
  static Future<List<BookRecommendation>> getBookRecommendations({
    required String major,
    required String interests,
    required String difficulty,
  }) async {
    try {
      print('백엔드 API 호출: $baseUrl/book-recommendations');

      // 백엔드 API에 HTTP POST 요청 전송
      final response = await http.post(
        Uri.parse('$baseUrl/book-recommendations'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'major': major,
          'interests': interests,
          'difficulty': difficulty,
        }),
      ).timeout(
        const Duration(seconds: 60), // 60초 타임아웃
        onTimeout: () {
          throw Exception('요청 시간 초과: 서버 응답이 너무 느립니다.');
        },
      );

      print('백엔드 응답 상태 코드: ${response.statusCode}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        if (data['status'] == 'success' && data['books'] != null) {
          final List<dynamic> booksJson = data['books'];
          return booksJson
              .map((json) => BookRecommendation.fromJson(json))
              .toList();
        } else {
          throw Exception('백엔드 응답 형식 오류: ${data['message'] ?? '알 수 없는 오류'}');
        }
      } else {
        String errorMessage = '백엔드 API 요청 실패: ${response.statusCode}';
        
        try {
          final errorData = jsonDecode(response.body);
          if (errorData['detail'] != null) {
            errorMessage += ' - ${errorData['detail']}';
          }
        } catch (e) {
          // JSON 파싱 실패 시 원본 응답 사용
          errorMessage += ' - ${response.body}';
        }
        
        throw Exception(errorMessage);
      }
    } catch (e) {
      print('백엔드 API 호출 오류: $e');
      
      // 연결 오류인 경우 더 친화적인 메시지 제공
      if (e.toString().contains('Connection refused') || 
          e.toString().contains('Failed to connect')) {
        throw Exception(
          '백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.\n'
          '서버 주소: $baseUrl'
        );
      }
      
      throw Exception('책 추천 요청 중 오류 발생: $e');
    }
  }

  /// 백엔드 서버의 헬스 체크를 수행하는 함수
  static Future<bool> checkServerHealth() async {
    try {
      final response = await http.get(
        Uri.parse('http://localhost:8000/health'),  // 직접 헬스체크 경로 지정
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 5));
      
      return response.statusCode == 200;
    } catch (e) {
      print('서버 헬스 체크 실패: $e');
      return false;
    }
  }

  /// OpenAI API 키 유효성을 테스트하는 함수
  static Future<bool> testApiKey() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/test-api-key'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 10));

      print('API 키 테스트 응답 코드: ${response.statusCode}');
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['valid'] == true;
      }
      
      return false;
    } catch (e) {
      print('API 키 테스트 오류: $e');
      return false;
    }
  }

  /// Mock 데이터를 가져오는 함수 (테스트용)
  static Future<List<BookRecommendation>> getMockRecommendations() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/mock-recommendations'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        if (data['status'] == 'success' && data['books'] != null) {
          final List<dynamic> booksJson = data['books'];
          return booksJson
              .map((json) => BookRecommendation.fromJson(json))
              .toList();
        }
      }
      
      throw Exception('Mock 데이터 요청 실패');
    } catch (e) {
      print('Mock 데이터 요청 오류: $e');
      throw Exception('Mock 데이터 요청 중 오류 발생: $e');
    }
  }

  /// 백엔드 서버 정보를 가져오는 함수
  static Future<Map<String, dynamic>> getServerInfo() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/..'),  // 루트 엔드포인트
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      
      throw Exception('서버 정보 요청 실패');
    } catch (e) {
      print('서버 정보 요청 오류: $e');
      throw Exception('서버 정보 요청 중 오류 발생: $e');
    }
  }
} 