"use client";

import Link from "next/link";
import { StatusBadge } from "./StatusBadge";
import { urls } from "@/lib/api";
import { formatDate, formatDuration } from "@/lib/format";
import type { Project } from "@/lib/types";

export function ProjectCard({
  project,
  onDuplicate,
  onDelete,
}: {
  project: Project;
  onDuplicate: () => void;
  onDelete: () => void;
}) {
  const busy = project.status === "processing";
  return (
    <article className="overflow-hidden rounded-gm border border-gm-line bg-white shadow-sm">
      <Link href={`/editor/${project.id}`} className="relative block aspect-[9/12] bg-gradient-to-br from-gm-lilac-mid to-gm-lilac">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={urls.thumbnail(project.id)} alt="" className="h-full w-full object-cover" />
        <span className="absolute right-3 top-3">
          <StatusBadge status={project.status} />
        </span>
        <span className="absolute bottom-3 right-3 rounded-md bg-black/50 px-2 py-0.5 text-xs text-white">
          {formatDuration(project.durationSec)}
        </span>
      </Link>
      <div className="space-y-3 p-4">
        <div>
          <h3 className="truncate font-medium text-gm-ink" title={project.name}>{project.name}</h3>
          <p className="text-xs text-gm-muted">{formatDate(project.createdAt)}</p>
          {project.status === "error" && project.errorMessage && (
            <p className="mt-1 text-xs text-rose-600">{project.errorMessage}</p>
          )}
        </div>
        <div className="flex flex-wrap gap-2 text-sm">
          <Link href={`/editor/${project.id}`} className="rounded-full bg-gm-purple px-4 py-1.5 font-medium text-white hover:bg-[#3a1559]">
            Editar
          </Link>
          <button type="button" onClick={onDuplicate} disabled={busy} className="rounded-full bg-gm-lilac-soft px-4 py-1.5 text-gm-purple hover:bg-gm-lilac-mid disabled:opacity-50">
            Duplicar
          </button>
          <button type="button" onClick={onDelete} disabled={busy} className="rounded-full px-4 py-1.5 text-gm-muted hover:bg-rose-50 hover:text-rose-700 disabled:opacity-50">
            Excluir
          </button>
        </div>
      </div>
    </article>
  );
}
