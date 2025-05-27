# Main script for running the simplified solver (

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "Bort_Solver"))

from simplified_bort import solve_book_scanning
from utils import read_input_file, get_solution_output, save_solution_file
# Import the validation function directly
from validate import validate_solution

def main():
    if len(sys.argv) != 2:
        print("Usage: python simplified_main.py <input_file.txt>")
        sys.exit(1)

    input_filename = f'input/{sys.argv[1]}'
    
    if not os.path.exists(input_filename):
        print(f"Error: Input file '{input_filename}' not found.")
        sys.exit(1)
    
    print(f"Reading input file: {input_filename}")
    B_all, L_all, D_days, book_scores_dict, libraries_dict = read_input_file(input_filename)
    
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    solve_time_limit_ms = 60 * 1000 * 20
    
    # No need to try with input_file parameter - simplified solver doesn't have it
    solver, variables = solve_book_scanning(
        B_all, L_all, D_days, book_scores_dict, libraries_dict,
        time_limit_ms=solve_time_limit_ms
    )
    
    if solver and variables:
        try:
            objective_value = solver.Objective().Value()
            print(f"\nObjective Value (Mathematical) = {objective_value:.0f}")
            
            solution_text = get_solution_output(solver, variables, libraries_dict, L_all)
            
            base_name = os.path.basename(input_filename)
            name_without_ext = os.path.splitext(base_name)[0]
            output_filename = os.path.join(output_dir, f"{name_without_ext}_simplified_solution.txt")
            
            save_solution_file(solution_text, output_filename)
            
            # Validate the solution directly
            print("\nValidating solution...")
            validation_result = validate_solution(input_filename, output_filename)
            print(validation_result)
            
        except Exception as e:
            print(f"\nError during solution processing: {e}")
    else:
        print("\nSolver setup failed or returned None.")

if __name__ == "__main__":
    main() 