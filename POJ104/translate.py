import os
import time
import csv
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

def translate_wasm_to_ll(wasm_path, src_dir, out_dir):
    """
    Call lowa to convert wasm to ll, preserve directory structure, 
    return (input file, output file, command, status, elapsed time)
    Output is saved to a .log file next to the ll file.
    """
    lowa_path = "/home/wang/lowa/lowa/build/tools/lowa"
    rule_path = "/home/wang/lowa/lowa/lib/rules_gpt.lr"

    relative_path = os.path.relpath(wasm_path, src_dir)
    out_base = os.path.splitext(relative_path)[0]
    ll_output_path = os.path.join(out_dir, f"{out_base}.ll")
    log_output_path = os.path.join(out_dir, f"{out_base}.log")
    output_dir = os.path.dirname(ll_output_path)
    os.makedirs(output_dir, exist_ok=True)
    # Use absolute path for wasm input, and only filename for output (since cwd=output_dir)
    abs_wasm_path = os.path.abspath(wasm_path)
    ll_filename = os.path.basename(ll_output_path)
    cmd = f"{lowa_path} -i {abs_wasm_path} -O -r={rule_path} -o {ll_filename}"
    start = time.time()
    try:
        result = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
            cwd=output_dir, timeout=10
        )
        elapsed = time.time() - start
        status = result.returncode
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - start
        status = "timeout"
        output = ""
        if hasattr(e, "output") and e.output:
            # e.output may be bytes, decode if needed
            if isinstance(e.output, bytes):
                output += e.output.decode("utf-8", errors="replace")
            else:
                output += e.output
        if hasattr(e, "stderr") and e.stderr:
            if isinstance(e.stderr, bytes):
                output += e.stderr.decode("utf-8", errors="replace")
            else:
                output += e.stderr
    # Save command output to .log file
    with open(log_output_path, "w", encoding="utf-8") as logf:
        logf.write(output)
    return (relative_path, status, elapsed)

def main():
    src_dir = "program_out"
    out_dir = "program_translated"
    stats_file = "poj104_translate_stats.csv"
    # Traverse all wasm files
    wasm_files = [os.path.join(root, file)
                  for root, _, files in os.walk(src_dir)
                  for file in files if file.endswith(".wasm")]
    results = []
    total = len(wasm_files)
    completed = 0
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(translate_wasm_to_ll, wasm, src_dir, out_dir): wasm for wasm in wasm_files}
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            results.append(result)
            current_file = futures[future]
            if completed % 1 == 0 or completed == total:
                percent = (completed / total) * 100
                print(f"Progress: {completed}/{total} ({percent:.2f}%) | Processing: {os.path.relpath(current_file, src_dir)}", end="\r")
    print()
    # Save statistics (only status, not output)
    with open(stats_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "status", "elapsed_sec"])
        for row in results:
            writer.writerow(row)
    print(f"Stats saved to {stats_file}")

    # Count success and failure
    success_count = sum(1 for _, status, _ in results if status == 0)
    fail_count = len(results) - success_count
    print(f"Total:{len(results)}, Success: {success_count}, Fail: {fail_count}")

if __name__ == "__main__":
    main()
