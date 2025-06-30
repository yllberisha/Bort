# Bort Solver: Google HashCode 2020 Book Scanning Optimizer

This repository contains an implementation of a Mixed Integer Linear Programming (MILP) and Constraint Programming (CP-SAT) solution for the Google HashCode 2020 Book Scanning problem using Google's OR-Tools optimization library.

## Problem Description

The Google HashCode 2020 Book Scanning problem involves optimizing the scanning of books across multiple libraries. Each book has a score, and each library has:
- A set of books
- A signup time (days required to register the library)
- A shipping rate (books that can be scanned per day once signed up)

The goal is to maximize the total score of all unique books scanned within a limited number of days.

## Solution Approach

This solution uses both MILP and CP-SAT approaches with the following key components:
- Decision variables for library selection, book scanning, and library signup order
- Objective function to maximize total book scores
- Constraints for library signup times, book scanning capacity, and unique book scanning

The underlying solver is SCIP (for MILP) or CP-SAT (for CP), both via OR-Tools.

## Requirements

- Python 3.6+
- OR-Tools (`pip install ortools`)

## Usage

### Running the Solver

The solver expects input files to be in the `input/` directory and automatically saves solutions to the `output/` directory.

```bash
python bort.py [input_filename] [--cp] [--milp] [--time SECONDS] [--workers N]
```

- `[input_filename]`: Name of the file in the `input/` directory.
- `--cp`: Use the CP-SAT solver (default is MILP if not specified).
- `--milp`: Explicitly use the MILP solver (default).
- `--time SECONDS`: Time limit for the solver in seconds (applies to both MILP and CP; default 300).
- `--workers N`: Number of search workers (CP only; default 1).

### Examples

Run MILP (default):
```bash
python bort.py a_example.txt --time 120
```

Run CP-SAT:
```bash
python bort.py a_example.txt --cp --time 60 --workers 4
```

## Input Format

The input files follow the Google HashCode 2020 format:
- First line: `B L D` (number of books, libraries, and days)
- Second line: Score of each book
- For each library:
  - First line: `N T M` (number of books, signup time, books per day)
  - Second line: IDs of books in the library

## Output Format

The solution file format:
- First line: `A` (number of libraries to sign up)
- For each library to sign up:
  - First line: `L K` (library ID, number of books to scan)
  - Second line: IDs of books to scan in order

## Repository Structure

- `bort_solver.py`: Core MILP optimization model implementation
- `bort_cp.py`: Core CP-SAT optimization model implementation
- `bort.py`: Command-line script that runs the solver
- `utils.py`: Utility functions for file I/O and solution formatting
- `input/`: Directory containing problem input files
- `output/`: Directory where solutions are saved

## License

This project is open source and available under the MIT License. 
