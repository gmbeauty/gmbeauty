import { Header } from "@/components/Header";
import { ButtonLink } from "@/components/Button";
import { ProjectCard } from "@/components/ProjectCard";
import { listProjects } from "@/lib/api";

export default async function DashboardPage() {
  const projects = await listProjects();

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
        {projects.length === 0 ? (
          <div className="rounded-gm border border-dashed border-gm-lilac-mid bg-gm-bg p-12 text-center text-gm-muted">
            Nenhum projeto ainda. Clique em “+ Novo vídeo” para começar.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {projects.map((p) => (
              <ProjectCard key={p.id} project={p} />
            ))}
          </div>
        )}

        <p className="mt-10 text-xs text-gm-muted">Fase 1: projetos de demonstração (dados fictícios).</p>
      </main>
    </>
  );
}
