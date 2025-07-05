import os
import glob
import subprocess
import concurrent.futures
import threading
import re

INPUT_DIR = os.path.join('input', 'synthetic')
OUTPUT_FILE = 'scores.txt'
MAX_PARALLEL = 4
TIME_LIMIT =  20 * 60  # 20 minutes in seconds
WORKERS = 4

VALID_SCORE_RE = re.compile(r'Valid solution\. Score: ([\d,]+)')
STAT_RE = re.compile(r'status:\s*(\w+)', re.IGNORECASE)
OBJ_RE = re.compile(r'objective:\s*([\d,]+)', re.IGNORECASE)

lock = threading.Lock()

HEADER = ['filename', 'score', 'status']
COL_WIDTHS = [32, 12, 12]

def run_solver(input_path):
    filename = os.path.basename(input_path)
    # Call solver with input file path relative to the 'input' directory
    cmd = [
        'python', 'bort.py',
        os.path.join('synthetic', filename),  # Bort.py will prepend 'input'
        '--cp',
        '--workers', str(WORKERS),
        '--time', str(TIME_LIMIT)
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

    # Try to get the output file name from the logs (Bort.py prints '... saved to <path>')
    out_file = None
    for line in output.splitlines():
        if 'saved to' in line:
            parts = line.split('saved to')
            if len(parts) > 1:
                out_file = parts[1].strip()
                break
    # If not found, use default CP-SAT output naming
    if not out_file:
        base = os.path.splitext(filename)[0]
        out_file = os.path.join('output', f'{base}_cp_sat.txt')

    status_match = STAT_RE.search(output)
    status = status_match.group(1).upper() if status_match else 'UNKNOWN'
    obj_match = OBJ_RE.search(output)
    score = obj_match.group(1).replace(',', '') if obj_match else 'N/A'
    gap = ''
    return filename, score, status, gap

def write_result(filename, score, status, gap):
    with lock:
        line = f"{filename:<{COL_WIDTHS[0]}} {score:>{COL_WIDTHS[1]}} {status:>{COL_WIDTHS[2]}}\n"
        with open(OUTPUT_FILE, 'a') as f:
            f.write(line)
        print(f"Logged: {filename}\t{score}\t{status}")

def main():
    # Clear output file and write pretty header
    header_line = f"{HEADER[0]:<{COL_WIDTHS[0]}} {HEADER[1]:>{COL_WIDTHS[1]}} {HEADER[2]:>{COL_WIDTHS[2]}}\n"
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