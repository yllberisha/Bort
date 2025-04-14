# Bort Solver: Google HashCode 2020 Book Scanning Optimizer

This repository contains an implementation of a Mixed Integer Linear Programming (MILP) solution for the Google HashCode 2020 Book Scanning problem using Google's OR-Tools optimization library.

## Problem Description

The Google HashCode 2020 Book Scanning problem involves optimizing the scanning of books across multiple libraries. Each book has a score, and each library has:
- A set of books
- A signup time (days required to register the library)
- A shipping rate (books that can be scanned per day once signed up)

The goal is to maximize the total score of all unique books scanned within a limited number of days.

## Solution Approach

This solution uses a MILP approach with the following key components:
- Decision variables for library selection, book scanning, and library signup order
- Objective function to maximize total book scores
- Constraints for library signup times, book scanning capacity, and unique book scanning

The underlying solver is SCIP (via OR-Tools), which is a high-performance solver for mixed integer programming problems.

## Requirements

- Python 3.6+
- OR-Tools (`pip install ortools`)

## Usage

### Running the Solver

```bash
python bort.py [input_file]
```

Parameters:
- `--input`: Path to the input problem file (required)

### Example

```bash
python main.py data/a_example.txt
```

### Validating Solutions

You can validate the solutions using the validation script:

```bash
python validate.py [input_file] [solution_file]
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

- `bort_solver.py`: Core optimization model implementation
- `bort.py`: Command-line interface for running the solver
- `utils.py`: Utility functions for file I/O and solution formatting
- `validate.py`: Script to validate solutions against problem constraints

## License

This project is open source and available under the MIT License. 
