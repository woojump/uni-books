import 'package:dartz/dartz.dart';
import '../../core/failure.dart';
import '../../core/usecase.dart';
import '../entities/book_entity.dart';
import '../repositories/book_repository.dart';

/// Use case for getting book recommendations
class GetBookRecommendations
    implements UseCase<List<BookEntity>, BookRecommendationParams> {
  final BookRepository repository;

  GetBookRecommendations(this.repository);

  @override
  Future<Either<Failure, List<BookEntity>>> call(
    BookRecommendationParams params,
  ) async {
    return await repository.getBookRecommendations(
      lectureTitle: params.lectureTitle,
      major: params.major,
      interests: params.interests,
      difficulty: params.difficulty,
    );
  }
}

/// Parameters for book recommendation request
class BookRecommendationParams {
  final String lectureTitle;
  final String major;
  final String interests;
  final String difficulty;

  const BookRecommendationParams({
    required this.lectureTitle,
    required this.major,
    required this.interests,
    required this.difficulty,
  });
}
