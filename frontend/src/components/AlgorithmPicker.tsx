import { Check } from "lucide-react";
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
              "relative rounded-xl border-2 px-3 py-2 text-left transition outline-none focus-visible:ring-4 focus-visible:ring-cobalt/25",
              selected ? "border-cobalt bg-cobalt-soft" : "border-line bg-surface hover:border-faint",
            )}
          >
            <span className="block text-sm font-bold">{a.name}</span>
            <span className={cn("block text-xs", selected ? "text-link" : "text-muted")}>{a.tagline}</span>
            {selected && (
              <span className="absolute top-2 right-2 flex size-4 items-center justify-center rounded-full bg-cobalt text-on-cobalt">
                <Check className="size-2.5" strokeWidth={4} aria-hidden />
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
