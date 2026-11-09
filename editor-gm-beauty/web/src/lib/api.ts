// Único ponto de comunicação com o backend (FastAPI).
import type { CaptionSegment, HighlightStrategy, Insights, Project, RenderSettings, SfxCategory, SfxEvent, SfxSound, BrollClip, BrollEvent } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const urls = {
  video: (id: string) => `${API_URL}/projects/${id}/video`,
  thumbnail: (id: string, v?: string) => `${API_URL}/projects/${id}/thumbnail${v ? `?v=${encodeURIComponent(v)}` : ""}`,
  download: (id: string) => `${API_URL}/projects/${id}/download`,
  logo: (v?: number) => `${API_URL}/logo${v ? `?v=${v}` : ""}`,
};

/** Erro com mensagem já pronta para mostrar à pessoa (sem termos técnicos). */
export class FriendlyError extends Error {}

const OFFLINE = "Não conseguimos conectar ao servidor do editor. Verifique se ele está ligado e tente novamente.";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { cache: "no-store", ...init });
  } catch {
    throw new FriendlyError(OFFLINE);
  }
  if (!res.ok) {
    let msg = "Algo deu errado. Tente novamente.";
    try {
      const body = await res.json();
      if (typeof body.detail === "string") msg = body.detail;
    } catch {
      /* mantém a mensagem padrão */
    }
    throw new FriendlyError(msg);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

const json = (method: string, body?: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: body === undefined ? undefined : JSON.stringify(body),
});

export const listProjects = () => request<Project[]>("/projects");
export const getProject = (id: string) => request<Project>(`/projects/${id}`);
export const deleteProject = (id: string) => request<void>(`/projects/${id}`, { method: "DELETE" });
export const duplicateProject = (id: string) => request<Project>(`/projects/${id}/duplicate`, { method: "POST" });
export const analyzeProject = (id: string) => request<Project>(`/projects/${id}/analyze`, { method: "POST" });
export const exportProject = (id: string) => request<Project>(`/projects/${id}/export`, { method: "POST" });

export const patchProject = (id: string, patch: Partial<Pick<Project, "name" | "contentType" | "style" | "settings">>) =>
  request<Project>(`/projects/${id}`, json("PATCH", patch));

export const saveCaptions = (id: string, captions: CaptionSegment[]) =>
  request<Project>(`/projects/${id}/captions`, json("PUT", { captions }));

export const applyHighlightStrategy = (id: string, strategy: HighlightStrategy) =>
  request<Project>(`/projects/${id}/highlights`, json("POST", { strategy }));

export const getInsights = (id: string) => request<Insights>(`/projects/${id}/insights`);
export const highlightHook = (id: string) => request<Project>(`/projects/${id}/hook/highlight`, { method: "POST" });

export const listSfx = () => request<SfxSound[]>("/library/sfx");
export const deleteSfx = (id: string) => request<void>(`/library/sfx/${id}`, { method: "DELETE" });
export const sfxAudioUrl = (id: string) => `${API_URL}/library/sfx/${id}/audio`;
export const suggestSfx = (projectId: string) => request<Project>(`/projects/${projectId}/sfx/suggest`, { method: "POST" });
export const saveSfx = (projectId: string, events: SfxEvent[]) => request<Project>(`/projects/${projectId}/sfx`, json("PUT", { events }));

export async function uploadSfx(file: File, name: string, category: SfxCategory): Promise<SfxSound> {
  const form = new FormData();
  form.append("file", file);
  form.append("name", name);
  form.append("category", category);
  return request<SfxSound>("/library/sfx", { method: "POST", body: form });
}

export const listBroll = () => request<BrollClip[]>("/library/broll");
export const deleteBroll = (id: string) => request<void>(`/library/broll/${id}`, { method: "DELETE" });
export const patchBroll = (id: string, patch: Partial<Pick<BrollClip, "name" | "tag">>) =>
  request<BrollClip>(`/library/broll/${id}`, json("PATCH", patch));
export const brollVideoUrl = (id: string) => `${API_URL}/library/broll/${id}/video`;
export const brollThumbUrl = (id: string) => `${API_URL}/library/broll/${id}/thumbnail`;
export const suggestBroll = (projectId: string) => request<Project>(`/projects/${projectId}/broll/suggest`, { method: "POST" });
export const saveBroll = (projectId: string, events: BrollEvent[]) => request<Project>(`/projects/${projectId}/broll`, json("PUT", { events }));

export async function uploadBroll(file: File, name: string, tag: string): Promise<BrollClip> {
  const form = new FormData();
  form.append("file", file);
  form.append("name", name);
  form.append("tag", tag);
  return request<BrollClip>("/library/broll", { method: "POST", body: form });
}

export async function hasLogo(): Promise<boolean> {
  try {
    return (await request<{ exists: boolean }>("/logo/status")).exists;
  } catch {
    return false;
  }
}

export async function uploadLogo(file: File): Promise<void> {
  const form = new FormData();
  form.append("file", file);
  await request("/logo", { method: "POST", body: form });
}

export const removeLogo = () => request<void>("/logo", { method: "DELETE" });

/** Envia o vídeo com barra de progresso. */
export function createProject(
  file: File,
  data: { contentType: string; style: string; settings: RenderSettings },
  onProgress: (pct: number) => void,
): Promise<Project> {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    form.append("file", file);
    form.append("contentType", data.contentType);
    form.append("style", data.style);
    form.append("settings", JSON.stringify(data.settings));
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_URL}/projects`);
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress((e.loaded / e.total) * 100);
    xhr.onerror = () => reject(new FriendlyError(OFFLINE));
    xhr.onload = () => {
      try {
        const body = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) return resolve(body as Project);
        reject(new FriendlyError(typeof body.detail === "string" ? body.detail : "Não conseguimos enviar este vídeo. Tente novamente."));
      } catch {
        reject(new FriendlyError("Não conseguimos enviar este vídeo. Tente novamente."));
      }
    };
    xhr.send(form);
  });
}
