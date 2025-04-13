
def read_input_file(filename):
    """
    Reads the input file and returns:
      - B_count: total number of unique books
      - L_count: total number of libraries
      - D: total number of days,
      - book_scores: dict mapping book id to its score,
      - libraries_data: dict mapping library id to a dictionary with:
            'books': list of book ids in the library,
            'signup': days to sign up,
            'ship': books that can be shipped per day.
    Expected file format:
      Line 1: B L D
      Line 2: B integers representing book scores.
      Then, for each library:
          Line: N signup ship
          Line: N integers (book IDs)
    """
    with open(filename, 'r') as f:
        # Filter out any empty lines.
        lines = [line.strip() for line in f if line.strip()]

    # First line: total number of books, libraries, and days.
    B_count, L_count, D = map(int, lines[0].split())

    # Second line: book scores.
    scores = list(map(int, lines[1].split()))
    # Filter out zero-score books potentially upfront if desired, but keep original B_count
    book_scores = {i: score for i, score in enumerate(scores) if score > 0} # OPTIONAL: Filter zero scores
    # B = list(book_scores.keys()) # If filtering zero scores
    B = list(range(B_count)) # Keep original book indices


    libraries_data = {}
    L_ids = list(range(L_count))

    # --- Pre-processing Filter ---
    active_L_ids = [] # Keep track of libraries that *can* be signed up

    # Parse library data (each library has two lines).
    index = 2
    for l_id in L_ids:
        # First line for library: N, signup time, shipping capacity.
        lib_params = list(map(int, lines[index].split()))
        index += 1
        if len(lib_params) < 3:
            raise ValueError(f"Library {l_id} parameters missing")
        N, signup, ship = lib_params

        # Second line: list of book IDs.
        book_list_all = list(map(int, lines[index].split()))
        index += 1

        # Filter books with score > 0 (if desired) and check if library is viable
        # book_list_filtered = [b for b in book_list_all if b in book_scores] # Only keep books with score > 0
        book_list_filtered = book_list_all # Keep all books for now, rely on objective

        # --- Pre-processing Check ---
        # If signup takes all days or more, or if library has no scoreable books (after filtering), skip it
        if signup >= D: # or not book_list_filtered: # Add second condition if filtering books
             print(f"Skipping library {l_id} (signup {signup} >= D {D} or no scoreable books)")
             continue # Skip this library

        active_L_ids.append(l_id)
        libraries_data[l_id] = {
            'books': book_list_filtered, # Use filtered list if applying book filter
            'signup': signup,
            'ship': ship,
            'original_books': book_list_all # Keep original list if needed elsewhere
            }

    # Use only the active libraries for the model
    L = active_L_ids
    print(f"Using {len(L)} libraries out of {L_count} after pre-processing.")

    # Ensure book IDs used by active libraries exist in book_scores
    active_B_ids = set()
    for l_id in L:
        active_B_ids.update(libraries_data[l_id]['books'])

    # Final book list relevant to the active libraries
    # B = list(b for b in B if b in active_B_ids and b in book_scores) # Filter B if needed
    # Using original B for constraint 2 might be safer if not filtering u variables
    B = list(range(B_count))


    return B, L, D, book_scores, libraries_data # Return modified L and potentially B


def get_solution_output(solver, variables, libraries, L):
    """
    Extracts the solution and returns a string representing the submission.
    Output format:
      First line: number of libraries selected.
      Then, for each selected library (ordered by signup start time):
            one line with: library_id number_of_scanned_books,
            and one line with the list of scanned book IDs.
    """
    if not solver or not variables:
        return "No solution found."

    y = variables['y']
    z = variables['z']
    t = variables['t']

    selected_libraries_info = []
    for l in L:
        # Use a tolerance for floating point comparisons with solution values
        if y[l].solution_value() > 0.5:
             selected_libraries_info.append({
                 'id': l,
                 'start_time': t[l].solution_value()
             })

    # Sort selected libraries by their actual computed start time
    selected_libraries_info.sort(key=lambda info: info['start_time'])

    output_lines = []
    output_lines.append(str(len(selected_libraries_info)))

    scanned_books_overall = set() # To verify constraint 2

    for lib_info in selected_libraries_info:
        l = lib_info['id']
        scanned_books_from_lib = []
        for b in libraries[l]['books']:
            # Check if the z variable exists and was selected
            if (l, b) in z and z[(l, b)].solution_value() > 0.5:
                scanned_books_from_lib.append(str(b))
                if b in scanned_books_overall:
                     print(f"WARNING: Book {b} scanned again from library {l}!") # Should not happen
                scanned_books_overall.add(b)


        if scanned_books_from_lib: # Only output libraries that scan at least one book
            output_lines.append(f"{l} {len(scanned_books_from_lib)}")
            output_lines.append(" ".join(scanned_books_from_lib))
        # else: # Optional: Decide if you want to list libraries selected but scanning 0 books
        #    print(f"Library {l} was selected but scanned 0 books.")


    # Adjust output if some selected libraries scanned 0 books and were omitted
    # Recalculate the count based on libraries actually outputted
    actual_output_library_count = (len(output_lines) -1) // 2
    output_lines[0] = str(actual_output_library_count)


    return "\n".join(output_lines)

def save_solution_file(solution_text, filename):
    """
    Saves the solution text to a file.
    """
    with open(filename, 'w') as f:
        f.write(solution_text)
    print(f"Solution saved to {filename}")