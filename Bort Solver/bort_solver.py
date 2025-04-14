from ortools.linear_solver import pywraplp
import time
import os
import sys
import tempfile
from utils import get_solution_output, read_input_file, save_solution_file

# Add parent directory to path to import validate
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from validate import validate_solution, read_input_file as validate_read_input

def calculate_validator_score(solver, variables, book_scores, libraries, L, D, input_file):
    """
    Uses the validator from validate.py to calculate the score.
    This ensures scores are calculated with exactly the same logic as the validator.
    """
    if not solver or not variables:
        return 0, 0, {}
    
    # First, get the solution output text
    solution_text = get_solution_output(solver, variables, libraries, L)
    
    # Write to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        tmp_file.write(solution_text)
        tmp_file_path = tmp_file.name
    
    try:
        # Run the validator
        validation_result = validate_solution(input_file, tmp_file_path)
        
        # Extract the score
        if "Total score: " in validation_result:
            # Extract score from validation result
            score_line = [line for line in validation_result.split('\n') if "Total score: " in line][0]
            score = int(score_line.split("Total score: ")[1])
            
            # Extract book count
            books_line = [line for line in validation_result.split('\n') if "Scanned books: " in line][0]
            book_count = int(books_line.split("Scanned books: ")[1].split('/')[0])
            
            return score, book_count, validation_result
        else:
            # Validation found errors
            return 0, 0, validation_result
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

