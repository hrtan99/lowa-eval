#!/usr/bin/python3
import subprocess
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv

class cd:
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

def cmd(commandline, project_dir):
    with cd(project_dir):
        status, output = subprocess.getstatusoutput(commandline)
        return status, output

def compile_single_program(program, output_dir):
    """
    Compile a single C program with multiple optimization levels.

    :param program: Path to the C program file.
    :param output_dir: Directory to save the compiled output.
    :return: List of tuples (program, optimization_level, status, output).
    """
    # clang_path = "clang"
    wasi_clang_path = "/opt/wasi-sdk/bin/clang"

    optimization_levels = ["0", "1", "2", "3"]
    results = []

    for opt in optimization_levels:
        basename = os.path.splitext(os.path.basename(program))[0]
        ll_output_path = os.path.join(output_dir, f"{basename}.{opt}.ll")
        ll_compile_cmd = f"{wasi_clang_path} -S -emit-llvm {program} -w -o {ll_output_path} -O{opt}"
        ll_status, ll_output = subprocess.getstatusoutput(ll_compile_cmd)
        results.append((program, f".{opt}.ll", ll_compile_cmd, ll_status, ll_output))

        wasm_output_path = os.path.join(output_dir, f"{basename}.{opt}.wasm")
        wasm_compile_cmd = f"{wasi_clang_path} {program} -w -o {wasm_output_path} -O{opt}"
        wasm_status, wasm_output = subprocess.getstatusoutput(wasm_compile_cmd)
        results.append((program, f".{opt}.wasm", wasm_compile_cmd, wasm_status, wasm_output))

    return results

def compile_programs_parallel(program_list_path=None, max_workers=None, result_file="compile_results.csv"):
    """
    Compile C programs in parallel with multiple optimization levels and store results.

    :param program_list_path: Path to the file containing the list of programs to compile.
    :param max_workers: Maximum number of worker processes to use.
    :param result_file: Path to the CSV file where results will be stored.
    """
    src_dir = "program_c"
    output_dir = "program_out"
    os.makedirs(output_dir, exist_ok=True)

    # Read program list or use all programs
    if program_list_path and os.path.exists(program_list_path):
        with open(program_list_path, "r", encoding="utf-8") as file:
            programs = [os.path.join(src_dir, line.strip()) for line in file if line.strip()]
    else:
        programs = [os.path.join(root, file) for root, _, files in os.walk(src_dir) for file in files if file.endswith(".c")]

    results = []

    # Compile programs in parallel with progress display
    total_programs = len(programs)
    completed_programs = 0
    success_programs = 0
    error_programs = 0
    success_targets = 0
    error_targets = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(compile_single_program, program, output_dir): program for program in programs}
        for future in as_completed(futures):
            completed_programs += 1
            result = future.result()
            results.extend(result)

            # Track program success
            program_success = True
            for _, _, _, status, _ in result:
                if status == 0:
                    success_targets += 1
                else:
                    error_targets += 1
                    program_success = False

            if program_success:
                success_programs += 1
            else:
                error_programs += 1

            # Display progress
            print(f"Progress: {completed_programs}/{total_programs} programs compiled", end="\r")

    print()  # Move to the next line after progress display

    # Write results to CSV with each column as a target and content as message
    targets = sorted(set(target for _, target, _, _, _ in results))
    target_messages = {target: [] for target in targets}

    for program, target, compile_cmd, status, message in results:
        target_messages[target].append(message)

    with open(result_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Program"] + targets)

        program_to_messages = {}
        for program, target, _, _, message in results:
            if program not in program_to_messages:
                program_to_messages[program] = {t: "" for t in targets}
            program_to_messages[program][target] = message

        for program, messages in program_to_messages.items():
            writer.writerow([program] + [messages[target] for target in targets])

    print(f"Compilation results saved to {result_file}")
    print(f"Summary:")
    print(f"    Programs={total_programs}, Success={success_programs}, Error={error_programs}")
    print(f"    Targets={len(targets)*total_programs}, Success={success_targets}, Error={error_targets}")

if __name__ == "__main__":
    program_list_file = "check_program_list.txt"  # Change this to the desired file path if needed
    compile_programs_parallel(program_list_file)

    # rootdir = "Program"
    # dirs = [home for home, _, _ in os.walk(rootdir)]
    # counter = 0
    # low_dirs = ""

    # with ProcessPoolExecutor() as executor:
    #     futures = {executor.submit(process_dir, d): d for d in dirs}

    #     tfc = 0
    #     tsu = 0
    #     tcc = 0

    #     for future in as_completed(futures):
    #         home, fc, cc, su = future.result()
    #         tfc += fc
    #         tsu += su
    #         tcc += cc
    #         sr = 0
    #         if (cc > 0):
    #             sr = su/cc
    #         if (sr < 0.8):
    #             low_dirs += f"{home} "
    #         print(f"{counter}/104\t{home}\tfile {fc}\tcprog {cc}\tsuccess {su}\tsuccess_rate {sr}")
    #         counter += 1

    #     print(f"Total:\t{rootdir}\tfile {tfc}\tcprog {tcc}\tsuccess {tsu}\tsuccess_rate {tsu/tcc}")
    #     print("Low success rate dirs:", low_dirs)
