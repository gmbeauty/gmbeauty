"use client";

import { useCallback, useEffect, useState } from "react";
import { ProjectCard } from "./ProjectCard";
import { deleteProject, duplicateProject, listProjects } from "@/lib/api";
import type { Project } from "@/lib/types";

export function Dashboard() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setProjects(await listProjects());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Algo deu errado.");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    listProjects()
      .then((list) => !cancelled && setProjects(list))
      .catch((e) => !cancelled && setError(e instanceof Error ? e.message : "Algo deu errado."));
    return () => {
      cancelled = true;
    };
  }, []);

  // Enquanto algum vídeo estiver processando, atualiza a lista sozinha.
  const anyBusy = projects?.some((p) => p.status === "processing");
  useEffect(() => {
    if (!anyBusy) return;
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [anyBusy, load]);

  async function act(fn: () => Promise<unknown>) {
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Algo deu errado.");
      return;
    }
    load();
  }

  function remove(p: Project) {
    if (confirm(`Excluir "${p.name}" para sempre? O vídeo e todos os arquivos serão apagados e isso não pode ser desfeito.`)) {
      act(() => deleteProject(p.id));
    }
  }

  if (error && !projects) {
    return (
      <div role="alert" className="rounded-gm border border-rose-200 bg-rose-50 p-6 text-rose-700">
        {error}
        <button onClick={load} className="ml-3 underline">Tentar de novo</button>
      </div>
    );
  }
  if (!projects) return <p className="text-gm-muted">Carregando…</p>;

  return (
    <>
      {error && <p role="alert" className="mb-4 text-sm text-rose-600">{error}</p>}
      {projects.length === 0 ? (
        <div className="rounded-gm border border-dashed border-gm-lilac-mid bg-gm-bg p-12 text-center text-gm-muted">
          Nenhum projeto ainda. Clique em “+ Novo vídeo” para começar.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} onDuplicate={() => act(() => duplicateProject(p.id))} onDelete={() => remove(p)} />
          ))}
        </div>
      )}
    </>
  );
}
