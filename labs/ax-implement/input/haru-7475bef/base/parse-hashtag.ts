/**
 * 텍스트에서 #프로젝트명 태그를 파싱하여 분리
 * 예: "할일 내용 #프로젝트A" → { cleanText: "할일 내용", projectName: "프로젝트A" }
 */
export function parseHashtag(text: string): {
  cleanText: string;
  projectName: string | null;
} {
  const match = text.match(/#(\S+)/);
  if (!match) {
    return { cleanText: text, projectName: null };
  }

  const projectName = match[1];
  const cleanText = text.replace(/#\S+/, "").trim();
  return { cleanText, projectName };
}
