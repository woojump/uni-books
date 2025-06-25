import 'package:dartz/dartz.dart';
import '../../core/failure.dart';
import '../entities/book_entity.dart';

/// Repository interface for book operations
/// This defines the contract that data layer implementations must follow
abstract class BookRepository {
  /// Get book recommendations based on user preferences
  Future<Either<Failure, List<BookEntity>>> getBookRecommendations({
    required String lectureTitle,
    required String major,
    required String interests,
    required String difficulty,
  });

  /// Get detailed information about a specific book
  Future<Either<Failure, BookEntity>> getBookDetail(String bookId);

  /// Check server health status
  Future<Either<Failure, bool>> checkServerHealth();

  /// Get mock recommendations for testing
  Future<Either<Failure, List<BookEntity>>> getMockRecommendations();
}
