import 'package:json_annotation/json_annotation.dart';

// build_runner로 생성되는 JSON 직렬화 코드 파일
part 'book_recommendation.g.dart';

/// 도서 추천 정보를 담는 데이터 모델
/// ChatGPT API로부터 받은 책 정보를 구조화하여 저장
@JsonSerializable()
class BookRecommendation {
  /// 책 제목 (필수)
  final String title;

  /// 저자 (필수)
  final String author;

  /// 책 설명 (필수)
  final String description;

  /// 학습 난이도: "초급", "중급", "고급" (필수)
  final String difficulty;

  /// ISBN 번호 (선택사항)
  final String? isbn;

  /// 출판사 (선택사항)
  final String? publisher;

  /// 출간년도 (선택사항)
  final String? publicationYear;

  /// 평점 (1.0 ~ 5.0, 선택사항)
  final double? rating;

  /// 책 표지 이미지 URL (선택사항)
  final String? imageUrl;

  /// 생성자 - 필수 필드는 required, 선택 필드는 nullable
  BookRecommendation({
    required this.title,
    required this.author,
    required this.description,
    required this.difficulty,
    this.isbn,
    this.publisher,
    this.publicationYear,
    this.rating,
    this.imageUrl,
  });

  /// JSON 데이터로부터 BookRecommendation 객체 생성
  /// ChatGPT API 응답을 파싱할 때 사용
  factory BookRecommendation.fromJson(Map<String, dynamic> json) =>
      _$BookRecommendationFromJson(json);

  /// BookRecommendation 객체를 JSON으로 변환
  /// 데이터 저장이나 API 전송 시 사용
  Map<String, dynamic> toJson() => _$BookRecommendationToJson(this);
}

/// 도서 추천 요청 정보를 담는 데이터 모델
/// 사용자가 입력한 정보를 구조화하여 API에 전달
@JsonSerializable()
class BookRecommendationRequest {
  /// 사용자의 전공 분야
  final String major;

  /// 사용자의 관심 기술
  final String interests;

  /// 원하는 학습 난이도
  final String difficulty;

  BookRecommendationRequest({
    required this.major,
    required this.interests,
    required this.difficulty,
  });

  factory BookRecommendationRequest.fromJson(Map<String, dynamic> json) =>
      _$BookRecommendationRequestFromJson(json);

  Map<String, dynamic> toJson() => _$BookRecommendationRequestToJson(this);
}

@JsonSerializable()
class OpenAIResponse {
  final List<Choice> choices;

  OpenAIResponse({required this.choices});

  factory OpenAIResponse.fromJson(Map<String, dynamic> json) =>
      _$OpenAIResponseFromJson(json);

  Map<String, dynamic> toJson() => _$OpenAIResponseToJson(this);
}

@JsonSerializable()
class Choice {
  final Message message;

  Choice({required this.message});

  factory Choice.fromJson(Map<String, dynamic> json) => _$ChoiceFromJson(json);

  Map<String, dynamic> toJson() => _$ChoiceToJson(this);
}

@JsonSerializable()
class Message {
  final String role;
  final String content;

  Message({required this.role, required this.content});

  factory Message.fromJson(Map<String, dynamic> json) =>
      _$MessageFromJson(json);

  Map<String, dynamic> toJson() => _$MessageToJson(this);
}
