import { copy } from "@/i18n/copy";

export default function HomePage() {
  return (
    <main>
      <h1>{copy.home.title}</h1>
      <p>{copy.home.description}</p>
    </main>
  );
}
