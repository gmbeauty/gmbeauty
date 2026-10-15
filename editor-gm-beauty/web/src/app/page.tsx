import { Header } from "@/components/Header";
import { ButtonLink } from "@/components/Button";
import { Dashboard } from "@/components/Dashboard";

export default function DashboardPage() {
  return (
    <>
      <Header>
        <ButtonLink href="/novo">+ Novo vídeo</ButtonLink>
      </Header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight text-gm-purple sm:text-3xl">Editor de Vídeos</h1>
          <p className="mt-1 text-gm-muted">Transforme vídeos brutos em conteúdo pronto para postar.</p>
        </div>
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-gm-muted">Projetos recentes</h2>
        <Dashboard />
      </main>
    </>
  );
}
