import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/entities/book_entity.dart';
import '../../domain/repositories/book_repository.dart';
import '../../domain/usecases/get_book_recommendations.dart';
import '../../domain/usecases/get_book_detail.dart';
import '../../domain/usecases/check_server_health.dart';
import '../../core/providers.dart';
import '../../core/failure.dart';

/// 도서 추천 화면의 상태를 나타내는 클래스
class BookRecommendationState {
  final List<BookEntity> recommendations;
  final bool isLoading;
  final bool isLoadingServerCheck;
  final bool isLoadingMockData;
  final String? error;
  final String? serverError;
  final bool isServerHealthy;

  const BookRecommendationState({
    this.recommendations = const [],
    this.isLoading = false,
    this.isLoadingServerCheck = false,
    this.isLoadingMockData = false,
    this.error,
    this.serverError,
    this.isServerHealthy = false,
  });

  BookRecommendationState copyWith({
    List<BookEntity>? recommendations,
    bool? isLoading,
    bool? isLoadingServerCheck,
    bool? isLoadingMockData,
    String? error,
    String? serverError,
    bool? isServerHealthy,
  }) {
    return BookRecommendationState(
      recommendations: recommendations ?? this.recommendations,
      isLoading: isLoading ?? this.isLoading,
      isLoadingServerCheck: isLoadingServerCheck ?? this.isLoadingServerCheck,
      isLoadingMockData: isLoadingMockData ?? this.isLoadingMockData,
      error: error,
      serverError: serverError,
      isServerHealthy: isServerHealthy ?? this.isServerHealthy,
    );
  }
}

/// 도서 추천 상태를 관리하는 StateNotifier
class BookRecommendationNotifier
    extends StateNotifier<BookRecommendationState> {
  final GetBookRecommendations _getBookRecommendations;
  final GetBookDetail _getBookDetail;
  final CheckServerHealth _checkServerHealth;
  final BookRepository _repository;

  BookRecommendationNotifier(
    this._getBookRecommendations,
    this._getBookDetail,
    this._checkServerHealth,
    this._repository,
  ) : super(const BookRecommendationState());

  /// 도서 추천 요청
  Future<void> getRecommendations({
    required String lectureTitle,
    required String major,
    required String interests,
    required String difficulty,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    final params = BookRecommendationParams(
      lectureTitle: lectureTitle,
      major: major,
      interests: interests,
      difficulty: difficulty,
    );

    final result = await _getBookRecommendations(params);

    result.fold(
      (failure) =>
          state = state.copyWith(
            isLoading: false,
            error: _mapFailureToMessage(failure),
          ),
      (recommendations) =>
          state = state.copyWith(
            isLoading: false,
            recommendations: recommendations,
            error: null,
          ),
    );
  }

  /// Mock 데이터 로드
  Future<void> loadMockData() async {
    state = state.copyWith(isLoadingMockData: true, error: null);

    // Mock 데이터를 위해 repository에서 직접 호출
    final result = await _repository.getMockRecommendations();

    result.fold(
      (failure) =>
          state = state.copyWith(
            isLoadingMockData: false,
            error: _mapFailureToMessage(failure),
          ),
      (recommendations) =>
          state = state.copyWith(
            isLoadingMockData: false,
            recommendations: recommendations,
            error: null,
          ),
    );
  }

  /// 서버 연결 상태 확인
  Future<void> checkServerHealth() async {
    state = state.copyWith(isLoadingServerCheck: true, serverError: null);

    final result = await _checkServerHealth();

    result.fold(
      (failure) =>
          state = state.copyWith(
            isLoadingServerCheck: false,
            serverError: _mapFailureToMessage(failure),
            isServerHealthy: false,
          ),
      (isHealthy) =>
          state = state.copyWith(
            isLoadingServerCheck: false,
            isServerHealthy: isHealthy,
            serverError: null,
          ),
    );
  }

  /// 책 상세 정보 조회
  Future<BookEntity?> getBookDetail(String bookId) async {
    final result = await _getBookDetail(bookId);

    return result.fold((failure) {
      // 에러가 발생해도 상태는 변경하지 않고 null 반환
      return null;
    }, (bookDetail) => bookDetail);
  }

  /// Failure를 사용자 친화적인 메시지로 변환
  String _mapFailureToMessage(Failure failure) {
    return switch (failure.runtimeType) {
      ServerFailure _ => '서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.',
      NetworkFailure _ => '네트워크 연결을 확인해주세요.',
      UnknownFailure _ => '알 수 없는 오류가 발생했습니다.',
      _ => '오류가 발생했습니다.',
    };
  }
}

/// BookRecommendationNotifier Provider
final bookRecommendationNotifierProvider =
    StateNotifierProvider<BookRecommendationNotifier, BookRecommendationState>((
      ref,
    ) {
      final getBookRecommendations = ref.watch(
        getBookRecommendationsUseCaseProvider,
      );
      final getBookDetail = ref.watch(getBookDetailUseCaseProvider);
      final checkServerHealth = ref.watch(checkServerHealthUseCaseProvider);
      final repository = ref.watch(bookRepositoryProvider);

      return BookRecommendationNotifier(
        getBookRecommendations,
        getBookDetail,
        checkServerHealth,
        repository,
      );
    });
