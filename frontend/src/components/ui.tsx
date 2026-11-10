import { ChevronDown, Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

export const cn = (...classes: (string | false | null | undefined)[]) => classes.filter(Boolean).join(" ");

const control =
  "w-full rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink outline-none transition " +
  "placeholder:text-faint hover:border-faint focus:border-cobalt focus:ring-4 focus:ring-cobalt/15";

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
        "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition outline-none",
        "focus-visible:ring-4 focus-visible:ring-cobalt/30 disabled:cursor-not-allowed disabled:opacity-60",
        size === "md" ? "h-11 px-5 text-sm" : "h-9 px-3.5 text-xs",
        variant === "primary" && "bg-cobalt text-on-cobalt hover:bg-cobalt-deep active:translate-y-px",
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
  return (
    <div className={cn("rounded-2xl border border-line bg-surface shadow-[0_1px_2px_rgb(11_16_32/0.04)]", className)}>
      {children}
    </div>
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
      <label htmlFor={htmlFor} className="text-[13px] font-semibold">
        {label}
      </label>
      {children}
      {hint && <p className="text-xs text-faint">{hint}</p>}
    </div>
  );
}

export function Input({ suffix, className, ...rest }: InputHTMLAttributes<HTMLInputElement> & { suffix?: string }) {
  return (
    <div className="relative">
      <input {...rest} className={cn(control, "", suffix && "pr-12", className)} />
      {suffix && (
        <span className="pointer-events-none absolute inset-y-0 right-3.5 flex items-center text-xs font-semibold text-faint">
          {suffix}
        </span>
      )}
    </div>
  );
}

export function Select({ className, children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="relative">
      <select {...rest} className={cn(control, "appearance-none truncate pr-10", className)}>
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute top-1/2 right-3.5 size-4 -translate-y-1/2 text-faint" aria-hidden />
    </div>
  );
}

export function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: "neutral" | "lime" | "cobalt" | "amber" | "coral";
  children: ReactNode;
  className?: string;
}) {
  const tones = {
    neutral: "bg-sunken text-muted",
    lime: "bg-lime text-lime-ink",
    cobalt: "bg-cobalt-soft text-link",
    amber: "bg-amber-soft text-amber",
    coral: "bg-coral-soft text-coral",
  };
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold", tones[tone], className)}>
      {children}
    </span>
  );
}

/**
 * Page shell: a full-width cobalt band with the title, and the page body pulled up over its edge.
 * The first element of `children` should be a card, since it overlaps the band.
 */
export function Page({
  eyebrow,
  title,
  lead,
  children,
}: {
  eyebrow: string;
  title: ReactNode;
  lead?: ReactNode;
  children: ReactNode;
}) {
  return (
    <>
      <section className="bg-band text-on-cobalt">
        <div className="mx-auto max-w-6xl px-4 pt-10 pb-28 sm:px-6 lg:pt-16 lg:pb-32">
          <span className="inline-flex rounded-full bg-white/12 px-3 py-1 text-xs font-semibold text-white/90 ring-1 ring-white/15">
            {eyebrow}
          </span>
          <h1 className="mt-5 max-w-3xl text-[2.6rem] leading-[1.02] font-[800] tracking-[-0.035em] text-balance sm:text-[4rem] [&_mark]:bg-transparent [&_mark]:text-lime">
            {title}
          </h1>
          {lead && <p className="mt-5 max-w-2xl text-[17px] leading-relaxed text-pretty text-white/75">{lead}</p>}
        </div>
      </section>
      <div className="mx-auto -mt-20 max-w-6xl px-4 pb-20 sm:px-6">{children}</div>
    </>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-2xl border border-coral/30 bg-coral-soft px-4 py-3 text-sm font-medium text-coral">
      {message}
    </div>
  );
}
