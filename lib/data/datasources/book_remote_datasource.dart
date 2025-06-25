import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/book_recommendation.dart';
import '../../core/failure.dart';

/// 원격 데이터 소스 추상 클래스
/// 백엔드 API와의 통신을 담당하는 인터페이스 정의
abstract class BookRemoteDataSource {
  /// 서버 상태 확인
  Future<bool> checkServerHealth();

  /// 도서 추천 요청
  Future<List<BookRecommendation>> getBookRecommendations({
    required String lectureTitle,
    required String major,
    required String interests,
    required String difficulty,
  });

  /// Mock 데이터 요청
  Future<List<BookRecommendation>> getMockRecommendations();

  /// 책 상세 정보 요청
  Future<BookDetail> getBookDetail({required BookRecommendation book});
}

/// 원격 데이터 소스 구현 클래스
/// 실제 HTTP 통신을 수행하는 클래스
class BookRemoteDataSourceImpl implements BookRemoteDataSource {
  final http.Client client;
  final String baseUrl;

  BookRemoteDataSourceImpl({
    required this.client,
    this.baseUrl = 'http://localhost:8000',
  });

  @override
  Future<bool> checkServerHealth() async {
    try {
      final response = await client
          .get(
            Uri.parse('$baseUrl/health'),
            headers: {'Content-Type': 'application/json'},
          )
          .timeout(const Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      throw ServerFailure('서버 연결 실패: $e');
    }
  }

  @override
  Future<List<BookRecommendation>> getBookRecommendations({
    required String lectureTitle,
    required String major,
    required String interests,
    required String difficulty,
  }) async {
    try {
      final response = await client
          .post(
            Uri.parse('$baseUrl/api/v1/book-recommendations'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'lecture_title': lectureTitle,
              'major_field': major,
              'interest_technology': interests,
              'learning_difficulty': difficulty,
            }),
          )
          .timeout(const Duration(seconds: 60));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List<dynamic> booksData = data['books'];
        return booksData
            .map((book) => BookRecommendation.fromJson(book))
            .toList();
      } else {
        throw ServerFailure('도서 추천 요청 실패: ${response.statusCode}');
      }
    } catch (e) {
      if (e is ServerFailure) rethrow;
      throw NetworkFailure('네트워크 오류: $e');
    }
  }

  @override
  Future<List<BookRecommendation>> getMockRecommendations() async {
    try {
      final response = await client
          .get(
            Uri.parse('$baseUrl/api/v1/mock-recommendations'),
            headers: {'Content-Type': 'application/json'},
          )
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List<dynamic> booksData = data['books'];
        return booksData
            .map((book) => BookRecommendation.fromJson(book))
            .toList();
      } else {
        throw ServerFailure('Mock 데이터 요청 실패: ${response.statusCode}');
      }
    } catch (e) {
      if (e is ServerFailure) rethrow;
      throw NetworkFailure('네트워크 오류: $e');
    }
  }

  @override
  Future<BookDetail> getBookDetail({required BookRecommendation book}) async {
    try {
      // 현재는 Mock 데이터 반환 (추후 실제 API 연동)
      await Future.delayed(const Duration(seconds: 2));

      return BookDetail(
        basicInfo: book,
        coverImageUrl: null,
        plot:
            '${book.title}에 대한 상세한 줄거리입니다. 이 책은 ${book.difficulty} 수준의 독자들을 대상으로 하며, ${book.description}',
        rating: DetailedRating(
          overall: book.rating ?? 4.0,
          totalReviews: 125,
          fiveStars: 65,
          fourStars: 40,
          threeStars: 15,
          twoStars: 3,
          oneStars: 2,
        ),
        reviews: [
          '이 책은 정말 유익하고 이해하기 쉽게 설명되어 있습니다.',
          '실무에 바로 적용할 수 있는 내용들이 많아서 좋았습니다.',
          '초보자도 쉽게 따라할 수 있도록 구성되어 있어요.',
        ],
        isAvailableForLoan: false,
      );
    } catch (e) {
      throw ServerFailure('책 상세 정보 조회 실패: $e');
    }
  }
}
