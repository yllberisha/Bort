# Book Scanning Problem: Mathematical Formulation and Python Implementation

## Sets and Parameters

### Mathematical Formulation:

Let:

- \( B \): the set of books  
- \( L \): the set of libraries  
- \( D \): total number of days available for scanning  
- For each book \( b \in B \), let \( s_b \) be the score awarded when book \( b \) is scanned  
- For each library \( l \in L \):  
  - \( B_l \subseteq B \): set of books available in library \( l \)  
  - \( \sigma_l \): number of days to complete the signup process for library \( l \)  
  - \( \delta_l \): number of books library \( l \) can scan per day after signup  

### Code Implementation:
```python
# B: set of books (assumed as indices or IDs)
# L: set of libraries (assumed as indices or IDs)
# D: total days (integer)
# book_scores: dictionary mapping b to s_b
# libraries: dictionary where libraries[l] has 'books' (B_l), 'signup' (sigma_l), 'ship' (delta_l)
```

---

## Decision Variables

### Mathematical Formulation:

- \( y_l \in \{0, 1\} \): 1 if library \( l \) is signed up, 0 otherwise  
- \( z_{l,b} \in \{0, 1\} \): 1 if book \( b \) is scanned from library \( l \)  
- \( u_b \in \{0, 1\} \): 1 if book \( b \) is scanned from any library  
- \( p_{l1,l2} \in \{0, 1\} \): 1 if library \( l1 \) is processed before \( l2 \)  
- \( t_l \in \{0, 1, \ldots, D-1\} \): day when signup for library \( l \) starts  

### Code Implementation:
```python
from ortools.linear_solver import pywraplp
solver = pywraplp.Solver.CreateSolver('SCIP')

y = {l: solver.IntVar(0, 1, f'y[{l}]') for l in L}
z = {(l, b): solver.IntVar(0, 1, f'z[{l},{b}]') 
     for l in L for b in libraries[l]['books'] if b in book_scores}
u = {b: solver.IntVar(0, 1, f'u[{b}]') for b in B}
p = {(l1, l2): solver.IntVar(0, 1, f'p[{l1},{l2}]') 
     for l1 in L for l2 in L if l1 != l2}
t = {l: solver.IntVar(0, D - 1, f't[{l}]') for l in L}
```

---

## Objective Function

### Mathematical Formulation:

\[
\text{Maximize } \sum_{b \in B} s_b u_b
\]

### Meaning:

The goal is to maximize the total score of scanned books. A book contributes its score \( s_b \) only if it is scanned (\( u_b = 1 \)).

### Code Implementation:
```python
objective = solver.Objective()
for b in B:
    if b in book_scores:
        objective.SetCoefficient(u[b], book_scores[b])
objective.SetMaximization()
```

---

## Constraints

### 1. Each Book Scanned at Most Once

#### Mathematical Formulation:
\[
\sum_{l \in L} z_{l,b} \leq 1 \quad \forall b \in B
\]

#### Meaning:
Each book can be scanned by at most one library.

#### Code:
```python
for b in B:
    relevant_z = [z[(l, b)] for l in L 
                  if b in libraries[l]['books'] and (l, b) in z]
    if relevant_z:
        solver.Add(solver.Sum(relevant_z) <= 1)
```

---

### 2. Link \( u_b \) to \( z_{l,b} \)

#### Mathematical Formulation:
\[
u_b \geq z_{l,b} \quad \forall l \in L, \, \forall b \in B_l
\]

#### Meaning:
If a book is scanned from any library, then \( u_b = 1 \).

#### Code:
```python
for l in L:
    for b in libraries[l]['books']:
        if (l, b) in z:
            solver.Add(u[b] >= z[(l, b)])
```

---

### 3. Only Scan from Signed-Up Libraries

#### Mathematical Formulation:
\[
z_{l,b} \leq y_l \quad \forall l \in L, \, \forall b \in B_l
\]

#### Meaning:
A library can only scan books if it has been signed up.

#### Code:
```python
for l in L:
    for b in libraries[l]['books']:
        if (l, b) in z:
            solver.Add(z[(l, b)] <= y[l])
```

---

### 4. Library Order Can't Conflict

#### Mathematical Formulation:
\[
p_{l1,l2} + p_{l2,l1} \leq 1 \quad \forall l1, l2 \in L, \, l1 \neq l2
\]

#### Meaning:
No two libraries can be ordered before each other.

#### Code:
```python
for l1 in L:
    for l2 in L:
        if l1 < l2:
            solver.Add(p[(l1, l2)] + p[(l2, l1)] <= 1)
```

---

### 5. Timing Between Libraries

#### Mathematical Formulation:
\[
t_{l2} \geq t_{l1} + \sigma_{l1} \cdot y_{l1} - D \cdot (1 - p_{l1,l2})
\quad \forall l1, l2 \in L, \, l1 \neq l2
\]

#### Meaning:
If library \( l1 \) is before \( l2 \), \( l2 \) starts after \( l1 \)'s signup.

#### Code:
```python
for l1 in L:
    for l2 in L:
        if l1 != l2:
            solver.Add(t[l2] >= t[l1] + libraries[l1]['signup'] * y[l1] 
                       - D * (1 - p[(l1, l2)]))
``` 