# UniBooks - AI 기반 도서 추천 앱

UniBooks는 사용자의 전공 분야, 관심 기술, 학습 난이도를 분석하여 ChatGPT API를 통해 맞춤형 도서를 추천해주는 Flutter 앱입니다.

## 주요 기능

- 📚 전공 분야별 맞춤 도서 추천
- 🔍 관심 기술에 따른 개인화된 추천
- 📊 학습 난이도 설정 (초급/중급/고급)
- 🤖 ChatGPT API를 활용한 AI 기반 추천
- 📱 직관적이고 현대적인 UI/UX

## 설정 방법

### 1. OpenAI API 키 설정

1. [OpenAI 웹사이트](https://platform.openai.com/)에서 계정을 생성하고 API 키를 발급받습니다.
2. 프로젝트 루트 디렉토리의 `.env` 파일을 열어 다음과 같이 설정합니다:

```bash
OPENAI_API_KEY=your_actual_api_key_here
```

**중요:** `.env` 파일에는 실제 API 키를 입력해야 하며, 이 파일은 절대 Git에 커밋하지 마세요.

### 2. 의존성 설치

```bash
flutter pub get
flutter packages pub run build_runner build
```

### 3. 앱 실행

```bash
flutter run
```

## 실제 ChatGPT API 사용하기

현재 앱은 테스트를 위해 Mock 데이터를 사용하고 있습니다. 실제 ChatGPT API를 사용하려면:

1. `.env` 파일에 유효한 OpenAI API 키를 설정합니다.
2. `lib/screens/home_screen.dart` 파일의 `_getRecommendations()` 메서드에서 다음 부분을 변경합니다:

```dart
// 현재 (Mock 데이터 사용):
final recommendations = await MockBookService.getMockRecommendations(
  major: _majorController.text,
  interests: _interestsController.text,
  difficulty: _selectedDifficulty,
);

// 실제 API 사용으로 변경:
final recommendations = await ChatGPTService.getBookRecommendations(
  major: _majorController.text,
  interests: _interestsController.text,
  difficulty: _selectedDifficulty,
);
```

## 프로젝트 구조

```
lib/
├── main.dart                    # 앱 진입점
├── models/
│   └── book_recommendation.dart # 도서 추천 데이터 모델
├── services/
│   └── chatgpt_service.dart    # ChatGPT API 서비스
└── screens/
    └── home_screen.dart        # 메인 화면
```

## 사용된 패키지

- `http`: HTTP 요청을 위한 패키지
- `flutter_riverpod`: 상태 관리 패키지
- `json_annotation`: JSON 직렬화를 위한 어노테이션
- `json_serializable`: JSON 직렬화 코드 자동 생성
- `build_runner`: 코드 생성 도구
- `dartz`: 함수형 프로그래밍 지원

## 주의사항

- 백엔드 서버가 실행되어 있어야 앱이 정상적으로 작동합니다.
- 개발 중에는 적절한 테스트 데이터를 사용하는 것을 권장합니다.

## 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이센스

이 프로젝트는 MIT 라이센스 하에 있습니다.
