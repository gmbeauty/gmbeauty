"use client";

import { CONTENT_TYPES } from "@/lib/content-types";
import { STYLE_PRESETS } from "@/lib/presets";
import type { EditorSettings } from "@/lib/types";

type Patch = (p: Partial<EditorSettings>) => void;

export function SidePanel({
  settings,
  onChange,
  silenceCount,
}: {
  settings: EditorSettings;
  onChange: Patch;
  silenceCount: number;
}) {
  return (
    <aside className="space-y-5 rounded-gm border border-gm-line bg-white p-4">
      <Field label="Tipo do vídeo">
        <select className={input} value={settings.contentType} onChange={(e) => onChange({ contentType: e.target.value as EditorSettings["contentType"] })}>
          {CONTENT_TYPES.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
        </select>
      </Field>

      <Field label="Estilo">
        <select className={input} value={settings.style} onChange={(e) => onChange({ style: e.target.value as EditorSettings["style"] })}>
          {STYLE_PRESETS.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
        </select>
      </Field>

      <Field label="Legenda">
        <Segmented
          value={settings.captionMode}
          onChange={(v) => onChange({ captionMode: v })}
          options={[
            { value: "traditional", label: "Tradicional" },
            { value: "highlight", label: "Destaque" },
            { value: "word-by-word", label: "Palavra a palavra" },
          ]}
        />
      </Field>

      <Field label="Fonte">
        <select className={input} disabled title="Escolha de fonte chega na Fase 5">
          <option>Inter (padrão)</option>
        </select>
      </Field>

      <Field label="Tamanho">
        <Segmented
          value={settings.fontSize}
          onChange={(v) => onChange({ fontSize: v })}
          options={[{ value: "sm", label: "P" }, { value: "md", label: "M" }, { value: "lg", label: "G" }]}
        />
      </Field>

      <Field label="Posição">
        <Segmented
          value={settings.position}
          onChange={(v) => onChange({ position: v })}
          options={[{ value: "top", label: "Topo" }, { value: "middle", label: "Meio" }, { value: "bottom", label: "Base" }]}
        />
      </Field>

      <Field label="Logo GM Beauty">
        <select className={input} value={settings.logo} onChange={(e) => onChange({ logo: e.target.value as EditorSettings["logo"] })}>
          <option value="none">Sem logo</option>
          <option value="top">Canto superior</option>
          <option value="bottom">Canto inferior</option>
          <option value="watermark">Marca d’água discreta</option>
        </select>
      </Field>

      <Toggle label={`Remover silêncios (${silenceCount} encontrados)`} checked={settings.removeSilences} onChange={(v) => onChange({ removeSilences: v })} />
      <Toggle label="Mostrar zonas seguras" checked={settings.showSafeZone} onChange={(v) => onChange({ showSafeZone: v })} />
    </aside>
  );
}

const input = "w-full rounded-lg border border-gm-line bg-white px-3 py-2 text-sm text-gm-ink focus:border-gm-lilac focus:outline-none disabled:bg-gm-bg disabled:text-gm-muted";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1.5 text-xs font-medium uppercase tracking-wide text-gm-muted">{label}</div>
      {children}
    </div>
  );
}

function Segmented<T extends string>({ value, onChange, options }: { value: T; onChange: (v: T) => void; options: { value: T; label: string }[] }) {
  return (
    <div className="flex rounded-full bg-gm-lilac-soft p-1">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          onClick={() => onChange(o.value)}
          aria-pressed={value === o.value}
          className={`flex-1 rounded-full px-2 py-1.5 text-xs font-medium transition ${value === o.value ? "bg-gm-purple text-white" : "text-gm-purple hover:bg-gm-lilac-mid"}`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-3 text-sm text-gm-ink">
      {label}
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="h-5 w-5 accent-[#4B1C71]" />
    </label>
  );
}
