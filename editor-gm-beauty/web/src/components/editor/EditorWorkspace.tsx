"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/Button";
import { CaptionList } from "./CaptionList";
import { SidePanel } from "./SidePanel";
import { Timeline } from "./Timeline";
import { VideoPreview } from "./VideoPreview";
import { HookCard } from "./HookCard";
import { SfxCard } from "./SfxCard";
import {
  analyzeProject, applyHighlightStrategy, exportProject, getInsights, getProject, hasLogo as fetchHasLogo,
  highlightHook, listSfx, patchProject, saveSfx, sfxAudioUrl, suggestSfx, removeLogo, saveCaptions, uploadLogo, urls,
} from "@/lib/api";
import { settingsForPreset } from "@/lib/presets";
import type { CaptionSegment, ContentTypeId, Insights, Project, RenderSettings, SfxEvent, SfxSound, StylePresetId } from "@/lib/types";

const STEPS: { stage: string; label: string }[] = [
  { stage: "audio", label: "Extraindo o áudio" },
  { stage: "transcricao", label: "Transcrevendo a fala (pode levar alguns minutos)" },
  { stage: "silencios", label: "Procurando pausas" },
  { stage: "legendas", label: "Montando as legendas" },
];

const msg = (e: unknown) => (e instanceof Error ? e.message : "Algo deu errado. Tente novamente.");

