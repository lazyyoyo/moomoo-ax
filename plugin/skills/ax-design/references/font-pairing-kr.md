# 한글 ↔ 영문 폰트 페어링 가이드

한국어 프로젝트에서 한글 폰트와 영문 폰트를 자연스럽게 조합하는 가이드.

---

## 페어링 원칙

1. **설계 기반 매칭**: 같은 설계 철학(geometric, humanist 등)의 폰트끼리 가장 자연스러움
2. **x-height 매칭**: 한글과 영문의 시각적 크기가 비슷해야 혼용 시 어색하지 않음
3. **weight 매칭**: 같은 weight에서 한글과 영문의 굵기 인상이 비슷한지 확인
4. **역할 분리**: 한글 본문 폰트와 영문 디스플레이 폰트를 섞어 사용하는 것도 유효
5. **테스트 필수**: 실제 한영 혼용 텍스트로 다양한 크기에서 확인

---

## 고딕 (Sans Serif) 페어링

### Pretendard ↔ 영문 조합

| 영문 폰트 | 관계 | 적합도 | 용도 |
|-----------|------|--------|------|
| **Inter** | 동일 설계 계열 (Pretendard가 Inter 기반) | ★★★★★ | 가장 자연스러운 기본 조합. UI, SaaS, 앱 |
| **Roboto** | 유사한 중립적 성격 | ★★★★☆ | 안정적인 대안 |
| **DM Sans** | geometric 계열 매칭 | ★★★★☆ | 미니멀 프로젝트 |
| **Plus Jakarta Sans** | 친근한 톤 매칭 | ★★★★☆ | 모던 브랜딩, 앱 |
| **Work Sans** | 화면 최적화 공통점 | ★★★★☆ | 대시보드, 인터페이스 |
| **Space Grotesk** | geometric + 약간의 개성 | ★★★☆☆ | 테크, 스타트업 |
| **Manrope** | 깨끗하고 다목적 | ★★★★☆ | 브랜딩, 웹사이트 |

**Pretendard + Inter CSS 예시:**
```css
/* 한글은 Pretendard, 영문은 Inter */
body {
  font-family: Inter, 'Pretendard Variable', Pretendard, sans-serif;
  /* 브라우저는 각 글리프에 맞는 폰트를 자동 선택 */
}
```

---

### Noto Sans KR ↔ 영문 조합

| 영문 폰트 | 관계 | 적합도 | 용도 |
|-----------|------|--------|------|
| **Noto Sans** | 동일 패밀리 | ★★★★★ | 다국어 프로젝트의 정석 |
| **Open Sans** | 유사한 중립적 humanist | ★★★★☆ | 범용 |
| **Source Sans Pro** | Adobe 패밀리 (Noto도 Adobe 협업) | ★★★★☆ | 기업, 문서 |

---

### SUIT ↔ 영문 조합

| 영문 폰트 | 관계 | 적합도 | 용도 |
|-----------|------|--------|------|
| **DM Sans** | geometric 매칭 | ★★★★☆ | 미니멀, 현대적 |
| **Poppins** | geometric + 친근한 | ★★★★☆ | 브랜딩, 마케팅 |
| **Epilogue** | 깨끗하고 절제된 | ★★★☆☆ | 콘텐츠 중심 |

---

### Gmarket Sans ↔ 영문 조합

| 영문 폰트 | 관계 | 적합도 | 용도 |
|-----------|------|--------|------|
| **Rubik** | 둥근 모서리 매칭 | ★★★★☆ | 이커머스, 밝은 브랜딩 |
| **Nunito** | 둥글고 친근한 | ★★★★☆ | 캐주얼, 마케팅 |
| **Cabin** | 따뜻한 톤 매칭 | ★★★☆☆ | 라이프스타일 |

---

## 명조 (Serif) 페어링

### MaruBuri ↔ 영문 조합

| 영문 폰트 | 관계 | 적합도 | 용도 |
|-----------|------|--------|------|
| **Playfair Display** | 우아한 디스플레이 serif 매칭 | ★★★★★ | 에디토리얼, 문학, 리딩 서비스 |
| **EB Garamond** | 클래식 serif 매칭 | ★★★★★ | 장문 콘텐츠, 학술 |
| **Libre Baskerville** | 권위 + 가독성 매칭 | ★★★★☆ | 출판, 뉴스 |
| **Instrument Serif** | 현대적 serif | ★★★★☆ | 에디토리얼, 모던 클래식 |
| **Lora** | 브러시 캘리그래피 영향의 serif | ★★★☆☆ | 블로그, 에세이 |

**MaruBuri + Playfair Display CSS 예시:**
```css
h1, h2, h3 {
  font-family: 'Playfair Display', 'MaruBuri', serif;
}
body {
  font-family: 'MaruBuri', Georgia, serif;
  line-height: 1.8;
}
```

---

### 나눔명조 ↔ 영문 조합

