import time
from collections import defaultdict
from typing import Dict, List

from ortools.sat.python import cp_model


BookID = int
LibID = int

# ---------------------------------------------------------------------------
# Greedy warm‑start
# ---------------------------------------------------------------------------

def greedy_schedule(D: int, libraries: Dict[LibID, dict]):
    remaining = D
    order: List[LibID] = []
    books_out: Dict[LibID, List[BookID]] = defaultdict(list)
    lib_score = {
        l: sum(libraries[l]["book_scores"].values()) / libraries[l]["signup"]
        for l in libraries
    }
    for l in sorted(lib_score, key=lib_score.get, reverse=True):
        s = libraries[l]["signup"]
        if s >= remaining:
            continue
        remaining -= s
        order.append(l)
        cap = libraries[l]["ship"] * remaining
        books_out[l] = [b for b, _ in libraries[l]["sorted_books"][:cap]]
        used = set().union(*(set(books_out[x]) for x in order[:-1]))
        books_out[l] = [b for b in books_out[l] if b not in used]
    return order, books_out

# ---------------------------------------------------------------------------
# Pre‑processing
# ---------------------------------------------------------------------------

def preprocess(B, libraries, D, book_scores):
    libs = {}
    for l, d in libraries.items():
        if d["signup"] >= D:
            continue
        max_b = d["ship"] * (D - d["signup"])
        books = sorted(d["books"], key=lambda b: book_scores[b], reverse=True)[:max_b]
        libs[l] = {
            **d,
            "books": books,
            "sorted_books": [(b, book_scores[b]) for b in books],
            "book_scores": {b: book_scores[b] for b in books},
        }
    return libs

# ---------------------------------------------------------------------------
# CP‑SAT model
# ---------------------------------------------------------------------------

def solve_cp_sat(B, L, D, book_scores, libraries, *, time_limit_s=300, workers=1):
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
    solver.parameters.relative_gap_limit = 0.02
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
    g_order, g_books = greedy_schedule(D, libraries)
    acc = 0
    for l in g_order:
        model.AddHint(y[l], 1)               # Add library selection hint
        model.AddHint(start[l], acc)         # Add start time hint
        acc += libraries[l]["signup"]        # Accumulate signup times
        for b in g_books[l]:                 # For each book in the greedy solution
            if (l, b) in z:                  # If the book is part of the library's books
                model.AddHint(z[(l, b)], 1)  # Add book assignment hint

    status = solver.SolveWithSolutionCallback(model, cb)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(solver.StatusName(status))

    selected = [l for l in g_order if solver.BooleanValue(y[l])]
    books_out = {l: [] for l in selected}
    used = set()
    for l in selected:
        for b in libraries[l]["books"]:
            if (l, b) in z and solver.BooleanValue(z[(l, b)]) and b not in used:
                books_out[l].append(b); used.add(b)
    return solver.ObjectiveValue(), selected, books_out

# ---------------------------------------------------------------------------
# Output builder compatible with HC format
# ---------------------------------------------------------------------------

def build_output(order, books):
    lines = [str(len(order))]
    for l in order:
        bl = books[l]
        lines.append(f"{l} {len(bl)}")
        lines.append(" ".join(map(str, bl)))
    return "\n".join(lines)
