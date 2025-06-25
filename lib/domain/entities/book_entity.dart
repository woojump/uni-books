/// Domain entity for book recommendation
/// This represents the core business object without any external dependencies
class BookEntity {
  final String title;
  final String author;
  final String description;
  final String genre;
  final String isbn;
  final String imageUrl;
  final double rating;
  final int pages;
  final String publishedDate;
  final String difficulty;
  final List<String> topics;

  const BookEntity({
    required this.title,
    required this.author,
    required this.description,
    required this.genre,
    required this.isbn,
    this.imageUrl = '',
    this.rating = 0.0,
    this.pages = 0,
    this.publishedDate = '',
    this.difficulty = 'Beginner',
    this.topics = const [],
  });

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is BookEntity &&
        other.title == title &&
        other.author == author &&
        other.isbn == isbn;
  }

  @override
  int get hashCode => title.hashCode ^ author.hashCode ^ isbn.hashCode;
}
