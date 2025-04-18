#Simplified Solver for Debugging

from ortools.linear_solver import pywraplp
from utils import get_solution_output, read_input_file, save_solution_file

def solve_book_scanning(B, L, D, book_scores, libraries, time_limit_ms=300000):
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        return None, None

    # Decision Variables
    y = {l: solver.IntVar(0, 1, f'y[{l}]') for l in L}  # Library signup
    z = {(l, b): solver.IntVar(0, 1, f'z[{l},{b}]') 
         for l in L for b in libraries[l]['books'] if b in book_scores}  # Book scans
    u = {b: solver.IntVar(0, 1, f'u[{b}]') for b in book_scores}  # Book scored
    p = {(l1, l2): solver.IntVar(0, 1, f'p[{l1},{l2}]') 
         for l1 in L for l2 in L if l1 != l2}  # Library order
    t = {l: solver.IntVar(0, D-1, f't[{l}]') for l in L}  # Signup start time

    # Objective: Maximize total score
    objective = solver.Objective()
    for b in book_scores:
        objective.SetCoefficient(u[b], book_scores[b])
    objective.SetMaximization()

    # Constraints
    # (2) Each book scanned at most once
    for b in book_scores:
        solver.Add(solver.Sum(z[l, b] for l in L 
                    if (l, b) in z) <= 1, f"book_once_{b}")

    # (3) u[b] = 1 if scanned from any library
    for l in L:
        for b in libraries[l]['books']:
            if (l, b) in z:
                solver.Add(u[b] >= z[l, b], f"link_u_{l}_{b}")

    # (4) Can't scan from unselected library
    for l in L:
        for b in libraries[l]['books']:
            if (l, b) in z:
                solver.Add(z[l, b] <= y[l], f"scan_if_selected_{l}_{b}")

    # (5) Library order exclusivity
    for l1 in L:
        for l2 in L:
            if l1 < l2:
                solver.Add(p[l1, l2] + p[l2, l1] <= 1, f"order_excl_{l1}_{l2}")

    # (6) Timing constraints
    for l1 in L:
        for l2 in L:
            if l1 != l2:
                solver.Add(t[l2] >= t[l1] + libraries[l1]['signup'] * y[l1] 
                           - D * (1 - p[l1, l2]), f"timing_{l1}_{l2}")

    # (7) Order enforcement if both selected
    for l1 in L:
        for l2 in L:
            if l1 < l2:
                solver.Add(p[l1, l2] + p[l2, l1] >= y[l1] + y[l2] - 1, 
                           f"order_both_{l1}_{l2}")

    # (8) Signup completes within time
    for l in L:
        solver.Add(t[l] + libraries[l]['signup'] * y[l] <= D, f"signup_time_{l}")
    
    
    # for l in L:
    #     solver.Add(t[l] <= D * y[l], f"start_time_bound_{l}")

    # (9) Capacity constraint (linearized)
    for l in L:
        M = len(libraries[l]['books'])
        capacity = libraries[l]['ship'] * (D - t[l] - libraries[l]['signup'])
        solver.Add(solver.Sum(z[l, b] for b in libraries[l]['books'] 
                    if (l, b) in z) <= capacity + M * (1 - y[l]), f"capacity_{l}")

    # (10) Don't exceed library's book count
    for l in L:
        solver.Add(solver.Sum(z[l, b] for b in libraries[l]['books'] 
                    if (l, b) in z) <= len(libraries[l]['books']) * y[l], 
                   f"book_limit_{l}")

    ##### ⚠️ NEW CONSTRAINT ADDED HERE #####
    # Ensure u[b] = 1 ONLY IF scanned from some library
    for b in book_scores:
        relevant_z = [z[l, b] for l in L if (l, b) in z]
        if relevant_z:
            solver.Add(u[b] <= solver.Sum(relevant_z), f"u_bound_{b}")

    # Solve
    solver.SetTimeLimit(time_limit_ms)
    solver.EnableOutput()  # Enable solver logging
    status = solver.Solve()

    return solver, {'y': y, 'z': z, 'u': u, 't': t, 'p': p}