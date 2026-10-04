import type { ProjectStatus } from "@/lib/types";

const STATUS: Record<ProjectStatus, { label: string; cls: string }> = {
  draft: { label: "Rascunho", cls: "bg-gray-100 text-gray-600" },
  processing: { label: "Processando", cls: "bg-amber-50 text-amber-700" },
  ready: { label: "Pronto", cls: "bg-emerald-50 text-emerald-700" },
  error: { label: "Erro", cls: "bg-rose-50 text-rose-700" },
};

export function StatusBadge({ status }: { status: ProjectStatus }) {
  const s = STATUS[status];
  return <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${s.cls}`}>{s.label}</span>;
}
