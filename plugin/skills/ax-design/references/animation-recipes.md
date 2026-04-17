# 모션 & 애니메이션 레시피

프론트엔드 모션 패턴별 코드 스니펫 모음.
Build phase에서 Plan 단계에서 결정한 모션을 구현할 때 참조.

> 라이브러리 선택은 `library-decision.md` 참조.
> 원칙: 모션은 의미가 있을 때만. 장식적 모션 금지. 한 화면에 최소 1개의 의미있는 모션.

---

## 1. 페이지 진입 애니메이션

### Fade-in + Slide-up (가장 범용적)

**CSS Only:**
```css
@keyframes fadeSlideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-enter {
  animation: fadeSlideUp 0.6s ease-out forwards;
}

/* Staggered reveal — 자식 요소들을 순차적으로 */
.stagger-container > * {
  opacity: 0;
  animation: fadeSlideUp 0.5s ease-out forwards;
}
.stagger-container > *:nth-child(1) { animation-delay: 0.1s; }
.stagger-container > *:nth-child(2) { animation-delay: 0.2s; }
.stagger-container > *:nth-child(3) { animation-delay: 0.3s; }
.stagger-container > *:nth-child(4) { animation-delay: 0.4s; }
```

**Motion (React):**
```tsx
import { motion } from "motion/react";

function FadeSlideUp({ children, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}

// Staggered container
function StaggerContainer({ children }) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: {},
        visible: { transition: { staggerChildren: 0.1 } },
      }}
    >
      {children}
    </motion.div>
  );
}

function StaggerItem({ children }) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
      }}
    >
      {children}
    </motion.div>
  );
}
```

**GSAP:**
```js
import gsap from "gsap";

// 단일 요소
gsap.from(".animate-enter", {
  opacity: 0,
  y: 20,
  duration: 0.6,
  ease: "power2.out",
});

// Staggered
gsap.from(".stagger-item", {
  opacity: 0,
  y: 20,
  duration: 0.5,
  stagger: 0.1,
  ease: "power2.out",
});
```

---

## 2. 스크롤 트리거 Reveal

### Intersection Observer (Vanilla JS)
```js
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("revealed");
        observer.unobserve(entry.target); // 한 번만 트리거
      }
    });
  },
  { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
);

document.querySelectorAll(".reveal-on-scroll").forEach((el) => {
  observer.observe(el);
});
```
```css
.reveal-on-scroll {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s ease-out, transform 0.6s ease-out;
}
.reveal-on-scroll.revealed {
  opacity: 1;
  transform: translateY(0);
}
```

**Motion (React) — whileInView:**
```tsx
<motion.div
  initial={{ opacity: 0, y: 30 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, margin: "-50px" }}
  transition={{ duration: 0.6, ease: "easeOut" }}
>
  {content}
</motion.div>
```

**GSAP ScrollTrigger:**
```js
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
gsap.registerPlugin(ScrollTrigger);

gsap.from(".reveal-section", {
  scrollTrigger: {
    trigger: ".reveal-section",
    start: "top 80%",
    toggleActions: "play none none none",
  },
  opacity: 0,
  y: 50,
  duration: 0.8,
  ease: "power2.out",
});
```

---

## 3. 호버 마이크로 인터랙션

### 카드 호버 — 리프트 효과
```css
.card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}
```

### 버튼 호버 — 스케일 + 컬러
```css
.btn {
  transition: transform 0.2s ease, background-color 0.2s ease;
}
.btn:hover {
  transform: scale(1.02);
  background-color: var(--color-primary-hover);
}
.btn:active {
  transform: scale(0.98);
}
```

### 이미지 호버 — 줌 인
```css
.image-container {
  overflow: hidden;
  border-radius: 12px;
}
.image-container img {
  transition: transform 0.5s ease;
}
.image-container:hover img {
  transform: scale(1.05);
}
```

### 링크 호버 — 밑줄 애니메이션
```css
.link {
  position: relative;
  text-decoration: none;
}
.link::after {
  content: "";
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background: var(--color-primary);
  transition: width 0.3s ease;
}
.link:hover::after {
  width: 100%;
}
```

---

## 4. 레이아웃 애니메이션

### Motion — 카드 리오더 / 리스트 변경
```tsx
import { AnimatePresence, motion } from "motion/react";

function AnimatedList({ items }) {
  return (
    <AnimatePresence mode="popLayout">
      {items.map((item) => (
        <motion.div
          key={item.id}
          layout
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
        >
          {item.content}
        </motion.div>
      ))}
    </AnimatePresence>
  );
}
```

### 탭 전환 — 슬라이딩 인디케이터
```tsx
function TabIndicator({ activeTab, tabs }) {
  return (
    <div className="relative flex">
      {tabs.map((tab, i) => (
        <button key={tab.id} onClick={() => setActive(i)}>
          {tab.label}
        </button>
      ))}
      <motion.div
        className="absolute bottom-0 h-0.5 bg-primary"
        layoutId="tab-indicator"
        transition={{ type: "spring", stiffness: 400, damping: 30 }}
      />
    </div>
  );
}
```

