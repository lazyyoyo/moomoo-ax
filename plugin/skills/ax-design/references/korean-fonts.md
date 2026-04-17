# 한국어 폰트 가이드

한국어 웹 프로젝트에서 사용할 수 있는 주요 폰트 목록.
CDN 링크, 적용 방법, 용도 분류를 포함.

> Pretendard는 한국어 웹에서 가장 많이 사용되는 폰트 (HTTP Archive 2024 기준 한국어 폰트 1위).
> 한국어 무료 폰트 전체 목록은 눈누(noonnu.cc)에서 확인 가능.

---

## 고딕 (Sans Serif) 계열

### Pretendard
- **성격**: 시스템 UI 대체 폰트. 크로스 플랫폼에서 자연스럽고 현대적
- **기반**: Inter + 본고딕 + M PLUS 1p을 다듬어 제작
- **특징**: 9가지 굵기, 가변(variable) 폰트 지원, 추가 가독성 보정 불필요
- **변형**: Pretendard JP (일본), Pretendard Std (라틴), Pretendard GOV (공공)
- **Best for**: 거의 모든 웹 프로젝트의 기본 선택. UI, 앱, 웹사이트
- **CDN (jsDelivr)**:
  ```html
  <link rel="stylesheet" as="style" crossorigin
    href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
  ```
- **CDN (cdnjs)**:
  ```html
  <link rel="stylesheet" as="style" crossorigin
    href="https://cdnjs.cloudflare.com/ajax/libs/pretendard/1.3.9/static/pretendard.min.css" />
  ```
- **CDN (UNPKG)**:
  ```html
  <link rel="stylesheet" as="style" crossorigin
    href="https://unpkg.com/pretendard@1.3.9/dist/web/static/pretendard.css" />
  ```
- **Variable font (jsDelivr)**:
  ```html
  <link rel="stylesheet" as="style" crossorigin
    href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css" />
  ```
- **font-family 추천 (동일 환경 우선)**:
  ```css
  font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont,
    system-ui, Roboto, "Helvetica Neue", "Segoe UI", "Apple SD Gothic Neo",
    "Noto Sans KR", "Malgun Gothic", "Apple Color Emoji", "Segoe UI Emoji",
    "Segoe UI Symbol", sans-serif;
  ```
- **npm**: `npm install pretendard` 또는 `yarn add pretendard`
- **Next.js**: 로컬 폰트 기능으로 적용 가능
- **GitHub**: https://github.com/orioncactus/pretendard

---

### Noto Sans KR (본고딕)
- **성격**: 구글/어도비 협업의 글로벌 폰트. 중립적이고 깔끔
- **특징**: 다국어 지원(CJK 통합), 다양한 weight, Google Fonts에서 바로 사용 가능
- **Best for**: 다국어 프로젝트, 안정적인 기본 선택
- **CDN (Google Fonts)**:
  ```html
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100..900&display=swap"
    rel="stylesheet">
  ```
- **font-family**:
  ```css
  font-family: 'Noto Sans KR', sans-serif;
  ```
- **주의**: 파일 크기가 크므로(CJK 폰트 특성) subset 로딩 권장

---

### SUIT
- **성격**: Pretendard와 유사한 시스템 UI 대체 폰트
- **특징**: 9가지 굵기, variable font 지원
- **Best for**: Pretendard의 대안, 약간 다른 톤이 필요할 때
- **눈누**: https://noonnu.cc/font_page/845

---

### 나눔고딕 (Nanum Gothic)
- **성격**: 네이버가 만든 한국의 대표적 무료 폰트
- **특징**: 오랫동안 한국 웹의 기본 폰트 역할, Google Fonts 지원
- **Best for**: 레거시 프로젝트, 나눔 브랜딩과 일관성이 필요한 경우
- **CDN (Google Fonts)**:
  ```html
  <link href="https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap"
    rel="stylesheet">
  ```
- **주의**: 2026년 기준으로는 Pretendard나 Noto Sans KR이 더 현대적 선택

---

### 나눔스퀘어 (Nanum Square)
- **성격**: 나눔고딕보다 각진 느낌, 타이틀에 강한 존재감
- **Best for**: 헤드라인, 배너, 포스터
- **눈누**: https://noonnu.cc/font_page/20

---

### Gmarket Sans
- **성격**: 활기차고 현대적, 약간 둥근 느낌
- **특징**: 3가지 weight (Light, Medium, Bold)
- **Best for**: 이커머스, 마케팅, 밝은 톤의 브랜딩
- **눈누**: https://noonnu.cc/font_page/40

---

### eScoreDream
- **성격**: 깔끔하고 세련된 현대적 고딕
- **특징**: 9가지 굵기
- **Best for**: 기업 사이트, 프레젠테이션, 폭넓은 weight가 필요한 프로젝트
- **눈누**: https://noonnu.cc/font_page/313

