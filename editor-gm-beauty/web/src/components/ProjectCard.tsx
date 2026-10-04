import Link from "next/link";
import { StatusBadge } from "./StatusBadge";
import { formatDate, formatDuration } from "@/lib/format";
import type { Project } from "@/lib/types";

export function ProjectCard({ project }: { project: Project }) {
  return (
    <article className="overflow-hidden rounded-gm border border-gm-line bg-white shadow-sm">
      <div className={`relative aspect-[9/12] bg-gradient-to-br ${project.thumbnailGradient}`}>
        <span className="absolute right-3 top-3">
          <StatusBadge status={project.status} />
        </span>
        <span className="absolute bottom-3 right-3 rounded-md bg-black/50 px-2 py-0.5 text-xs text-white">
          {formatDuration(project.durationSec)}
        </span>
      </div>
      <div className="space-y-3 p-4">
        <div>
          <h3 className="truncate font-medium text-gm-ink">{project.name}</h3>
          <p className="text-xs text-gm-muted">{formatDate(project.createdAt)}</p>
        </div>
        <div className="flex gap-2 text-sm">
          <Link href={`/editor/${project.id}`} className="rounded-full bg-gm-purple px-4 py-1.5 font-medium text-white hover:bg-[#3a1559]">
            Editar
          </Link>
          {/* Fase 1: botões ainda sem ação (mock) */}
          <button type="button" disabled title="Disponível em breve" className="rounded-full bg-gm-lilac-soft px-4 py-1.5 text-gm-purple opacity-60">
            Duplicar
          </button>
          <button type="button" disabled title="Disponível em breve" className="rounded-full px-4 py-1.5 text-gm-muted opacity-60">
            Excluir
          </button>
        </div>
      </div>
    </article>
  );
}
