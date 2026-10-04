"use client";

import { useRef } from "react";
import { cutRanges, removedSeconds } from "@/lib/cuts";
import { CONTENT_TYPES } from "@/lib/content-types";
import { formatTimestamp } from "@/lib/format";
import { STYLE_PRESETS } from "@/lib/presets";
import type { ContentTypeId, RenderSettings, SilenceRange, StylePresetId } from "@/lib/types";

export function SidePanel({
  settings,
  contentType,
  style,
  silences,
  showSafeZone,
  hasLogo,
  onSettings,
  onContentType,
  onStyle,
  onToggleSafeZone,
  onUploadLogo,
  onRemoveLogo,
  onSeek,
}: {
  settings: RenderSettings;
  contentType: ContentTypeId;
  style: StylePresetId;
  silences: SilenceRange[];
  showSafeZone: boolean;
  hasLogo: boolean;
  onSettings: (p: Partial<RenderSettings>) => void;
  onContentType: (v: ContentTypeId) => void;
  onStyle: (v: StylePresetId) => void;
  onToggleSafeZone: (v: boolean) => void;
  onUploadLogo: (f: File) => void;
  onRemoveLogo: () => void;
  onSeek: (t: number) => void;
}) {
  const logoInput = useRef<HTMLInputElement>(null);
  const cuts = cutRanges(silences, settings.silenceMinSec);

  return (
    <aside className="space-y-5 rounded-gm border border-gm-line bg-white p-4">
      <Field label="Tipo do vídeo">
        <select className={input} value={contentType} onChange={(e) => onContentType(e.target.value as ContentTypeId)}>
          {CONTENT_TYPES.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
        </select>
      </Field>

      <Field label="Estilo">
        <select className={input} value={style} onChange={(e) => onStyle(e.target.value as StylePresetId)}>
          {STYLE_PRESETS.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
        </select>
        <p className="mt-1 text-xs text-gm-muted">Trocar o estilo reaplica as configurações dele (menos a logo).</p>
      </Field>

      <Field label="Legenda">
        <Segmented
          value={settings.captionMode}
          onChange={(v) => onSettings({ captionMode: v })}
          options={[{ value: "traditional", label: "Tradicional" }, { value: "highlight", label: "Destaque" }, { value: "word-by-word", label: "Palavra a palavra" }]}
        />
      </Field>

      <Field label="Destaques automáticos">
        <select className={input} value={settings.highlightStrategy} onChange={(e) => onSettings({ highlightStrategy: e.target.value as RenderSettings["highlightStrategy"] })}>
          <option value="none">Nenhum (só os que eu marcar)</option>
          <option value="keywords">Palavra-chave de cada fala</option>
          <option value="offer">Preço, desconto e promoção</option>
        </select>
        <p className="mt-1 text-xs text-gm-muted">Só usa palavras que estão na fala. Substitui os destaques atuais.</p>
      </Field>

      <Field label="Cor do texto">
        <Colors value={settings.textColor} onChange={(v) => onSettings({ textColor: v })} />
      </Field>
      <Field label="Cor do destaque">
        <Colors value={settings.highlightColor} onChange={(v) => onSettings({ highlightColor: v })} />
      </Field>

      <Field label="Fonte">
        <select className={input} disabled title="A fonte é definida no servidor (CAPTION_FONT)">
          <option>Padrão do servidor</option>
        </select>
      </Field>

      <Field label="Tamanho">
        <Segmented value={settings.fontSize} onChange={(v) => onSettings({ fontSize: v })} options={[{ value: "sm", label: "P" }, { value: "md", label: "M" }, { value: "lg", label: "G" }]} />
      </Field>

      <Field label="Posição">
        <Segmented value={settings.position} onChange={(v) => onSettings({ position: v })} options={[{ value: "top", label: "Topo" }, { value: "middle", label: "Meio" }, { value: "bottom", label: "Base" }]} />
      </Field>

      <Field label="Logo GM Beauty">
        <select className={input} value={settings.logoPosition} onChange={(e) => onSettings({ logoPosition: e.target.value as RenderSettings["logoPosition"] })}>
          <option value="none">Sem logo</option>
          <option value="top">Canto superior</option>
          <option value="bottom">Canto inferior</option>
          <option value="watermark">Marca d’água discreta</option>
        </select>
        <div className="mt-2 flex items-center gap-2 text-xs">
          <input ref={logoInput} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={(e) => e.target.files?.[0] && onUploadLogo(e.target.files[0])} />
          <button type="button" onClick={() => logoInput.current?.click()} className="rounded-full bg-gm-lilac-soft px-3 py-1 text-gm-purple hover:bg-gm-lilac-mid">
            {hasLogo ? "Trocar logo" : "Enviar logo"}
          </button>
          {hasLogo && <button type="button" onClick={onRemoveLogo} className="text-gm-muted underline">Remover</button>}
        </div>
        {settings.logoPosition !== "none" && !hasLogo && <p className="mt-1 text-xs text-amber-700">Envie a logo para ela aparecer no vídeo.</p>}
        {settings.logoPosition !== "none" && (
          <div className="mt-3 space-y-2">
            <Slider label="Tamanho" min={8} max={50} step={1} value={settings.logoSizePct} suffix="%" onChange={(v) => onSettings({ logoSizePct: v })} />
            <Slider label="Transparência" min={10} max={100} step={5} value={Math.round(settings.logoOpacity * 100)} suffix="%" onChange={(v) => onSettings({ logoOpacity: v / 100 })} />
          </div>
        )}
      </Field>

      <div className="space-y-2">
        <Toggle label="Remover silêncios" checked={settings.removeSilences} onChange={(v) => onSettings({ removeSilences: v })} />
        <p className="text-xs text-gm-muted">
          {silences.length === 0
            ? "Nenhuma pausa longa encontrada."
            : `${silences.length} pausa(s) encontrada(s). ${settings.removeSilences ? `Serão removidos ${removedSeconds(cuts).toFixed(1)} s, mantendo um respiro natural.` : "Ligue para cortar só o miolo das pausas longas."}`}
        </p>
        <label className="flex items-center justify-between gap-3 text-xs text-gm-muted">
          Cortar pausas maiores que
          <select className="rounded-lg border border-gm-line px-2 py-1 text-gm-ink" value={settings.silenceMinSec} onChange={(e) => onSettings({ silenceMinSec: Number(e.target.value) })}>
            {[0.5, 0.6, 0.8, 1.0].map((v) => <option key={v} value={v}>{v.toString().replace(".", ",")} s</option>)}
          </select>
        </label>
        {silences.length > 0 && (
          <ul className="max-h-28 overflow-y-auto text-xs text-gm-muted">
            {silences.map((s) => (
              <li key={s.id}>
                <button type="button" onClick={() => onSeek(s.startSec)} className="hover:text-gm-purple">
                  {formatTimestamp(s.startSec)} → {formatTimestamp(s.endSec)} ({(s.endSec - s.startSec).toFixed(1)} s)
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <Toggle label="Mostrar zonas seguras" checked={showSafeZone} onChange={onToggleSafeZone} />
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
        <button key={o.value} type="button" onClick={() => onChange(o.value)} aria-pressed={value === o.value}
          className={`flex-1 rounded-full px-2 py-1.5 text-xs font-medium transition ${value === o.value ? "bg-gm-purple text-white" : "text-gm-purple hover:bg-gm-lilac-mid"}`}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

function Colors({ value, onChange }: { value: RenderSettings["textColor"]; onChange: (v: RenderSettings["textColor"]) => void }) {
  const opts = [{ v: "white", c: "#ffffff", l: "Branco" }, { v: "lilac", c: "#B57EDC", l: "Lilás GM" }, { v: "purple", c: "#4B1C71", l: "Roxo GM" }] as const;
  return (
    <div className="flex gap-2">
      {opts.map((o) => (
        <button key={o.v} type="button" onClick={() => onChange(o.v)} aria-pressed={value === o.v} aria-label={o.l} title={o.l}
          className={`h-8 w-8 rounded-full border ${value === o.v ? "ring-2 ring-gm-purple ring-offset-2" : "border-gm-line"}`} style={{ background: o.c }} />
      ))}
    </div>
  );
}

function Slider({ label, min, max, step, value, suffix, onChange }: { label: string; min: number; max: number; step: number; value: number; suffix: string; onChange: (v: number) => void }) {
  return (
    <label className="flex items-center gap-2 text-xs text-gm-muted">
      <span className="w-24">{label}</span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} className="flex-1 accent-[#4B1C71]" />
      <span className="w-9 text-right tabular-nums">{value}{suffix}</span>
    </label>
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
