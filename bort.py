# Main script to run Book Scanning solver (MILP or CP-SAT)

import sys, os, argparse
from validate import validate_solution

sys.path.append(os.path.join(os.path.dirname(__file__), "Bort_Solver"))

from bort_milp import solve_book_scanning_milp
from utils import read_input_file, get_solution_output, save_solution_file

def main(args):
    input_path = os.path.join("input", args.input_file)
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    print(f"Reading input: {input_path}")
    B, L, D, scores, libs = read_input_file(input_path)

    os.makedirs("output", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    if args.cp:
        from Bort_Solver.bort_cp import preprocess, solve_cp_sat, build_output

        pre_libs = preprocess(B, libs, D, scores)
        print(f"Libraries kept: {len(pre_libs)} / {len(libs)}")

        obj, order, books = solve_cp_sat(
            B, list(pre_libs), D, scores, pre_libs,
            time_limit_s=args.time,
            workers=args.workers
        )

        solution = build_output(order, books)
        out_file = f"output/{base_name}_cp_sat.txt"
        save_solution_file(solution, out_file)
        print(f"Score: {int(obj):,} → saved to {out_file}")

    else:
        time_limit_ms = args.time * 1000
        solver, vars_ = solve_book_scanning_milp(B, L, D, scores, libs, time_limit_ms)

        if not solver or not vars_:
            print("MILP solver failed or returned no solution.")
            return

        try:
            obj = solver.Objective().Value()
            solution = get_solution_output(solver, vars_, libs, L)
            out_file = f"output/{base_name}_milp.txt"
            save_solution_file(solution, out_file)
            print(f"Score: {int(obj):,} → saved to {out_file}")
        except Exception as e:
            print(f"Error during MILP solution extraction: {e}")
            return

    print("Validating solution...")
    result = validate_solution(input_path, out_file)
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Book Scanning Solver")
    parser.add_argument("input_file", help="File name inside ./input")
    parser.add_argument("--cp", action="store_true", help="Use CP-SAT solver")
    parser.add_argument("--milp", action="store_true", help="Use MILP solver (default)")
    parser.add_argument("--time", type=int, default=300, help="Time limit (sec)")
    parser.add_argument("--workers", type=int, default=1, help="CP-SAT worker count")
    args = parser.parse_args()
    
    main(args)
