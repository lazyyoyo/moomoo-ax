import type { ReactNode } from "react";
import { copy } from "@/i18n/copy";

export const metadata = {
  title: copy.home.title,
  description: copy.home.description,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