| 영문 폰트 | 관계 | 적합도 | 용도 |
|-----------|------|--------|------|
| **Georgia** | 클래식 web serif | ★★★★☆ | 레거시, 범용 |
| **PT Serif** | 다국어 지원 serif | ★★★★☆ | 다국어 프로젝트 |
| **Merriweather** | 화면 최적화 serif | ★★★☆☆ | 블로그, 장문 |

---

### Noto Serif KR ↔ 영문 조합

| 영문 폰트 | 관계 | 적합도 | 용도 |
|-----------|------|--------|------|
| **Noto Serif** | 동일 패밀리 | ★★★★★ | 다국어의 정석 |
| **Roboto Serif** | 현대적 serif 매칭 | ★★★★☆ | 앱, 웹 본문 |

---

## 크로스 카테고리 페어링 (한글 고딕 + 영문 Serif, 또는 그 반대)

### 한글 고딕(본문) + 영문 Serif(제목)

| 한글 | 영문 | 효과 | 용도 |
|------|------|------|------|
| Pretendard (본문) | Bodoni Moda (제목) | 럭셔리 + 현대적 | 패션, 하이엔드 |
| Pretendard (본문) | Abril Fatface (제목) | 임팩트 + 깔끔 | 에디토리얼, 매거진 |
| Noto Sans KR (본문) | Instrument Serif (제목) | 중립 + 세련 | 기업, 브랜드 |
| SUIT (본문) | EB Garamond (제목) | 모던 + 클래식 | 학술, 문화 |

### 한글 명조(본문) + 영문 Sans(제목)

| 한글 | 영문 | 효과 | 용도 |
|------|------|------|------|
| MaruBuri (본문) | Oswald (제목) | 전통 + 강한 존재감 | 매거진, 뉴스 |
| MaruBuri (본문) | Raleway (제목) | 따뜻한 + 우아한 | 라이프스타일, 문학 |
| 나눔명조 (본문) | Manrope (제목) | 클래식 + 현대적 | 블로그, 에세이 |

---

## 도메인별 추천 세트

### SaaS / 웹앱
```css
/* 기본 */
--font-heading: Inter, 'Pretendard Variable', sans-serif;
--font-body: 'Pretendard Variable', Inter, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

### 콘텐츠 / 리딩 서비스
```css
/* Rubato 같은 읽기 서비스에 추천 */
--font-heading: 'Playfair Display', 'MaruBuri', serif;
--font-body: 'MaruBuri', Georgia, serif;
--font-ui: 'Pretendard Variable', sans-serif;
```

### 랜딩페이지 / 마케팅
```css
/* 임팩트 있는 조합 */
--font-heading: 'Abril Fatface', 'MaruBuri Bold', serif;
--font-body: 'Pretendard Variable', Inter, sans-serif;
```

### 대시보드 / 어드민
```css
/* 가독성 + 데이터 밀도 */
--font-heading: 'Pretendard Variable', sans-serif;
--font-body: 'Pretendard Variable', sans-serif;
--font-mono: 'Fira Code', 'Source Code Pro', monospace;
--font-data: 'Tabular Nums', 'Pretendard Variable', sans-serif;
```

### 크리에이티브 / 포트폴리오
```css
/* 실험적 — 프로젝트마다 다르게 */
--font-heading: /* display 폰트 선택 */;
--font-body: 'Pretendard Variable', sans-serif;
/* 또는 */
--font-body: 'MaruBuri', serif;
```

---

## 기술적 구현 팁

### 한글-영문 동시 적용 시 font-family 순서
```css
/* 영문 폰트를 먼저, 한글 폰트를 뒤에 */
/* 브라우저가 영문 글리프는 영문 폰트에서, 한글은 한글 폰트에서 가져감 */
font-family: 'Inter', 'Pretendard', sans-serif;
```

### Variable Font으로 weight 통일
```css
/* Pretendard Variable + Inter Variable */
@font-face {
  font-family: 'Pretendard Variable';
  font-weight: 100 900;
  font-display: swap;
  src: url('/fonts/PretendardVariable.woff2') format('woff2');
}

body {
  font-family: 'Inter var', 'Pretendard Variable', sans-serif;
  font-weight: 400; /* 자연스럽게 두 폰트 모두 400 적용 */
}

h1 {
  font-weight: 700; /* 두 폰트 모두 700 */
}
```

### Next.js에서의 적용
```tsx
import localFont from 'next/font/local';
import { Inter } from 'next/font/google';

const pretendard = localFont({
  src: '../fonts/PretendardVariable.woff2',
  display: 'swap',
  variable: '--font-pretendard',
});

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export default function RootLayout({ children }) {
  return (
    <html className={`${pretendard.variable} ${inter.variable}`}>
      <body>{children}</body>
    </html>
  );
}
```
```css
body {
  font-family: var(--font-inter), var(--font-pretendard), sans-serif;
}
```
