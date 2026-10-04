import Link from "next/link";
import { Header } from "@/components/Header";
import { EditorWorkspace } from "@/components/editor/EditorWorkspace";
import { getProject } from "@/lib/api";
import { CONTENT_TYPES } from "@/lib/content-types";
import { STYLE_PRESETS } from "@/lib/presets";

export default async function EditorPage(props: PageProps<"/editor/[id]">) {
  const { id } = await props.params;
  const query = await props.searchParams;
  const project = await getProject(id);

  // Aceita tipo/estilo vindos da tela "Novo vídeo"; valores inválidos são ignorados.
  const tipo = CONTENT_TYPES.find((t) => t.id === query.tipo)?.id ?? project.contentType;
  const estilo = STYLE_PRESETS.find((s) => s.id === query.estilo)?.id ?? project.style;

  return (
    <>
      <Header>
        <Link href="/" className="text-sm text-gm-muted hover:text-gm-purple">← Projetos</Link>
      </Header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">
        <h1 className="mb-6 text-xl font-semibold text-gm-purple">{project.name}</h1>
        <EditorWorkspace initial={{ contentType: tipo, style: estilo }} />
      </main>
    </>
  );
}
