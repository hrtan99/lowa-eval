#!/usr/bin/python3
import subprocess
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

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

def process_dir(home):
    clang_path = "clang"
    wasi_clang_path = "/opt/wasi-sdk/bin/clang"
    clang_compile_host_cmd = clang_path + " {} -w -o {} -lm"
    clang_compile_wasm_cmd = wasi_clang_path + " {} -w -o {} -lm -v"

    file_count = 0
    success = 0
    c_count = 0

    files = sorted(os.listdir(home))
    for filename in files:
        if filename.endswith('.c'):
            host_file = filename[:-2] + ".out"
            status, output = cmd(clang_compile_host_cmd.format(filename, host_file), home)
            file_count += 1
            if status != 0:
                if not ("cin" in output or "cout" in output):
                    c_count += 1
            else:
                c_count += 1
                success += 1
                wasm_file = filename[:-2] + ".wasm"
                status, output = cmd(clang_compile_wasm_cmd.format(filename, wasm_file), home)
                if status != 0:
                    print(wasm_file)
                    print(output)
        # break

    return home, file_count, c_count, success

if __name__ == "__main__":
    rootdir = "Program"
    dirs = [home for home, _, _ in os.walk(rootdir)]
    counter = 0
    low_dirs = ""

    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_dir, d): d for d in dirs}

        tfc = 0
        tsu = 0
        tcc = 0

        for future in as_completed(futures):
            home, fc, cc, su = future.result()
            tfc += fc
            tsu += su
            tcc += cc
            sr = 0
            if (cc > 0):
                sr = su/cc
            if (sr < 0.8):
                low_dirs += f"{home} "
            print(f"{counter}/104\t{home}\tfile {fc}\tcprog {cc}\tsuccess {su}\tsuccess_rate {sr}")
            counter += 1

        print(f"Total:\t{rootdir}\tfile {tfc}\tcprog {tcc}\tsuccess {tsu}\tsuccess_rate {tsu/tcc}")
        print("Low success rate dirs:", low_dirs)