export function EditorWorkspace({ id }: { id: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [settings, setSettings] = useState<RenderSettings | null>(null);
  const [captions, setCaptions] = useState<CaptionSegment[]>([]);
  const [insights, setInsights] = useState<Insights>({ zoomPlan: [], hook: null });
  const [sfxEvents, setSfxEvents] = useState<SfxEvent[]>([]);
  const [sfxSounds, setSfxSounds] = useState<SfxSound[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [currentSec, setCurrentSec] = useState(0);
  const [showSafeZone, setShowSafeZone] = useState(true);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [logoVersion, setLogoVersion] = useState<number | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Cópias "mais recentes" para os salvamentos automáticos (com atraso) lerem.
  const latestCaptions = useRef(captions);
  const latestSettings = useRef(settings);
  useEffect(() => { latestCaptions.current = captions; }, [captions]);
  useEffect(() => { latestSettings.current = settings; }, [settings]);
  const capTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const setTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const capDirty = useRef(false);
  const setDirty = useRef(false);
  const prevStage = useRef<string | null>(null);

  // Plano de zoom e análise do gancho (calculados no servidor a partir das legendas e configurações salvas).
  const refreshInsights = useCallback(async () => {
    try {
      setInsights(await getInsights(id));
    } catch {
      /* é só um complemento; o editor continua funcionando */
    }
  }, [id]);

  // ---------- carregar ----------
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [p, logo, sounds] = await Promise.all([getProject(id), fetchHasLogo(), listSfx().catch(() => [] as SfxSound[])]);
        if (cancelled) return;
        setProject(p);
        setSfxEvents(p.sfxEvents);
        setSfxSounds(sounds);
        setSettings(p.settings);
        setCaptions(p.captions);
        setSelectedId(p.captions[0]?.id ?? null);
        setLogoVersion(logo ? Date.now() : null);
        if (p.analyzed) setInsights(await getInsights(id));
      } catch (e) {
        if (!cancelled) setError(msg(e));
      }
    })();
    return () => { cancelled = true; };
  }, [id]);

  // ---------- acompanhar processamento ----------
  const processing = project?.status === "processing";
  useEffect(() => {
    if (!processing) return;
    const t = setInterval(async () => {
      try {
        const p = await getProject(id);
        const wasAnalysis = prevStage.current !== null && prevStage.current !== "render";
        if (p.status !== "processing" && wasAnalysis && p.analyzed) {
          setCaptions(p.captions);
          setSettings(p.settings);
          setSelectedId(p.captions[0]?.id ?? null);
          refreshInsights();
        }
        prevStage.current = p.status === "processing" ? p.stage : null;
        setProject(p);
      } catch (e) {
        setError(msg(e));
      }
    }, 1500);
    return () => clearInterval(t);
  }, [processing, id, refreshInsights]);
  useEffect(() => { if (project?.status === "processing") prevStage.current = project.stage; }, [project?.status, project?.stage]);

  // ---------- salvar automaticamente ----------
  const flushCaptions = useCallback(async () => {
    clearTimeout(capTimer.current);
    if (!capDirty.current) return;
    capDirty.current = false;
    try {
      await saveCaptions(id, latestCaptions.current);
      setSaveState("saved");
      setError(null);
      refreshInsights();
    } catch (e) {
      capDirty.current = true;
      setSaveState("error");
      setError(msg(e));
      throw e;
    }
  }, [id, refreshInsights]);

  const flushSettings = useCallback(async () => {
    clearTimeout(setTimer.current);
    if (!setDirty.current || !latestSettings.current) return;
    setDirty.current = false;
    try {
      await patchProject(id, { settings: latestSettings.current });
      refreshInsights();
    } catch (e) {
      setDirty.current = true;
      setError(msg(e));
      throw e;
    }
  }, [id, refreshInsights]);

  function changeCaption(capId: string, patch: Partial<CaptionSegment>) {
    setCaptions((cs) => cs.map((c) => (c.id === capId ? { ...c, ...patch } : c)));
    capDirty.current = true;
    setSaveState("saving");
    clearTimeout(capTimer.current);
    capTimer.current = setTimeout(() => flushCaptions().catch(() => {}), 800);
  }

  async function runHighlightStrategy(strategy: RenderSettings["highlightStrategy"]) {
    try {
      await flushCaptions();
      const p = await applyHighlightStrategy(id, strategy);
      setCaptions(p.captions);
      setProject((cur) => (cur ? { ...cur, status: p.status } : cur));
      refreshInsights();
    } catch (e) {
      setError(msg(e));
    }
  }

  async function persistSfx(next: SfxEvent[]) {
    setSfxEvents(next.slice().sort((a, b) => a.startSec - b.startSec));
    try {
      const p = await saveSfx(id, next);
      setSfxEvents(p.sfxEvents);
    } catch (e) {
      setError(msg(e));
    }
  }

  async function doSuggestSfx() {
    setError(null);
    try {
      const p = await suggestSfx(id);
      setSfxEvents(p.sfxEvents);
      if (!settings?.sfxEnabled) changeSettings({ sfxEnabled: true });
    } catch (e) {
      setError(msg(e));
    }
  }

  const addSfx = (sfxId: string) =>
    persistSfx([...sfxEvents, { id: Math.random().toString(36).slice(2, 10), startSec: Math.round(currentSec * 100) / 100, sfxId }]);
  const previewSfx = (sfxId: string) => {
    const a = new Audio(sfxAudioUrl(sfxId));
    a.volume = Math.min(1, 10 ** ((settings?.sfxGainDb ?? -14) / 20));
    a.play().catch(() => {});
  };

  async function doHighlightHook() {
    try {
      await flushCaptions();
      const p = await highlightHook(id);
      setCaptions(p.captions);
      refreshInsights();
    } catch (e) {
      setError(msg(e));
    }
  }

  function changeSettings(patch: Partial<RenderSettings>) {
    if (!settings) return;
    const next = { ...settings, ...patch };
    setSettings(next);
    latestSettings.current = next;
    setDirty.current = true;
    clearTimeout(setTimer.current);
    setTimer.current = setTimeout(() => flushSettings().catch(() => {}), 600);
    if (patch.highlightStrategy !== undefined) runHighlightStrategy(patch.highlightStrategy);
  }

  async function changeStyle(style: StylePresetId) {
    if (!settings) return;
    const next = settingsForPreset(style, settings);
    setSettings(next);
    latestSettings.current = next;
    setProject((p) => (p ? { ...p, style } : p));
    try {
      await patchProject(id, { style, settings: next });
      setDirty.current = false;
      await runHighlightStrategy(next.highlightStrategy);
    } catch (e) {
      setError(msg(e));
    }
  }

  async function changeContentType(contentType: ContentTypeId) {
    setProject((p) => (p ? { ...p, contentType } : p));
    try { await patchProject(id, { contentType }); } catch (e) { setError(msg(e)); }
  }

  async function rename(name: string) {
    if (!project || !name.trim() || name === project.name) return;
    try { setProject(await patchProject(id, { name })); } catch (e) { setError(msg(e)); }
  }

  // ---------- ações ----------
  async function doExport() {
    setError(null);
    try {
      await flushCaptions();
      await flushSettings();
      setProject(await exportProject(id));
    } catch (e) {
      setError(msg(e));
    }
  }

  async function doAnalyze() {
    if (captions.length && !confirm("Refazer a transcrição substitui as legendas atuais, incluindo suas correções. Continuar?")) return;
    setError(null);
    try {
      await flushSettings();
      setProject(await analyzeProject(id));
    } catch (e) {
      setError(msg(e));
    }
  }

  async function onUploadLogo(file: File) {
    try {
      await uploadLogo(file);
      setLogoVersion(Date.now());
    } catch (e) {
      setError(msg(e));
    }
  }

  async function onRemoveLogo() {
    try {
      await removeLogo();
      setLogoVersion(null);
      changeSettings({ logoPosition: "none" });
    } catch (e) {
      setError(msg(e));
    }
  }

  const seek = useCallback((t: number) => {
    if (videoRef.current) videoRef.current.currentTime = t;
    setCurrentSec(t);
  }, []);

  function select(capId: string) {
    setSelectedId(capId);
    const c = captions.find((x) => x.id === capId);
    if (c) seek(c.startSec + 0.01);
  }

  // ---------- telas ----------
  if (error && !project) {
    return <p role="alert" className="rounded-gm border border-rose-200 bg-rose-50 p-6 text-rose-700">{error}</p>;
  }
  if (!project || !settings) return <p className="text-gm-muted">Carregando…</p>;

  const analyzing = project.status === "processing" && project.stage !== "render";
  const exporting = project.status === "processing" && project.stage === "render";
  const logoUrl = logoVersion ? urls.logo(logoVersion) : null;

  const nameField = (
    <input
      key={project.id}
      defaultValue={project.name}
      onBlur={(e) => rename(e.target.value)}
      aria-label="Nome do vídeo"
      className="mb-6 w-full rounded-lg border border-transparent bg-transparent px-1 text-xl font-semibold text-gm-purple hover:border-gm-line focus:border-gm-lilac focus:outline-none"
    />
  );

  const preview = (
    <VideoPreview
      project={project} settings={settings} captions={captions} showSafeZone={showSafeZone}
      zoomPlan={insights.zoomPlan} sfxEvents={sfxEvents} logoUrl={logoUrl} videoRef={videoRef} currentSec={currentSec} onTime={setCurrentSec}
    />
  );

  if (!project.analyzed) {
    const stepIndex = STEPS.findIndex((s) => s.stage === project.stage);
    return (
      <div>
      {nameField}
      <div className="grid gap-6 md:grid-cols-[300px_1fr]">
        {preview}
        <div className="rounded-gm border border-gm-line bg-white p-6">
          {analyzing ? (
            <>
              <h2 className="text-lg font-semibold text-gm-purple">Analisando seu vídeo…</h2>
              <p className="mt-1 text-sm text-gm-muted">Você pode ver o vídeo ao lado enquanto isso.</p>
              <ol className="mt-4 space-y-2 text-sm">
                {STEPS.map((s, i) => (
                  <li key={s.stage} className={i < stepIndex ? "text-emerald-700" : i === stepIndex ? "font-medium text-gm-purple" : "text-gm-muted"}>
                    {i < stepIndex ? "✓" : i === stepIndex ? "●" : "○"} {s.label}
                  </li>
                ))}
              </ol>
            </>
          ) : (
            <>
              <h2 className="text-lg font-semibold text-gm-purple">
                {project.status === "error" ? "Não foi possível analisar o vídeo" : "Vamos analisar o vídeo"}
              </h2>
              {project.status === "error" && project.errorMessage && <p role="alert" className="mt-2 text-sm text-rose-700">{project.errorMessage}</p>}
              {error && <p role="alert" className="mt-2 text-sm text-rose-700">{error}</p>}
              <Button className="mt-4" onClick={doAnalyze}>{project.status === "error" ? "Tentar novamente" : "Analisar vídeo"}</Button>
            </>
          )}
        </div>
      </div>
      </div>
    );
  }

  return (
    <div>
    {nameField}
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="min-w-0 space-y-6">
        <div className="grid gap-6 md:grid-cols-[300px_1fr]">
          {preview}
          <div className="min-w-0 space-y-2">
            <CaptionList captions={captions} selectedId={selectedId} onSelect={select} onChange={changeCaption} saveState={saveState} />
            <button type="button" onClick={doAnalyze} disabled={processing} className="text-xs text-gm-muted underline hover:text-gm-purple disabled:opacity-50">
              Refazer transcrição
            </button>
          </div>
        </div>
        <Timeline
          durationSec={project.durationSec} captions={captions} silences={project.silences} zoomPlan={insights.zoomPlan} sfxEvents={sfxEvents} settings={settings}
          selectedId={selectedId} currentSec={currentSec} onSelect={select} onSeek={seek}
        />
        <SfxCard
          enabled={settings.sfxEnabled} gainDb={settings.sfxGainDb} events={sfxEvents} sounds={sfxSounds} currentSec={currentSec}
          onToggle={(v) => changeSettings({ sfxEnabled: v })} onGain={(db) => changeSettings({ sfxGainDb: db })}
          onSuggest={doSuggestSfx} onAdd={addSfx} onPreview={previewSfx}
          onChangeSound={(evId, sfxId) => persistSfx(sfxEvents.map((e) => (e.id === evId ? { ...e, sfxId } : e)))}
          onRemove={(evId) => persistSfx(sfxEvents.filter((e) => e.id !== evId))}
        />
        {insights.hook && (
          <HookCard hook={insights.hook} trimStartSec={settings.trimStartSec} onTrimStart={(sec) => changeSettings({ trimStartSec: sec })} onHighlightHook={doHighlightHook} />
        )}
      </div>

      <div className="space-y-4">
        <SidePanel
          settings={settings} contentType={project.contentType} style={project.style} silences={project.silences}
          showSafeZone={showSafeZone} hasLogo={logoVersion !== null}
          onSettings={changeSettings} onContentType={changeContentType} onStyle={changeStyle}
          onToggleSafeZone={setShowSafeZone} onUploadLogo={onUploadLogo} onRemoveLogo={onRemoveLogo} onSeek={seek}
        />

        {error && <p role="alert" className="rounded-gm bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        {project.status === "error" && project.errorMessage && !error && (
          <p role="alert" className="rounded-gm bg-rose-50 p-3 text-sm text-rose-700">{project.errorMessage}</p>
        )}

        {exporting && (
          <div aria-live="polite">
            <div className="h-2 overflow-hidden rounded-full bg-gm-lilac-soft">
              <div className="h-full bg-gm-purple transition-all" style={{ width: `${project.progress}%` }} />
            </div>
            <p className="mt-2 text-center text-sm text-gm-muted">Exportando… {Math.round(project.progress)}%</p>
          </div>
        )}

        {project.status === "ready" && project.hasOutput && (
          <div className="rounded-gm border border-emerald-200 bg-emerald-50 p-4 text-center">
            <p className="mb-3 text-sm font-medium text-emerald-800">Vídeo pronto! 1080×1920 · MP4 (H.264)</p>
            <a href={urls.download(id)} className="inline-flex w-full items-center justify-center rounded-full bg-emerald-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-emerald-800">
              Baixar vídeo
            </a>
          </div>
        )}

        <Button className="w-full" onClick={doExport} disabled={processing}>
          {project.status === "ready" ? "Exportar novamente" : "Exportar vídeo"}
        </Button>
        {project.status === "draft" && project.hasOutput && (
          <p className="text-center text-xs text-gm-muted">Você mudou algo depois da última exportação. Exporte de novo para atualizar.</p>
        )}
        <p className="text-center text-xs text-gm-muted">Pronto para Instagram Reels, TikTok, TikTok Shop e YouTube Shorts.</p>
      </div>
    </div>
    </div>
  );
}
