"""Command line interface: ``python -m matching <command>``.

Commands
  evaluate      run the benchmarks and write docs/BENCHMARKS.md
  data-report   write the data quality report to docs/DATA.md
  label-sheet   write eval/to_label.csv for human relevance labelling
  export-tree   dump both cluster trees as JSON (for inspection)
  search        one-off search from the command line
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m matching")
    sub = p.add_subparsers(dest="cmd", required=True)

    ev = sub.add_parser("evaluate")
    ev.add_argument("--quick", action="store_true")
    ev.add_argument("--out", default=str(ROOT / "docs" / "BENCHMARKS.md"))
    ev.add_argument("--labels", default=str(ROOT / "eval" / "labels.csv"))

    dr = sub.add_parser("data-report")
    dr.add_argument("--out", default=str(ROOT / "docs" / "DATA.md"))

    ls = sub.add_parser("label-sheet")
    ls.add_argument("--out", default=str(ROOT / "eval" / "to_label.csv"))
    ls.add_argument("--queries", type=int, default=25)

    ex = sub.add_parser("export-tree")
    ex.add_argument("--out", default=str(ROOT / "build"))

    se = sub.add_parser("search")
    se.add_argument("direction", choices=["seeker_to_job", "job_to_seeker"])
    se.add_argument("--algorithm", default="astar")
    se.add_argument("--k", type=int, default=5)
    se.add_argument("--skills", default="")
    se.add_argument("--sector")
    se.add_argument("--contract")
    se.add_argument("--education")
    se.add_argument("--city")
    se.add_argument("--years", type=float)
    se.add_argument("--exp-min", type=float)
    se.add_argument("--exp-max", type=float)
    se.add_argument("--salary", type=float)

    args = p.parse_args(argv)

    if args.cmd == "data-report":
        from .data import data_quality_report
        text = data_quality_report()
        _write(args.out, text)
        return

    from .engine import Matcher
    m = Matcher()

    if args.cmd == "evaluate":
        from .evaluation import run_all
        _write(args.out, run_all(m, quick=args.quick, labels_path=args.labels))
    elif args.cmd == "label-sheet":
        from .evaluation import make_labeling_sheet
        n = make_labeling_sheet(m, args.out, n_queries=args.queries)
        print(f"Wrote {n} pairs to {args.out}; fill in the 'relevance' column (0-3) and save as eval/labels.csv")
    elif args.cmd == "export-tree":
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for direction, tree in m.trees.items():
            path = out / f"{tree.entity}_tree.json"
            path.write_text(json.dumps(tree.to_dict(), indent=1), encoding="utf-8")
            print(f"Wrote {path} ({tree.n_nodes} nodes)")
    elif args.cmd == "search":
        q = m.make_query(args.direction, sector=args.sector, contract_type=args.contract,
                         education=args.education, city=args.city, years=args.years,
                         exp_lo=args.exp_min, exp_hi=args.exp_max, salary=args.salary,
                         skills=[s for s in args.skills.split(",") if s.strip()])
        r = m.search(q, args.algorithm, k=args.k)
        print(json.dumps({"stats": r.stats.as_dict(), "matches": r.hits}, indent=2, ensure_ascii=False))


def _write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    sys.exit(main())
