import 'package:dartz/dartz.dart';
import '../../core/failure.dart';
import '../../core/usecase.dart';
import '../entities/book_entity.dart';
import '../repositories/book_repository.dart';

/// Use case for getting book detail
class GetBookDetail implements UseCase<BookEntity, String> {
  final BookRepository repository;

  GetBookDetail(this.repository);

  @override
  Future<Either<Failure, BookEntity>> call(String bookId) async {
    return await repository.getBookDetail(bookId);
  }
}
