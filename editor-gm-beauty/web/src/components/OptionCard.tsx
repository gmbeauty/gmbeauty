export function OptionCard({
  selected,
  title,
  description,
  onClick,
}: {
  selected: boolean;
  title: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`rounded-gm border p-4 text-left transition ${
        selected ? "border-gm-lilac bg-gm-lilac-soft ring-2 ring-gm-lilac" : "border-gm-line bg-white hover:border-gm-lilac-mid"
      }`}
    >
      <div className="font-medium text-gm-purple">{title}</div>
      <div className="mt-1 text-sm text-gm-muted">{description}</div>
    </button>
  );
}
