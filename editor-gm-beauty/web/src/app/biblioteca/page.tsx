import Link from "next/link";
import { Header } from "@/components/Header";
import { BrollLibrary } from "@/components/BrollLibrary";
import { SfxLibrary } from "@/components/SfxLibrary";

export default function LibraryPage() {
  return (
    <>
      <Header>
        <Link href="/" className="text-sm text-gm-muted hover:text-gm-purple">← Projetos</Link>
      </Header>
      <main className="mx-auto w-full max-w-3xl flex-1 space-y-10 px-4 py-8 sm:px-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-gm-purple">Biblioteca GM</h1>
          <p className="mt-1 text-gm-muted">Os arquivos que o editor pode usar nos seus vídeos.</p>
        </div>
        <BrollLibrary />
        <SfxLibrary />
      </main>
    </>
  );
}