---

### KoPub Dotum (KoPub 돋움)
- **성격**: 한국출판인회의의 공식 폰트, 안정적이고 가독성 우수
- **Best for**: 출판, 공식 문서, 긴 본문
- **눈누**: https://noonnu.cc/font_page/24

---

## 명조 (Serif) 계열

### MaruBuri (마루부리)
- **성격**: 전통적이면서 부드러운 명조체
- **Best for**: 문학, 리딩 서비스, 감성적 콘텐츠, 에디토리얼
- **눈누**: https://noonnu.cc/font_page/679

---

### 나눔명조 (Nanum Myeongjo)
- **성격**: 전통적, 격식있는 느낌
- **특징**: 세리프 장식, 긴 텍스트에서 눈의 피로 감소
- **Best for**: 인쇄물, 책, 공식 문서, 문학 콘텐츠
- **CDN (Google Fonts)**:
  ```html
  <link href="https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&display=swap"
    rel="stylesheet">
  ```

---

### KoPub Batang (KoPub 바탕)
- **성격**: 출판인회의 공식 명조 폰트
- **Best for**: 출판, 공식 문서, 학술

---

### Noto Serif KR
- **성격**: Google/Adobe의 글로벌 serif, 중립적이고 가독성 좋은 명조
- **Best for**: 다국어 serif 프로젝트, 장문 본문
- **CDN (Google Fonts)**:
  ```html
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@200..900&display=swap"
    rel="stylesheet">
  ```

---

## 손글씨 / 디스플레이 계열

### Cafe24 Surround
- **성격**: 밝고 활기찬 핸드라이팅 느낌
- **Best for**: 카페, 라이프스타일 브랜드, 소셜미디어

### 여기어때 잘난체
- **성격**: 굵고 임팩트 있는 디스플레이
- **Best for**: 배너, 프로모션, 강한 헤드라인

### 강원교육모두체
- **성격**: 부드럽고 따뜻한, 교육적 느낌
- **Best for**: 교육, 아동, 공공 서비스

---

## 한국어 폰트 적용 시 주의사항

### word-break
```css
/* 한국어는 반드시 단어 단위로 줄바꿈 */
word-break: keep-all;
/* 줄바꿈 허용 지점을 추가로 제어 */
overflow-wrap: break-word;
```

### 줄간격 (line-height)
```css
/* 한글은 영문보다 넓은 줄간격이 필요 */
/* 본문: 1.6 ~ 1.8 */
/* 제목: 1.2 ~ 1.4 */
body { line-height: 1.7; }
h1, h2, h3 { line-height: 1.3; }
```

### 자간 (letter-spacing)
```css
/* 한글은 기본 자간이 적절한 경우가 많음 */
/* 제목에서 약간의 자간 조정은 OK */
h1 { letter-spacing: -0.02em; }
/* 본문에서는 건드리지 않는 것이 안전 */
```

### 폰트 로딩 최적화
```css
/* font-display: swap으로 FOUT 방지 */
@font-face {
  font-family: 'Pretendard';
  font-display: swap;
  /* ... */
}
```
```html
<!-- 중요 폰트는 preload -->
<link rel="preload" as="font" type="font/woff2" crossorigin
  href="/fonts/Pretendard-Regular.subset.woff2">
```

### Fallback Stack
```css
/* 한국어 프로젝트 기본 fallback stack */
font-family:
  'Pretendard Variable', Pretendard,     /* 1순위: 프로젝트 폰트 */
  -apple-system, BlinkMacSystemFont,      /* 2순위: 시스템 폰트 */
  'Apple SD Gothic Neo',                  /* 3순위: macOS 한글 */
  'Noto Sans KR',                         /* 4순위: 크로스플랫폼 한글 */
  'Malgun Gothic', '맑은 고딕',           /* 5순위: Windows 한글 */
  sans-serif;                             /* 최종 fallback */
```

### 파일 크기 관리
- 한국어 폰트는 글리프 수가 많아 파일 크기가 큼 (1~15MB)
- **subset 로딩**: Google Fonts는 자동 subset, 자체 호스팅 시 서브셋 도구 사용
- **Variable font**: 여러 weight를 하나의 파일로 → 전체 크기 절약
- **preload**: 첫 화면에 보이는 폰트만 preload, 나머지는 lazy

---

## 참고 리소스

- 눈누 (한국어 무료 폰트 모음): https://noonnu.cc/
- Pretendard GitHub: https://github.com/orioncactus/pretendard
- Google Fonts 한국어: https://fonts.google.com/?subset=korean
- 한글 허브 무료 폰트: https://hangulhub.co.kr/en/tools/fonts
