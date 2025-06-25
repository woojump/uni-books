// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'book_recommendation.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BookRecommendation _$BookRecommendationFromJson(Map<String, dynamic> json) =>
    BookRecommendation(
      title: json['title'] as String,
      author: json['author'] as String,
      description: json['description'] as String,
      difficulty: json['difficulty'] as String,
      isbn: json['isbn'] as String?,
      publisher: json['publisher'] as String?,
      publicationYear: json['publicationYear'] as String?,
      rating: (json['rating'] as num?)?.toDouble(),
      imageUrl: json['imageUrl'] as String?,
    );

Map<String, dynamic> _$BookRecommendationToJson(BookRecommendation instance) =>
    <String, dynamic>{
      'title': instance.title,
      'author': instance.author,
      'description': instance.description,
      'difficulty': instance.difficulty,
      'isbn': instance.isbn,
      'publisher': instance.publisher,
      'publicationYear': instance.publicationYear,
      'rating': instance.rating,
      'imageUrl': instance.imageUrl,
    };

BookRecommendationRequest _$BookRecommendationRequestFromJson(
  Map<String, dynamic> json,
) => BookRecommendationRequest(
  major: json['major'] as String,
  interests: json['interests'] as String,
  difficulty: json['difficulty'] as String,
);

Map<String, dynamic> _$BookRecommendationRequestToJson(
  BookRecommendationRequest instance,
) => <String, dynamic>{
  'major': instance.major,
  'interests': instance.interests,
  'difficulty': instance.difficulty,
};

OpenAIResponse _$OpenAIResponseFromJson(Map<String, dynamic> json) =>
    OpenAIResponse(
      choices:
          (json['choices'] as List<dynamic>)
              .map((e) => Choice.fromJson(e as Map<String, dynamic>))
              .toList(),
    );

Map<String, dynamic> _$OpenAIResponseToJson(OpenAIResponse instance) =>
    <String, dynamic>{'choices': instance.choices};

Choice _$ChoiceFromJson(Map<String, dynamic> json) =>
    Choice(message: Message.fromJson(json['message'] as Map<String, dynamic>));

Map<String, dynamic> _$ChoiceToJson(Choice instance) => <String, dynamic>{
  'message': instance.message,
};

Message _$MessageFromJson(Map<String, dynamic> json) =>
    Message(role: json['role'] as String, content: json['content'] as String);

Map<String, dynamic> _$MessageToJson(Message instance) => <String, dynamic>{
  'role': instance.role,
  'content': instance.content,
};
