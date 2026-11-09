import Link from "next/link";
import { Header } from "@/components/Header";
import { EditorWorkspace } from "@/components/editor/EditorWorkspace";

export default async function EditorPage(props: PageProps<"/editor/[id]">) {
  const { id } = await props.params;
  return (
    <>
      <Header>
        <Link href="/" className="text-sm text-gm-muted hover:text-gm-purple">← Projetos</Link>
      </Header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">
        <EditorWorkspace id={id} />
      </main>
    </>
  );
}
