import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../data/datasources/book_remote_datasource.dart';
import '../data/repositories/book_repository_impl.dart';
import '../domain/repositories/book_repository.dart';
import '../domain/usecases/get_book_recommendations.dart';
import '../domain/usecases/get_book_detail.dart';
import '../domain/usecases/check_server_health.dart';

/// HTTP Client Provider
final httpClientProvider = Provider<http.Client>((ref) {
  return http.Client();
});

/// Remote Data Source Provider
final bookRemoteDataSourceProvider = Provider<BookRemoteDataSource>((ref) {
  final client = ref.watch(httpClientProvider);
  return BookRemoteDataSourceImpl(client: client);
});

/// Repository Provider
final bookRepositoryProvider = Provider<BookRepository>((ref) {
  final remoteDataSource = ref.watch(bookRemoteDataSourceProvider);
  return BookRepositoryImpl(remoteDataSource: remoteDataSource);
});

/// Use Cases Providers
final getBookRecommendationsUseCaseProvider = Provider<GetBookRecommendations>((
  ref,
) {
  final repository = ref.watch(bookRepositoryProvider);
  return GetBookRecommendations(repository);
});

final getBookDetailUseCaseProvider = Provider<GetBookDetail>((ref) {
  final repository = ref.watch(bookRepositoryProvider);
  return GetBookDetail(repository);
});

final checkServerHealthUseCaseProvider = Provider<CheckServerHealth>((ref) {
  final repository = ref.watch(bookRepositoryProvider);
  return CheckServerHealth(repository);
});
