import 'package:dartz/dartz.dart';

/// 앱 전반에서 사용되는 실패(Failure) 추상 클래스
/// 모든 에러 상황을 통일된 방식으로 처리하기 위한 기본 클래스
abstract class Failure {
  final String message;
  const Failure(this.message);
}

/// 서버 관련 실패
class ServerFailure extends Failure {
  const ServerFailure(super.message);
}

/// 네트워크 연결 실패
class NetworkFailure extends Failure {
  const NetworkFailure(super.message);
}

/// 데이터 파싱 실패
class ParsingFailure extends Failure {
  const ParsingFailure(super.message);
}

/// 알 수 없는 실패
class UnknownFailure extends Failure {
  const UnknownFailure(super.message);
}

/// Either 타입의 별칭 정의
/// Left: 실패, Right: 성공
typedef FailureOr<T> = Either<Failure, T>;
