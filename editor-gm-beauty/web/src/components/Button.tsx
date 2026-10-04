import Link from "next/link";

const base =
  "inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-gm-lilac disabled:cursor-not-allowed disabled:opacity-50";
const variants = {
  primary: "bg-gm-purple text-white hover:bg-[#3a1559]",
  soft: "bg-gm-lilac-soft text-gm-purple hover:bg-gm-lilac-mid",
  ghost: "text-gm-muted hover:bg-gm-lilac-soft hover:text-gm-purple",
} as const;

type Variant = keyof typeof variants;

export function Button({
  variant = "primary",
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button className={`${base} ${variants[variant]} ${className}`} {...props} />;
}

export function ButtonLink({
  variant = "primary",
  className = "",
  ...props
}: React.ComponentProps<typeof Link> & { variant?: Variant }) {
  return <Link className={`${base} ${variants[variant]} ${className}`} {...props} />;
}