---

## 5. 패럴랙스 효과

### CSS Only (간단한 패럴랙스)
```css
.parallax-bg {
  background-image: url("/hero.jpg");
  background-attachment: fixed;
  background-size: cover;
  background-position: center;
  min-height: 60vh;
}
```

### Motion — 스크롤 기반 패럴랙스
```tsx
import { motion, useScroll, useTransform } from "motion/react";

function ParallaxSection() {
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], [0, -200]);

  return (
    <motion.div style={{ y }}>
      <img src="/background.jpg" alt="" />
    </motion.div>
  );
}
```

### GSAP — 다중 레이어 패럴랙스
```js
gsap.to(".parallax-bg", {
  scrollTrigger: {
    trigger: ".parallax-section",
    start: "top bottom",
    end: "bottom top",
    scrub: true,
  },
  y: -100,
  ease: "none",
});

gsap.to(".parallax-fg", {
  scrollTrigger: {
    trigger: ".parallax-section",
    start: "top bottom",
    end: "bottom top",
    scrub: true,
  },
  y: -200,
  ease: "none",
});
```

---

## 6. Kinetic Typography

### 스크롤에 따른 텍스트 크기 변화
```tsx
function KineticHeading() {
  const { scrollYProgress } = useScroll();
  const scale = useTransform(scrollYProgress, [0, 0.3], [1, 2.5]);
  const opacity = useTransform(scrollYProgress, [0.2, 0.35], [1, 0]);

  return (
    <motion.h1
      style={{ scale, opacity }}
      className="text-6xl font-bold text-center"
    >
      Your Headline Here
    </motion.h1>
  );
}
```

### 글자별 순차 등장
```tsx
function AnimatedText({ text }) {
  const letters = text.split("");
  return (
    <span>
      {letters.map((letter, i) => (
        <motion.span
          key={i}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.03, duration: 0.4 }}
        >
          {letter === " " ? "\u00A0" : letter}
        </motion.span>
      ))}
    </span>
  );
}
```

### GSAP — 텍스트 스크러빙 (스크롤에 글자 색상 변화)
```js
const text = document.querySelector(".scrub-text");
const chars = text.textContent.split("");
text.innerHTML = chars
  .map((c) => `<span class="char">${c}</span>`)
  .join("");

gsap.to(".char", {
  scrollTrigger: {
    trigger: ".scrub-text",
    start: "top 80%",
    end: "top 20%",
    scrub: true,
  },
  color: "#000",
  stagger: 0.02,
});
```

---

## 7. 페이지 전환 (Page Transition)

### Motion — 페이지 레벨 전환 (Next.js App Router)
```tsx
// layout.tsx
import { AnimatePresence } from "motion/react";

export default function Layout({ children }) {
  return <AnimatePresence mode="wait">{children}</AnimatePresence>;
}

// page.tsx
import { motion } from "motion/react";

export default function Page() {
  return (
    <motion.main
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
    >
      {/* page content */}
    </motion.main>
  );
}
```

---

## 8. 로딩 & 스켈레톤

### 스켈레톤 UI 펄스
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.skeleton {
  background: linear-gradient(90deg, #e0e0e0 25%, #f0f0f0 50%, #e0e0e0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### 스피너 (미니멀)
```css
.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
```

---

## 9. 3D 요소

### CSS 3D — 카드 틸트 (마우스 따라가기)
```js
const card = document.querySelector(".tilt-card");
card.addEventListener("mousemove", (e) => {
  const rect = card.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  const rotateX = ((y - centerY) / centerY) * -10;
  const rotateY = ((x - centerX) / centerX) * 10;
  card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
});
card.addEventListener("mouseleave", () => {
  card.style.transform = "perspective(1000px) rotateX(0) rotateY(0)";
  card.style.transition = "transform 0.5s ease";
});
```

---

## 모션 적용 원칙 체크리스트

- [ ] 이 모션은 사용자 경험을 개선하는가? (정보 전달, 맥락 제공, 상태 변화 표시)
- [ ] 모션 없이도 기능은 완전한가? (모션은 향상이지 필수가 아님)
- [ ] `prefers-reduced-motion` 미디어 쿼리를 존중하는가?
- [ ] 모션 duration이 적절한가? (300~600ms가 대부분의 UI 전환에 적합)
- [ ] ease 함수가 적절한가? (ease-out이 대부분의 진입에 자연스러움)
- [ ] 모바일에서 성능 테스트를 했는가?

### prefers-reduced-motion 존중
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

```tsx
// Motion (React) — 자동으로 존중하지만 명시적으로도 가능
import { useReducedMotion } from "motion/react";

function Component() {
  const shouldReduceMotion = useReducedMotion();
  return (
    <motion.div
      animate={{ x: shouldReduceMotion ? 0 : 100 }}
    />
  );
}
```
