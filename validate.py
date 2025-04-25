#!/usr/bin/env python3
import sys

def error(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)

def read_ints(line):
    return list(map(int, line.strip().split()))

def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input_file> <solution_file>")
        sys.exit(1)

    input_path = sys.argv[1]
    sol_path = sys.argv[2]

    # Read input file
    try:
        with open(input_path, 'r') as f:
            # First line: B, L, D
            line = f.readline()
            if not line:
                error("Input file is empty")
            BLD = read_ints(line)
            if len(BLD) != 3:
                error("Input file first line must contain three integers: B L D")
            B, L, D = BLD

            # Second line: book scores
            line = f.readline()
            if not line:
                error("Missing book scores line")
            book_scores = read_ints(line)
            if len(book_scores) != B:
                error(f"Expected {B} book scores, got {len(book_scores)}")

            # Next L library descriptions
            libraries = []
            for lib_id in range(L):
                line = f.readline()
                if not line:
                    error(f"Missing library {lib_id} description")
                parts = read_ints(line)
                if len(parts) != 3:
                    error(f"Library {lib_id} header must have 3 ints: N T M")
                N, T, M = parts
                # Next line: N book IDs
                line = f.readline()
                if not line:
                    error(f"Missing book ID list for library {lib_id}")
                book_ids = read_ints(line)
                if len(book_ids) != N:
                    error(f"Library {lib_id}: expected {N} book IDs, got {len(book_ids)}")
                libraries.append({
                    "N": N, "T": T, "M": M,
                    "books": set(book_ids)
                })
    except FileNotFoundError:
        error(f"Input file '{input_path}' not found")
    except Exception as e:
        error(f"Error reading input file: {e}")

    # Read solution file
    try:
        with open(sol_path, 'r') as f:
            line = f.readline()
            if not line:
                error("Solution file is empty")
            A = int(line.strip())
            solution = []
            for i in range(A):
                line = f.readline()
                if not line:
                    error(f"Missing signup line for solution library {i}")
                parts = read_ints(line)
                if len(parts) != 2:
                    error(f"Solution line must have 2 ints: lib_id K")
                lib_id, K = parts
                if lib_id < 0 or lib_id >= L:
                    error(f"Invalid library ID {lib_id} in solution")
                line = f.readline()
                if not line:
                    error(f"Missing book list for solution library {lib_id}")
                book_ids = read_ints(line)
                if len(book_ids) != K:
                    error(f"Library {lib_id} in solution: expected {K} book IDs, got {len(book_ids)}")
                solution.append((lib_id, book_ids))
    except FileNotFoundError:
        error(f"Solution file '{sol_path}' not found")
    except Exception as e:
        error(f"Error reading solution file: {e}")

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
                error(f"Book {b} not available in library {lib_id}")
            if b in scanned:
                # already scanned, skip score addition
                continue
            scanned.add(b)
            score += book_scores[b]

    # Output final score
    print(f"Your score: {score}")

if __name__ == "__main__":
    main()


