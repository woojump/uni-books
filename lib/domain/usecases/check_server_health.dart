import 'package:dartz/dartz.dart';
import '../../core/failure.dart';
import '../../core/usecase.dart';
import '../repositories/book_repository.dart';

/// Use case for checking server health
class CheckServerHealth implements UseCase0<bool> {
  final BookRepository repository;

  CheckServerHealth(this.repository);

  @override
  Future<Either<Failure, bool>> call() async {
    return await repository.checkServerHealth();
  }
}
