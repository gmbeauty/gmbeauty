import Link from "next/link";

export function Header({ children }: { children?: React.ReactNode }) {
  return (
    <header className="sticky top-0 z-20 border-b border-gm-line bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-full bg-gm-purple text-sm font-semibold text-white">
            GM
          </span>
          <span className="text-lg font-semibold tracking-tight text-gm-purple">GM Beauty</span>
        </Link>
        <div className="flex items-center gap-3">
          <Link href="/biblioteca" className="text-sm text-gm-muted hover:text-gm-purple">Biblioteca</Link>
          {children}
        </div>
      </div>
    </header>
  );
}
