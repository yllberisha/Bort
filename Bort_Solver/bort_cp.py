from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List

from ortools.sat.python import cp_model
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


BookID = int
LibID = int

def greedy_lib_order(D: int, libraries: Dict[LibID, dict]) -> List[LibID]:
    """Greedy function returning only library order for safer hinting"""
    remaining = D
    order: List[LibID] = []
    lib_density = {
        l: sum(libraries[l]["book_scores"].values()) / libraries[l]["signup"]
        for l in libraries
    }
    for l in sorted(lib_density, key=lib_density.get, reverse=True):
        s = libraries[l]["signup"]
        if s >= remaining:
            continue
        remaining -= s
        order.append(l)
    return order

# ---------------------------------------------------------------------------
# Pre‑processing
# ---------------------------------------------------------------------------

def preprocess(B, libraries, D, book_scores):
    """Enhanced preprocessing with cleaner memory usage"""
    libs = {}
    for l, d in libraries.items():
        if d["signup"] >= D:
            continue
        max_b = d["ship"] * (D - d["signup"])
        valid_books = [b for b in d["books"] if b in book_scores]
        books = sorted(valid_books, key=lambda b: book_scores[b], reverse=True)[:max_b]
        libs[l] = {
            **d,
            "books": books,
            "sorted_books": [(b, book_scores[b]) for b in books],  # Keep for compatibility
            "book_scores": {b: book_scores[b] for b in books},
        }
    return libs

# ---------------------------------------------------------------------------
# CP‑SAT model
# ---------------------------------------------------------------------------

def solve_cp_sat(B, L, D, book_scores, libraries, *, 
                 time_limit_s=300, workers=1, gap_limit=0.0, use_minimal_hint=True):
    model = cp_model.CpModel()

    y = {l: model.NewBoolVar(f"y[{l}]") for l in L}
    start = {l: model.NewIntVar(0, D - 1, f"s[{l}]") for l in L}
    interval = {
        l: model.NewOptionalIntervalVar(start[l], libraries[l]["signup"], start[l] + libraries[l]["signup"], y[l], f"int[{l}]")
        for l in L
    }
    z = {}
    for l in L:
        for b in libraries[l]["books"]:
            z[(l, b)] = model.NewBoolVar(f"z[{l},{b}]")
            model.Add(z[(l, b)] <= y[l])

    model.AddNoOverlap(interval.values())

    for b in B:
        zlist = [z[(l, b)] for l in L if (l, b) in z]
        if zlist:
            model.Add(sum(zlist) <= 1)

    for l in L:
        max_days = D - libraries[l]["signup"] - start[l]
        cap = libraries[l]["ship"]
        big_m = len(libraries[l]["books"])
        model.Add(sum(z[(l, b)] for b in libraries[l]["books"]) <= cap * max_days + big_m * (1 - y[l]))

    model.Maximize(sum(book_scores[b] * z[(l, b)] for (l, b) in z))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = workers
    solver.parameters.relative_gap_limit = gap_limit
    solver.parameters.log_search_progress = True

    class Prog(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__(); self.t0 = time.time()
        def OnSolutionCallback(self):
            best = self.ObjectiveValue(); bound = self.BestObjectiveBound()
            gap = 100 * (best - bound) / max(1, best)
            print(f"inc {best:,.0f}  gap {gap:4.1f}%  t {time.time()-self.t0:5.1f}s")
    cb = Prog()

    # warm‑start 
    if use_minimal_hint:
        # Minimal hints - safer for large instances
        try:
            hint_vars, hint_vals = [], []
            acc = 0
            for l in greedy_lib_order(D, libraries):
                hint_vars.extend([y[l], start[l]])
                hint_vals.extend([1, acc])
                acc += libraries[l]["signup"]
            model.AddHint(hint_vars, hint_vals)
            print(f"✔  Minimal AddHint injected for {len(hint_vars)} vars")
        except Exception as e:
            print("⚠  Minimal AddHint failed – continuing without warm‑start:", e)

    status = solver.SolveWithSolutionCallback(model, cb)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"Solver failed: {solver.StatusName(status)}")

    # Extract solution with proper ordering
    selected = [l for l in L if solver.BooleanValue(y[l])]
    selected.sort(key=lambda l: solver.Value(start[l]))  # Sort by start time
    books_out = {l: [] for l in selected}
    used = set()
    for l in selected:
        for b in libraries[l]["books"]:
            if (l, b) in z and solver.BooleanValue(z[(l, b)]) and b not in used:
                books_out[l].append(b)
                used.add(b)
    
    # Filter out libraries with no books (they waste signup time)
    selected_with_books = [l for l in selected if books_out[l]]
    books_out = {l: books_out[l] for l in selected_with_books}
    
    return solver.ObjectiveValue(), selected_with_books, books_out

# ---------------------------------------------------------------------------
# Output builder (Hash Code format)
# ---------------------------------------------------------------------------

def build_output(order, books):
    """Build output in Hash Code format"""
    lines = [str(len(order))]
    for l in order:
        bl = books[l]
        lines.append(f"{l} {len(bl)}")
        lines.append(" ".join(map(str, bl)))
    return "\n".join(lines)
