/// Core constants used throughout the application
class AppConstants {
  static const String baseUrl = 'http://localhost:8000';
  static const int connectionTimeout = 30000;
  static const int receiveTimeout = 30000;
}

/// API endpoints
class ApiEndpoints {
  static const String health = '/health';
  static const String recommendations = '/recommendations';
  static const String bookDetail = '/book-detail';
}
