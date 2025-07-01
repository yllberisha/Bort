import os
import glob
import subprocess
import concurrent.futures
import threading
import re

INPUT_DIR = os.path.join('input', 'synthetic')
OUTPUT_FILE = 'scores.txt'
MAX_PARALLEL = 4
TIME_LIMIT = 20*60  # 20 minutes in seconds
WORKERS = 4

# Regex patterns to extract info from output
SCORE_RE = re.compile(r'Score: ([\d,]+)')
STATUS_RE = re.compile(r'status: (\w+)')
GAP_RE = re.compile(r'gap ([\-\d\.]+)%')
OBJECTIVE_RE = re.compile(r'objective: ([\d,]+)')
VALID_SCORE_RE = re.compile(r'Valid solution\. Score: ([\d,]+)')

lock = threading.Lock()

HEADER = ['filename', 'score', 'status', 'gap']
COL_WIDTHS = [32, 12, 12, 8]

def run_solver(input_path):
    filename = os.path.basename(input_path)
    cmd = [
        'python', 'bort.py',
        os.path.join('synthetic', filename),
        '--cp',
        '--workers', str(WORKERS),
        '--time', str(TIME_LIMIT // 60)
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=TIME_LIMIT,
            text=True
        )
        output = proc.stdout
    except subprocess.TimeoutExpired:
        return filename, 'TIMEOUT', 'TIMEOUT', 'TIMEOUT'
    except Exception as e:
        return filename, 'ERROR', 'ERROR', str(e)

    # Try to get the output file name from the logs
    out_file = None
    for line in output.splitlines():
        if 'Solution saved to' in line:
            parts = line.split('Solution saved to')
            if len(parts) > 1:
                out_file = parts[1].strip()
                break
    # If not found, try to guess
    if not out_file:
        base = os.path.splitext(filename)[0]
        out_file = os.path.join('output', 'synthetic', f'{base}_cp_sat.txt')
    # Validate using validate.py
    score = None
    try:
        val_proc = subprocess.run(
            ['python', 'validate.py', os.path.join('synthetic', filename), out_file],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=60
        )
        val_out = val_proc.stdout
        for line in val_out.splitlines():
            if 'Score:' in line:
                m = re.search(r'Score: ([\d,]+)', line)
                if m:
                    score = m.group(1).replace(',', '')
    except Exception:
        pass
    # Fallback to log parsing if validation fails
    status = None
    gap = None
    for line in output.splitlines():
        m = STATUS_RE.search(line)
        if m:
            status = m.group(1)
        if 'gap' in line and '%' in line:
            m = GAP_RE.search(line)
            if m:
                gap = m.group(1)
    if status == 'OPTIMAL':
        gap = '0'
    if score is None:
        # fallback to log parsing for score
        for line in output.splitlines():
            m = SCORE_RE.search(line)
            if m:
                score = m.group(1).replace(',', '')
            m = VALID_SCORE_RE.search(line)
            if m:
                score = m.group(1).replace(',', '')
            m = OBJECTIVE_RE.search(line)
            if m:
                score = m.group(1).replace(',', '')
    if score is None:
        score = 'N/A'
    if status is None:
        status = 'N/A'
    if gap is None:
        gap = 'N/A'
    return filename, score, status, gap

def write_result(filename, score, status, gap):
    with lock:
        line = f"{filename:<{COL_WIDTHS[0]}} {score:>{COL_WIDTHS[1]}} {status:>{COL_WIDTHS[2]}} {gap:>{COL_WIDTHS[3]}}\n"
        with open(OUTPUT_FILE, 'a') as f:
            f.write(line)
        print(f"Logged: {filename}\t{score}\t{status}\t{gap}")

def main():
    # Clear output file and write pretty header
    header_line = f"{HEADER[0]:<{COL_WIDTHS[0]}} {HEADER[1]:>{COL_WIDTHS[1]}} {HEADER[2]:>{COL_WIDTHS[2]}} {HEADER[3]:>{COL_WIDTHS[3]}}\n"
    with open(OUTPUT_FILE, 'w') as f:
        f.write(header_line)
    files = sorted(glob.glob(os.path.join(INPUT_DIR, '*.txt')), key=lambda f: os.path.getsize(f))
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as executor:
        futures = {executor.submit(run_solver, f): f for f in files}
        for future in concurrent.futures.as_completed(futures):
            filename, score, status, gap = future.result()
            write_result(filename, score, status, gap)

if __name__ == '__main__':
    main() 