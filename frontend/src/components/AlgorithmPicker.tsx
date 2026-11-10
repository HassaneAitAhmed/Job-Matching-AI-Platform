import type { Algorithm } from "../lib/api";
import { ALGORITHMS } from "../lib/format";
import { cn } from "./ui";

export function AlgorithmPicker({ value, onChange }: { value: Algorithm; onChange: (a: Algorithm) => void }) {
  return (
    <div role="radiogroup" aria-label="Algorithm" className="grid grid-cols-2 gap-2">
      {(Object.keys(ALGORITHMS) as Algorithm[]).map((key) => {
        const a = ALGORITHMS[key];
        const selected = key === value;
        return (
          <button
            key={key}
            type="button"
            role="radio"
            aria-checked={selected}
            title={a.description}
            onClick={() => onChange(key)}
            className={cn(
              "relative rounded-md border px-3 py-2 text-left transition outline-none focus-visible:ring-3 focus-visible:ring-accent/25",
              selected ? "border-ink bg-sunken/70" : "border-line bg-surface hover:border-faint",
            )}
          >
            <span className="block text-sm font-medium">{a.name}</span>
            <span className="block font-mono text-[10.5px] text-muted">{a.tagline}</span>
            {selected && <span className="absolute top-2.5 right-2.5 size-1.5 rounded-full bg-accent" aria-hidden />}
          </button>
        );
      })}
    </div>
  );
}
