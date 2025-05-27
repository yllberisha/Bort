#!/usr/bin/env python3
import sys

def error(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)

def read_ints(line):
    return list(map(int, line.strip().split()))

def validate_solution(input_path, sol_path):
    """Validate a solution file against an input file and return the score."""
    try:
        # Read input file
        with open(input_path, 'r') as f:
            # First line: B, L, D
            line = f.readline()
            if not line:
                return "Error: Input file is empty"
            BLD = read_ints(line)
            if len(BLD) != 3:
                return "Error: Input file first line must contain three integers: B L D"
            B, L, D = BLD

            # Second line: book scores
            line = f.readline()
            if not line:
                return "Error: Missing book scores line"
            book_scores = read_ints(line)
            if len(book_scores) != B:
                return f"Error: Expected {B} book scores, got {len(book_scores)}"

            # Next L library descriptions
            libraries = []
            for lib_id in range(L):
                line = f.readline()
                if not line:
                    return f"Error: Missing library {lib_id} description"
                parts = read_ints(line)
                if len(parts) != 3:
                    return f"Error: Library {lib_id} header must have 3 ints: N T M"
                N, T, M = parts
                # Next line: N book IDs
                line = f.readline()
                if not line:
                    return f"Error: Missing book ID list for library {lib_id}"
                book_ids = read_ints(line)
                if len(book_ids) != N:
                    return f"Error: Library {lib_id}: expected {N} book IDs, got {len(book_ids)}"
                libraries.append({
                    "N": N, "T": T, "M": M,
                    "books": set(book_ids)
                })

        # Read solution file
        with open(sol_path, 'r') as f:
            line = f.readline()
            if not line:
                return "Error: Solution file is empty"
            A = int(line.strip())
            solution = []
            for i in range(A):
                line = f.readline()
                if not line:
                    return f"Error: Missing signup line for solution library {i}"
                parts = read_ints(line)
                if len(parts) != 2:
                    return f"Error: Solution line must have 2 ints: lib_id K"
                lib_id, K = parts
                if lib_id < 0 or lib_id >= L:
                    return f"Error: Invalid library ID {lib_id} in solution"
                line = f.readline()
                if not line:
                    return f"Error: Missing book list for solution library {lib_id}"
                book_ids = read_ints(line)
                if len(book_ids) != K:
                    return f"Error: Library {lib_id} in solution: expected {K} book IDs, got {len(book_ids)}"
                solution.append((lib_id, book_ids))

        # Validate and compute score
        scanned = set()
        score = 0
        day = 0

        for lib_id, book_list in solution:
            lib = libraries[lib_id]
            # signup
            day += lib["T"]
            if day > D:
                # no more scanning allowed
                break
            remaining_days = D - day
            max_books = remaining_days * lib["M"]
            # scan books in order, up to capacity
            for i, b in enumerate(book_list):
                if i >= max_books:
                    break
                if b not in lib["books"]:
                    return f"Error: Book {b} not available in library {lib_id}"
                if b in scanned:
                    # already scanned, skip score addition
                    continue
                scanned.add(b)
                score += book_scores[b]

        return f"Valid solution. Score: {score}"

    except FileNotFoundError as e:
        return f"Error: File not found - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input_file> <solution_file>")
        sys.exit(1)

    input_path = sys.argv[1]
    sol_path = sys.argv[2]
    
    result = validate_solution(input_path, sol_path)
    print(result)

if __name__ == "__main__":
    main()


