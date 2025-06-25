import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../models/book_recommendation.dart';

/// ChatGPT API와 통신하여 도서 추천을 받는 서비스 클래스
/// OpenAI의 GPT-3.5-turbo 모델을 사용하여 사용자 맞춤형 책 추천 제공
class ChatGPTService {
  /// OpenAI Chat Completions API 엔드포인트
  static const String _baseUrl = 'https://api.openai.com/v1/chat/completions';

  /// .env 파일에서 OpenAI API 키를 가져오는 getter
  /// 환경 변수 'OPENAI_API_KEY'에서 값을 읽어옴
  static String get _apiKey => dotenv.env['OPENAI_API_KEY'] ?? '';

  /// 사용자 정보를 바탕으로 ChatGPT에게 도서 추천을 요청하는 메인 함수
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
      // API 키 유효성 검사
      if (_apiKey.isEmpty) {
        throw Exception('OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.');
      }

      // 디버깅용 로그 - API 키의 첫 10자만 출력하여 보안 유지
      print('API 키 확인: ${_apiKey.substring(0, 10)}...');

      // 사용자 입력을 바탕으로 ChatGPT용 프롬프트 생성
      final prompt = _createPrompt(major, interests, difficulty);

      // OpenAI API에 HTTP POST 요청 전송
      final response = await http.post(
        Uri.parse(_baseUrl),
        headers: {
          'Authorization': 'Bearer $_apiKey', // Bearer 토큰 방식 인증
          'Content-Type': 'application/json', // JSON 형식 데이터 전송
        },
        body: jsonEncode({
          'model': 'gpt-3.5-turbo',
          'messages': [
            {
              'role': 'system',
              'content': '''당신은 대학생을 위한 전문 도서 추천 시스템입니다. 
              사용자의 전공, 관심 기술, 학습 난이도에 맞는 책들을 추천해주세요.
              응답은 반드시 JSON 배열 형태로만 제공하고, 다른 텍스트는 포함하지 마세요.
              각 책 정보는 다음 형식을 따라주세요:
              [
                {
                  "title": "책 제목",
                  "author": "저자",
                  "description": "책 설명 (200자 이내)",
                  "difficulty": "초급/중급/고급",
                  "isbn": "ISBN (있는 경우)",
                  "publisher": "출판사",
                  "publicationYear": "출간년도",
                  "rating": 4.5,
                  "imageUrl": null
                }
              ]''',
            },
            {'role': 'user', 'content': prompt},
          ],
          'max_tokens': 2000,
          'temperature': 0.7,
        }),
      );

      print('응답 상태 코드: ${response.statusCode}'); // 디버깅용

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final content = data['choices'][0]['message']['content'];

        // JSON 파싱
        final List<dynamic> booksJson = jsonDecode(content);
        return booksJson
            .map((json) => BookRecommendation.fromJson(json))
            .toList();
      } else {
        print('에러 응답: ${response.body}'); // 디버깅용
        final errorData = jsonDecode(response.body);
        String errorMessage = 'API 요청 실패: ${response.statusCode}';

        if (errorData['error'] != null) {
          errorMessage += ' - ${errorData['error']['message'] ?? '알 수 없는 오류'}';
        }

        throw Exception(errorMessage);
      }
    } catch (e) {
      print('오류 발생: $e'); // 디버깅용
      throw Exception('책 추천 요청 중 오류 발생: $e');
    }
  }

  static String _createPrompt(
    String major,
    String interests,
    String difficulty,
  ) {
    return '''
전공 분야: $major
관심 기술: $interests
학습 난이도: $difficulty

위의 정보를 바탕으로 적합한 책 5권을 추천해주세요. 
각 책은 전공 분야와 관심 기술에 맞고, 요청한 학습 난이도에 적합해야 합니다.
실제 존재하는 책들로만 추천해주시고, 한국어 번역서가 있다면 우선적으로 추천해주세요.
''';
  }

  // API 키 테스트용 함수
  static Future<bool> testApiKey() async {
    try {
      if (_apiKey.isEmpty) {
        print('API 키가 비어있습니다.');
        return false;
      }

      final response = await http.post(
        Uri.parse(_baseUrl),
        headers: {
          'Authorization': 'Bearer $_apiKey',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'model': 'gpt-3.5-turbo',
          'messages': [
            {'role': 'user', 'content': 'Hello'},
          ],
          'max_tokens': 5,
        }),
      );

      print('테스트 응답 코드: ${response.statusCode}');
      print('테스트 응답 본문: ${response.body}');

      return response.statusCode == 200;
    } catch (e) {
      print('API 키 테스트 오류: $e');
      return false;
    }
  }
}

// Mock 데이터를 위한 임시 서비스
class MockBookService {
  static Future<List<BookRecommendation>> getMockRecommendations({
    required String major,
    required String interests,
    required String difficulty,
  }) async {
    // 실제 API 연동 전 테스트용 mock 데이터
    await Future.delayed(const Duration(seconds: 2));

    return [
      BookRecommendation(
        title: "Clean Code",
        author: "Robert C. Martin",
        description: "소프트웨어 개발자를 위한 클린 코드 작성법을 다루는 필독서입니다.",
        difficulty: "중급",
        publisher: "인사이트",
        publicationYear: "2013",
        rating: 4.8,
      ),
      BookRecommendation(
        title: "Flutter 완벽 가이드",
        author: "김태헌",
        description: "Flutter 프레임워크를 활용한 모바일 앱 개발의 모든 것을 다룹니다.",
        difficulty: difficulty,
        publisher: "한빛미디어",
        publicationYear: "2023",
        rating: 4.5,
      ),
      BookRecommendation(
        title: "자료구조와 알고리즘",
        author: "홍정모",
        description: "프로그래밍의 기초가 되는 자료구조와 알고리즘을 쉽게 설명합니다.",
        difficulty: "초급",
        publisher: "생능출판",
        publicationYear: "2022",
        rating: 4.3,
      ),
    ];
  }
}
