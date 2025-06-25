import 'package:dartz/dartz.dart';
import '../datasources/book_remote_datasource.dart';
import '../../core/failure.dart';
import '../../domain/entities/book_entity.dart';
import '../../domain/repositories/book_repository.dart';

/// 도서 Repository 구현 클래스
/// 실제 데이터 소스와 통신하며 에러 처리를 담당
class BookRepositoryImpl implements BookRepository {
  final BookRemoteDataSource remoteDataSource;

  BookRepositoryImpl({required this.remoteDataSource});

  @override
  Future<Either<Failure, bool>> checkServerHealth() async {
    try {
      final result = await remoteDataSource.checkServerHealth();
      return Right(result);
    } on ServerFailure catch (failure) {
      return Left(failure);
    } catch (e) {
      return Left(UnknownFailure('서버 상태 확인 중 알 수 없는 오류: $e'));
    }
  }

  @override
  Future<Either<Failure, List<BookEntity>>> getBookRecommendations({
    required String lectureTitle,
    required String major,
    required String interests,
    required String difficulty,
  }) async {
    try {
      final recommendations = await remoteDataSource.getBookRecommendations(
        lectureTitle: lectureTitle,
        major: major,
        interests: interests,
        difficulty: difficulty,
      );

      final entities =
          recommendations.map((model) => model.toEntity()).toList();
      return Right(entities);
    } on ServerFailure catch (failure) {
      return Left(failure);
    } on NetworkFailure catch (failure) {
      return Left(failure);
    } catch (e) {
      return Left(UnknownFailure('도서 추천 요청 중 알 수 없는 오류: $e'));
    }
  }

  @override
  Future<Either<Failure, List<BookEntity>>> getMockRecommendations() async {
    try {
      final recommendations = await remoteDataSource.getMockRecommendations();
      final entities =
          recommendations.map((model) => model.toEntity()).toList();
      return Right(entities);
    } on ServerFailure catch (failure) {
      return Left(failure);
    } on NetworkFailure catch (failure) {
      return Left(failure);
    } catch (e) {
      return Left(UnknownFailure('Mock 데이터 요청 중 알 수 없는 오류: $e'));
    }
  }

  @override
  Future<Either<Failure, BookEntity>> getBookDetail(String bookId) async {
    try {
      // 현재는 Mock 구현 - 추후 실제 API 연동
      await Future.delayed(const Duration(seconds: 1));

      final mockBook = BookEntity(
        title: 'Sample Book',
        author: 'Sample Author',
        description: 'Sample Description',
        genre: 'Technology',
        isbn: bookId,
        imageUrl: '',
        rating: 4.5,
        pages: 300,
        publishedDate: '2024',
        difficulty: '중급',
        topics: ['Programming', 'Technology'],
      );

      return Right(mockBook);
    } catch (e) {
      return Left(UnknownFailure('책 상세 정보 조회 중 알 수 없는 오류: $e'));
    }
  }
}
