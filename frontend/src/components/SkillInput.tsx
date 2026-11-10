import { X } from "lucide-react";
import { useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { cn } from "./ui";

interface Props {
  id?: string;
  value: string[];
  onChange: (skills: string[]) => void;
  suggestions: string[];
  placeholder?: string;
}

/** Tag input with type-ahead suggestions from the skill vocabulary. */
export function SkillInput({ id, value, onChange, suggestions, placeholder }: Props) {
  const [text, setText] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();

  const chosen = useMemo(() => new Set(value.map((v) => v.toLowerCase())), [value]);
  const matches = useMemo(() => {
    const q = text.trim().toLowerCase();
    if (!q) return [];
    const starts: string[] = [];
    const contains: string[] = [];
    for (const s of suggestions) {
      const l = s.toLowerCase();
      if (chosen.has(l)) continue;
      if (l.startsWith(q)) starts.push(s);
      else if (l.includes(q)) contains.push(s);
      if (starts.length >= 8) break;
    }
    return [...starts, ...contains].slice(0, 8);
  }, [text, suggestions, chosen]);

  const add = (skill: string) => {
    const s = skill.trim().replace(/\s+/g, " ");
    if (s && !chosen.has(s.toLowerCase())) onChange([...value, s]);
    setText("");
    setActive(0);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      if (text.trim()) {
        e.preventDefault();
        add(open && matches[active] ? matches[active] : text);
      }
    } else if (e.key === "Backspace" && !text && value.length) {
      onChange(value.slice(0, -1));
    } else if (e.key === "ArrowDown" && matches.length) {
      e.preventDefault();
      setOpen(true);
      setActive((a) => (a + 1) % matches.length);
    } else if (e.key === "ArrowUp" && matches.length) {
      e.preventDefault();
      setActive((a) => (a - 1 + matches.length) % matches.length);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const showList = open && matches.length > 0;

  return (
    <div className="relative">
      <div
        onClick={() => inputRef.current?.focus()}
        className={cn(
          "flex min-h-10 w-full cursor-text flex-wrap items-center gap-1.5 rounded-md border border-line bg-surface px-2 py-1.5 transition",
          "hover:border-faint focus-within:border-accent focus-within:ring-3 focus-within:ring-accent/15",
        )}
      >
        {value.map((skill) => (
          <span
            key={skill}
            className="inline-flex items-center gap-1 rounded-full bg-accent-soft py-0.5 pr-1 pl-2.5 text-xs font-medium text-accent"
          >
            {skill}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onChange(value.filter((v) => v !== skill));
              }}
              className="rounded-full p-0.5 hover:bg-accent/15"
              aria-label={`Remove ${skill}`}
            >
              <X className="size-3" />
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          id={id}
          value={text}
          onChange={(e) => {
            const v = e.target.value;
            if (v.includes(",")) {
              v.split(",").slice(0, -1).forEach(add);
              setText(v.split(",").pop() ?? "");
            } else {
              setText(v);
            }
            setOpen(true);
            setActive(0);
          }}
          onKeyDown={onKeyDown}
          onFocus={() => setOpen(true)}
          onBlur={() => {
            setOpen(false);
            if (text.trim()) add(text);
          }}
          placeholder={value.length ? "" : placeholder}
          className="min-w-24 flex-1 bg-transparent px-1 py-0.5 text-sm outline-none placeholder:text-faint"
          role="combobox"
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          autoComplete="off"
        />
      </div>
      {showList && (
        <ul
          id={listId}
          role="listbox"
          className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-md border border-line bg-surface p-1 shadow-[0_12px_32px_-12px_rgb(0_0_0/0.25)]"
        >
          {matches.map((m, i) => (
            <li
              key={m}
              role="option"
              aria-selected={i === active}
              onMouseDown={(e) => {
                e.preventDefault();
                add(m);
              }}
              onMouseEnter={() => setActive(i)}
              className={cn(
                "cursor-pointer rounded px-2.5 py-1.5 text-sm",
                i === active ? "bg-accent-soft text-accent" : "text-ink",
              )}
            >
              {m}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
