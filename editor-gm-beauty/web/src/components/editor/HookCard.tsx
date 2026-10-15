"use client";

import { Button } from "@/components/Button";
import type { Hook } from "@/lib/types";

const LEVEL = {
  strong: { label: "Gancho forte", cls: "bg-emerald-50 text-emerald-700" },
  good: { label: "Gancho bom", cls: "bg-amber-50 text-amber-700" },
  weak: { label: "Gancho a melhorar", cls: "bg-rose-50 text-rose-700" },
} as const;

export function HookCard({
  hook,
  trimStartSec,
  onTrimStart,
  onHighlightHook,
}: {
  hook: Hook;
  trimStartSec: number;
  onTrimStart: (sec: number) => void;
  onHighlightHook: () => void;
}) {
  const lv = LEVEL[hook.level];
  return (
    <section className="rounded-gm border border-gm-line bg-white p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-medium text-gm-purple">Gancho dos primeiros 3 segundos</h3>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${lv.cls}`}>{lv.label}</span>
      </div>
      <ul className="space-y-3">
        {hook.checks.map((c) => (
          <li key={c.id} className="flex items-start gap-2 text-sm">
            <span aria-hidden className={c.ok ? "text-emerald-600" : "text-amber-600"}>{c.ok ? "✓" : "!"}</span>
            <div className="min-w-0 flex-1">
              <div className="text-gm-ink">{c.label}</div>
              {c.tip && <div className="text-xs text-gm-muted">{c.tip}</div>}
              {c.action === "trim_start" && hook.suggestedTrimSec !== null && (
                <Button variant="soft" className="mt-2 !px-3 !py-1 text-xs" onClick={() => onTrimStart(hook.suggestedTrimSec!)}>
                  Cortar {hook.suggestedTrimSec.toFixed(1).replace(".", ",")} s do início
                </Button>
              )}
              {c.action === "highlight_hook" && (
                <Button variant="soft" className="mt-2 !px-3 !py-1 text-xs" onClick={onHighlightHook}>
                  Destacar palavra do gancho
                </Button>
              )}
            </div>
          </li>
        ))}
      </ul>
      {trimStartSec > 0 && (
        <p className="mt-3 text-xs text-gm-muted">
          Início cortado: {trimStartSec.toFixed(1).replace(".", ",")} s.{" "}
          <button type="button" onClick={() => onTrimStart(0)} className="underline hover:text-gm-purple">Desfazer</button>
        </p>
      )}
      <p className="mt-3 text-[11px] text-gm-muted">Checagem por regras simples sobre a transcrição; use como guia, não como regra.</p>
    </section>
  );
}
