import 'package:dartz/dartz.dart';
import 'failure.dart';

/// Abstract class for use cases with parameters
abstract class UseCase<Type, Params> {
  Future<Either<Failure, Type>> call(Params params);
}

/// Abstract class for use cases without parameters
abstract class UseCase0<Type> {
  Future<Either<Failure, Type>> call();
}

/// Class for use cases that don't need parameters
class NoParams {
  const NoParams();
}