def solve_book_scanning_strict(B, L, D, book_scores, libraries, time_limit_ms=300000, input_file=None):
    """
    Builds and solves the MILP model for book scanning with a corrected formulation.
    
    Args:
        B: Set of all book IDs.
        L: Set of all library IDs.
        D: Total number of days.
        book_scores: Dict mapping book IDs to their scores.
        libraries: Dict containing library details (books, signup time, ship rate).
        time_limit_ms: Solver time limit in milliseconds (default: 300,000 ms = 5 minutes).
        input_file: Path to the input file (for validation).
    
    Returns:
        - solver: The OR-Tools solver instance with the solution.
        - variables: Dict containing the decision variables.
    """
    # Initialize the solver
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        raise Exception("SCIP solver not found.")

    solver.SetSolverSpecificParametersAsString("display/verblevel=4")

    solver.SetTimeLimit(time_limit_ms)
    print(f"Solver time limit set to {time_limit_ms / 1000} seconds.")
    start_time = time.time()

    # --- Decision Variables ---
    # y[l]: Binary variable, 1 if library l is signed up, 0 otherwise
    y = {l: solver.IntVar(0, 1, f'y[{l}]') for l in L}

    # z[l,b]: Binary variable, 1 if library l scans book b, 0 otherwise
    z = {}
    for l in L:
        for b in libraries[l]['books']:
            if b in book_scores:
                z[(l, b)] = solver.IntVar(0, 1, f'z[{l},{b}]')

    # u[b]: Binary variable, 1 if book b is scanned, 0 otherwise
    u = {b: solver.IntVar(0, 1, f'u[{b}]') for b in B}

    # p[l1,l2]: Binary variable, 1 if library l1 signs up before l2, 0 otherwise
    p = {}
    for l1 in L:
        for l2 in L:
            if l1 != l2:
                p[(l1, l2)] = solver.IntVar(0, 1, f'p[{l1},{l2}]')

    # t[l]: Integer variable, the day library l starts scanning
    t = {l: solver.IntVar(0, D - 1, f't[{l}]') for l in L}

    print(f"Time after variable creation: {time.time() - start_time:.2f}s")

    # --- Objective Function ---
    # Maximize the total score: ∑ (book_score[b] * u[b])
    objective = solver.Objective()
    for b in B:
        if b in book_scores:
            objective.SetCoefficient(u[b], book_scores[b])
    objective.SetMaximization()

    print(f"Time after objective setup: {time.time() - start_time:.2f}s")

    # --- Constraints ---

    # 1. Each book is scanned at most once: ∑ z[l,b] ≤ 1 for all b
    for b in B:
        relevant_z_vars = [z[(l, b)] for l in L if b in libraries[l]['books'] and (l, b) in z]
        if relevant_z_vars:
            solver.Add(solver.Sum(relevant_z_vars) <= 1, name=f"book_scanned_at_most_once_{b}")

    print(f"Time after constraint 1: {time.time() - start_time:.2f}s")

    # 2. Link u[b] to z[l,b]: u[b] ≥ z[l,b] for all l, b in B_l
    for l in L:
        for b in libraries[l]['books']:
            if (l, b) in z:
                solver.Add(u[b] >= z[(l, b)], name=f"link_u_z_{l}_{b}")

    print(f"Time after constraint 2: {time.time() - start_time:.2f}s")

    # 3. A book can only be scanned if the library is signed up: z[l,b] ≤ y[l]
    for l in L:
        for b in libraries[l]['books']:
            if (l, b) in z:
                solver.Add(z[(l, b)] <= y[l], name=f"scan_if_selected_{l}_{b}")

    print(f"Time after constraint 3: {time.time() - start_time:.2f}s")

    # 4. Order exclusivity: p[l1,l2] + p[l2,l1] ≤ 1 for all l1 ≠ l2
    for l1 in L:
        for l2 in L:
            if l1 < l2:
                solver.Add(p[(l1, l2)] + p[(l2, l1)] <= 1, name=f"order_exclusive_{l1}_{l2}")

    print(f"Time after constraint 4: {time.time() - start_time:.2f}s")

    # 5. Timing constraint: t[l2] ≥ t[l1] + signup[l1] * y[l1] - D * (1 - p[l1,l2])
    for l1 in L:
        for l2 in L:
            if l1 != l2:
                solver.Add(t[l2] >= t[l1] + libraries[l1]['signup'] * y[l1] - D * (1 - p[(l1, l2)]), 
                           name=f"timing_{l1}_before_{l2}")

    print(f"Time after constraint 5: {time.time() - start_time:.2f}s")

    # 6. Order if both signed up: p[l1,l2] + p[l2,l1] ≥ y[l1] + y[l2] - 1
    for l1 in L:
        for l2 in L:
            if l1 < l2:
                solver.Add(p[(l1, l2)] + p[(l2, l1)] >= y[l1] + y[l2] - 1, 
                           name=f"order_if_both_{l1}_{l2}")

    print(f"Time after constraint 6: {time.time() - start_time:.2f}s")

    # 7. Signup must finish within D days: t[l] + signup[l] * y[l] ≤ D
    for l in L:
        solver.Add(t[l] + libraries[l]['signup'] * y[l] <= D, name=f"signup_finish_time_{l}")

    print(f"Time after constraint 7: {time.time() - start_time:.2f}s")

    # 8. Capacity constraint: ∑ z[l,b] ≤ ship[l] * (D - t[l] - signup[l]) + M * (1 - y[l])
    for l in L:
        sum_z = solver.Sum(z[(l, b)] for b in libraries[l]['books'] if (l, b) in z)
        capacity_if_active = libraries[l]['ship'] * (D - t[l] - libraries[l]['signup'])
        M = len(libraries[l]['books'])
        solver.Add(sum_z <= capacity_if_active + M * (1 - y[l]), name=f"capacity_limit_{l}")

    print(f"Time after constraint 8: {time.time() - start_time:.2f}s")

    # 9. Scanned books ≤ available books: ∑ z[l,b] ≤ |B_l| * y[l]
    for l in L:
        sum_z = solver.Sum(z[(l, b)] for b in libraries[l]['books'] if (l, b) in z)
        num_books_in_library = len(libraries[l]['books'])
        solver.Add(sum_z <= num_books_in_library * y[l], name=f"scanned_le_available_{l}")

    print(f"Time after constraint 9: {time.time() - start_time:.2f}s")

    # 10. New constraint: u[b] ≤ ∑ z[l,b] for each book b
    for b in B:
        relevant_z_vars = [z[(l, b)] for l in L if b in libraries[l]['books'] and (l, b) in z]
        if relevant_z_vars:
            solver.Add(u[b] <= solver.Sum(relevant_z_vars), name=f"u_bounded_by_z_{b}")

    print(f"Time after new constraint: {time.time() - start_time:.2f}s")

    print(f"Model building completed in {time.time() - start_time:.2f} seconds.")
    print(f"Number of variables = {solver.NumVariables()}")
    print(f"Number of constraints = {solver.NumConstraints()}")

    # --- Solve the Model ---
    print("\nStarting solver...")
    solve_start_time = time.time()
    status = solver.Solve()
    solve_end_time = time.time()
    print(f"Solver finished in {solve_end_time - solve_start_time:.2f} seconds.")

    # --- Check Solution Status ---
    if status == pywraplp.Solver.OPTIMAL:
        print("\nSolution found: OPTIMAL")
    elif status == pywraplp.Solver.FEASIBLE:
        print("\nSolution found: FEASIBLE (may not be optimal due to time limit)")
    elif status == pywraplp.Solver.INFEASIBLE:
        raise Exception("Problem is INFEASIBLE.")
    else:
        raise Exception(f"Solver failed with status: {status}")

    # Calculate and print the scores
    objective_value = solver.Objective().Value()
    
    print(f"\nObjective Value (Mathematical) = {objective_value:.0f}")
    
    # If input_file is provided, use the validate.py validator
    if input_file:
        validated_score, books_scanned, validation_details = calculate_validator_score(
            solver, {'y': y, 'z': z, 't': t, 'p': p, 'u': u}, 
            book_scores, libraries, L, D, input_file
        )
        
        print(f"Validated Score (Using validator.py) = {validated_score:.0f}")
        print(f"Books Scanned = {books_scanned}")
        
        # If there's a difference, explain it
        if objective_value != validated_score:
            print(f"\nScore Difference = {objective_value - validated_score:.0f}")
            print("|* This difference occurs because the validator accounts for time constraints")
            print("|* and library capacities when calculating the score, while the solver's")
            print("|* objective value is based on the mathematical model.\n")
    
    variables = {'y': y, 'z': z, 't': t, 'p': p, 'u': u}
    return solver, variables