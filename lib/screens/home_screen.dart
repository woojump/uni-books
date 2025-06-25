import 'package:flutter/material.dart';
import '../models/book_recommendation.dart';
import '../services/chatgpt_service.dart';

/// 앱의 메인 홈 화면 위젯
/// 사용자 입력을 받아 AI 도서 추천을 받고 결과를 표시하는 화면
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

/// 홈 화면의 상태를 관리하는 클래스
/// 사용자 입력, API 호출, 결과 표시 등의 상태를 관리
class _HomeScreenState extends State<HomeScreen> {
  /// 폼 유효성 검사를 위한 키
  final _formKey = GlobalKey<FormState>();

  /// 사용자 입력 컨트롤러들
  final _majorController = TextEditingController(); // 전공 분야 입력
  final _interestsController = TextEditingController(); // 관심 기술 입력

  /// 학습 난이도 선택 관련 변수들
  String _selectedDifficulty = '초급'; // 현재 선택된 난이도
  final List<String> _difficulties = ['초급', '중급', '고급']; // 선택 가능한 난이도 목록

  /// 앱 상태 관리 변수들
  List<BookRecommendation> _recommendations = []; // 추천받은 책 목록
  bool _isLoading = false; // 로딩 상태
  String? _error; // 에러 메시지

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // 상단 앱바 설정
      appBar: AppBar(
        title: const Text(
          'UniBooks',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        elevation: 0,
      ),
      // 스크롤 가능한 메인 컨텐츠
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(), // 앱 소개 헤더
            const SizedBox(height: 24),
            _buildInputForm(), // 사용자 입력 폼
            const SizedBox(height: 24),
            // 상태에 따른 조건부 위젯 렌더링
            if (_isLoading) _buildLoadingWidget(), // 로딩 중일 때
            if (_error != null) _buildErrorWidget(), // 에러 발생 시
            if (_recommendations.isNotEmpty)
              _buildRecommendationsSection(), // 추천 결과가 있을 때
          ],
        ),
      ),
    );
  }

  /// 앱 소개 및 설명을 표시하는 헤더 위젯
  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.blue.shade50, Colors.indigo.shade50],
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '📚 맞춤형 도서 추천',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.indigo.shade700,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '전공 분야, 관심 기술, 학습 난이도를 입력하면\nAI가 적합한 책을 추천해드립니다.',
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(color: Colors.grey.shade600),
          ),
        ],
      ),
    );
  }

  /// 사용자 입력을 받는 폼 위젯
  /// 전공 분야, 관심 기술, 학습 난이도를 입력받고 API 호출 버튼 제공
  Widget _buildInputForm() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '정보 입력',
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _majorController,
                decoration: const InputDecoration(
                  labelText: '전공 분야',
                  hintText: '예: 컴퓨터공학, 전자공학, 경영학 등',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.school),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return '전공 분야를 입력해주세요';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _interestsController,
                decoration: const InputDecoration(
                  labelText: '관심 기술',
                  hintText: '예: Flutter, AI, 블록체인, 데이터 분석 등',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.code),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return '관심 기술을 입력해주세요';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _selectedDifficulty,
                decoration: const InputDecoration(
                  labelText: '학습 난이도',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.trending_up),
                ),
                items:
                    _difficulties.map((String difficulty) {
                      return DropdownMenuItem<String>(
                        value: difficulty,
                        child: Text(difficulty),
                      );
                    }).toList(),
                onChanged: (String? newValue) {
                  setState(() {
                    _selectedDifficulty = newValue!;
                  });
                },
              ),
              const SizedBox(height: 20),
              // API 키 유효성을 테스트하는 버튼 (개발/디버깅용)
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: _testApiKey,
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: const Text(
                    'API 키 테스트',
                    style: TextStyle(fontSize: 14),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              // 메인 도서 추천 요청 버튼
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _getRecommendations,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: Text(
                    _isLoading ? '추천 중...' : '책 추천받기',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// API 호출 중 로딩 상태를 표시하는 위젯
  Widget _buildLoadingWidget() {
    return const Center(
      child: Column(
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 16),
          Text('AI가 적합한 책을 찾고 있습니다...'),
        ],
      ),
    );
  }

  /// 에러 발생 시 에러 메시지를 표시하는 위젯
  Widget _buildErrorWidget() {
    return Card(
      color: Colors.red.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            Icon(Icons.error, color: Colors.red.shade700),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                _error!,
                style: TextStyle(color: Colors.red.shade700),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 추천받은 도서 목록을 표시하는 섹션 위젯
  Widget _buildRecommendationsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '📖 추천 도서',
          style: Theme.of(
            context,
          ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: _recommendations.length,
          itemBuilder: (context, index) {
            return _buildBookCard(_recommendations[index]);
          },
        ),
      ],
    );
  }

  /// 개별 도서 정보를 카드 형태로 표시하는 위젯
  /// [book]: 표시할 도서 정보
  Widget _buildBookCard(BookRecommendation book) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 60,
                  height: 80,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.book, size: 30, color: Colors.grey),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        book.title,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        book.author,
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey.shade600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          _buildDifficultyChip(book.difficulty),
                          if (book.rating != null) ...[
                            const SizedBox(width: 8),
                            Row(
                              children: [
                                const Icon(
                                  Icons.star,
                                  size: 16,
                                  color: Colors.amber,
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  book.rating!.toString(),
                                  style: const TextStyle(fontSize: 12),
                                ),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(book.description, style: const TextStyle(fontSize: 14)),
            if (book.publisher != null || book.publicationYear != null) ...[
              const SizedBox(height: 8),
              Text(
                '${book.publisher ?? ''} ${book.publicationYear ?? ''}',
                style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
              ),
            ],
          ],
        ),
      ),
    );
  }

  /// 학습 난이도를 색상별 칩으로 표시하는 위젯
  /// [difficulty]: 난이도 문자열 ("초급", "중급", "고급")
  /// Returns: 난이도에 따라 색상이 다른 칩 위젯
  Widget _buildDifficultyChip(String difficulty) {
    // 난이도별 색상 설정
    Color color;
    switch (difficulty) {
      case '초급':
        color = Colors.green; // 초급: 녹색
        break;
      case '중급':
        color = Colors.orange; // 중급: 주황색
        break;
      case '고급':
        color = Colors.red; // 고급: 빨간색
        break;
      default:
        color = Colors.grey; // 기본: 회색
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        difficulty,
        style: TextStyle(
          fontSize: 12,
          color: color,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  /// ChatGPT API를 호출하여 도서 추천을 받는 메인 함수
  /// 폼 유효성 검사 후 API 호출하고 결과를 상태에 반영
  Future<void> _getRecommendations() async {
    // 폼 유효성 검사
    if (!_formKey.currentState!.validate()) return;

    // 로딩 상태 시작 및 이전 결과/에러 초기화
    setState(() {
      _isLoading = true;
      _error = null;
      _recommendations = [];
    });

    try {
      // ChatGPT API 호출하여 도서 추천 받기
      final recommendations = await ChatGPTService.getBookRecommendations(
        major: _majorController.text,
        interests: _interestsController.text,
        difficulty: _selectedDifficulty,
      );

      // 성공 시 결과를 상태에 저장
      setState(() {
        _recommendations = recommendations;
        _isLoading = false;
      });
    } catch (e) {
      // 에러 발생 시 에러 메시지 저장
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// OpenAI API 키의 유효성을 테스트하는 함수 (개발/디버깅용)
  /// 간단한 API 호출로 키가 유효한지 확인하고 스낵바로 결과 표시
  Future<void> _testApiKey() async {
    try {
      final isValid = await ChatGPTService.testApiKey();

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(isValid ? 'API 키가 유효합니다!' : 'API 키가 유효하지 않습니다.'),
          backgroundColor: isValid ? Colors.green : Colors.red,
          duration: const Duration(seconds: 3),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('API 키 테스트 중 오류: $e'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }

  @override
  void dispose() {
    // 메모리 누수 방지를 위해 컨트롤러들 해제
    _majorController.dispose();
    _interestsController.dispose();
    super.dispose();
  }
}
