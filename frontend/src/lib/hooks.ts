import { useCallback, useEffect, useState } from "react";

export type Route = "jobs" | "talent" | "batch" | "how";
const ROUTES: Route[] = ["jobs", "talent", "batch", "how"];

function readRoute(): Route {
  const r = window.location.hash.replace(/^#\/?/, "") as Route;
  return ROUTES.includes(r) ? r : "jobs";
}

/** Tiny hash router: #/jobs, #/talent, #/batch, #/how. */
export function useRoute(): [Route, (r: Route) => void] {
  const [route, setRoute] = useState<Route>(readRoute);
  useEffect(() => {
    const onChange = () => setRoute(readRoute());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  const navigate = useCallback((r: Route) => {
    window.location.hash = `/${r}`;
    window.scrollTo({ top: 0 });
  }, []);
  return [route, navigate];
}

export function useTheme(): [boolean, () => void] {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  const toggle = useCallback(() => {
    setDark((d) => {
      const next = !d;
      document.documentElement.classList.toggle("dark", next);
      try {
        localStorage.setItem("theme", next ? "dark" : "light");
      } catch {
        // storage unavailable (private mode); the choice just isn't remembered
      }
      return next;
    });
  }, []);
  return [dark, toggle];
}
