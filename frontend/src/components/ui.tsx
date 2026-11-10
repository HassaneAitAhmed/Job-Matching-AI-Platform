import { ChevronDown, Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

export const cn = (...classes: (string | false | null | undefined)[]) => classes.filter(Boolean).join(" ");

const control =
  "w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-ink outline-none transition " +
  "placeholder:text-faint hover:border-faint focus:border-accent focus:ring-3 focus:ring-accent/15";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md";
  loading?: boolean;
};

export function Button({ variant = "primary", size = "md", loading, className, children, disabled, ...rest }: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition outline-none",
        "focus-visible:ring-3 focus-visible:ring-accent/30 disabled:cursor-not-allowed disabled:opacity-60",
        size === "md" ? "h-10 px-4 text-sm" : "h-8 px-3 text-xs",
        variant === "primary" && "bg-ink text-paper hover:bg-accent hover:text-surface",
        variant === "secondary" && "border border-line bg-surface text-ink hover:border-ink",
        variant === "ghost" && "text-muted hover:bg-sunken hover:text-ink",
        className,
      )}
    >
      {loading && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn("rounded-lg border border-line bg-surface", className)}>{children}</div>;
}

/** Small monospaced uppercase label, used for field labels and captions. */
export function Label({ children, className, htmlFor }: { children: ReactNode; className?: string; htmlFor?: string }) {
  return (
    <label htmlFor={htmlFor} className={cn("font-mono text-[11px] tracking-[0.08em] text-muted uppercase", className)}>
      {children}
    </label>
  );
}

export function Field({
  label,
  hint,
  htmlFor,
  children,
  className,
}: {
  label: string;
  hint?: ReactNode;
  htmlFor?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {hint && <p className="text-xs text-faint">{hint}</p>}
    </div>
  );
}

export function Input({ suffix, className, ...rest }: InputHTMLAttributes<HTMLInputElement> & { suffix?: string }) {
  return (
    <div className="relative">
      <input {...rest} className={cn(control, "tabular-nums", suffix && "pr-12", className)} />
      {suffix && (
        <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center font-mono text-[11px] text-faint">
          {suffix}
        </span>
      )}
    </div>
  );
}

export function Select({ className, children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="relative">
      <select {...rest} className={cn(control, "appearance-none truncate pr-9", className)}>
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-faint" aria-hidden />
    </div>
  );
}

export function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: "neutral" | "accent" | "ochre" | "signal";
  children: ReactNode;
  className?: string;
}) {
  const tones = {
    neutral: "border border-line text-muted",
    accent: "bg-accent-soft text-accent",
    ochre: "bg-ochre-soft text-ochre",
    signal: "bg-signal-soft text-signal",
  };
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium", tones[tone], className)}>
      {children}
    </span>
  );
}

/** Page heading: numbered mono eyebrow, serif title (use <em> for the accent word), lead paragraph. */
export function SectionTitle({
  index,
  eyebrow,
  title,
  children,
}: {
  index: string;
  eyebrow: string;
  title: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className="max-w-3xl">
      <p className="font-mono text-xs tracking-[0.08em] text-muted uppercase">
        <span className="text-accent">{index}</span>
        <span className="mx-2 text-faint">/</span>
        {eyebrow}
      </p>
      <h1 className="mt-4 font-display text-[2.75rem] leading-[1.02] font-[420] tracking-[-0.02em] text-balance sm:text-6xl [&_em]:text-accent [&_em]:italic">
        {title}
      </h1>
      {children && <p className="mt-5 max-w-2xl text-[17px] leading-relaxed text-pretty text-muted">{children}</p>}
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-md border border-signal/30 bg-signal-soft px-4 py-3 text-sm text-signal">
      {message}
    </div>
  );
}
