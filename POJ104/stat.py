
import os
import re
import csv
import subprocess

# Directory to be analyzed
CODE_ROOT = os.path.join(os.path.dirname(__file__), 'program_c')

# Fields for statistics
FIELDS = [
    'file', 'is_cpp', 'has_struct', 'has_switch', 'has_indirect_call', 'has_scanf', 'has_printf',
    'line_count', 'function_count'
]

def is_cpp(code):
    # Return True if C++-only features appear
    cpp_keywords = ['::', 'using', 'class', 'new', 'delete', 'cout', 'cin', 'endl', 'template', 'namespace']
    return any(kw in code for kw in cpp_keywords)

def has_struct(code):
    return bool(re.search(r'\bstruct\b', code))

def has_switch(code):
    return bool(re.search(r'\bswitch\b', code))

def has_indirect_call(code):
    # Check for indirect function call: (*xxx)( or xxx->xxx(
    return bool(re.search(r'\(\*\w+\)\s*\(|->\s*\w+\s*\(', code))

def has_scanf(code):
    return bool(re.search(r'\bscanf\s*\(', code))

def has_printf(code):
    return bool(re.search(r'\bprintf\s*\(', code))

def count_lines(code):
    # Count total lines in the file
    return len(code.splitlines())

def count_functions(filepath):
    # Use ctags to count functions in the file
    try:
        result = subprocess.run([
            'ctags', '--c-kinds=f', '-x', filepath
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', check=True)
        lines = result.stdout.strip().splitlines()
        return len(lines)
    except Exception:
        return -1

def stat_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()
    return {
        'file': os.path.relpath(filepath, CODE_ROOT),
        'is_cpp': is_cpp(code),
        'has_struct': has_struct(code),
        'has_switch': has_switch(code),
        'has_indirect_call': has_indirect_call(code),
        'has_scanf': has_scanf(code),
        'has_printf': has_printf(code),
        'line_count': count_lines(code),
        'function_count': count_functions(filepath),
    }

def main():
    results = []
    # Gather all files first for progress display
    all_files = []
    for root, dirs, files in os.walk(CODE_ROOT):
        for file in files:
            if file.endswith('.c') or file.endswith('.cpp'):
                all_files.append(os.path.join(root, file))
        import re
        def natural_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]
        all_files.sort(key=lambda x: natural_key(os.path.relpath(x, CODE_ROOT)))
        total = len(all_files)

    for idx, filepath in enumerate(all_files, 1):
        if idx % 100 == 0 or idx == total:
            percent = 100.0 * idx / total if total else 100.0
            print(f"Processing {idx}/{total} ({percent:.2f}%): {os.path.relpath(filepath, CODE_ROOT)}", end='\r')
        info = stat_file(filepath)
        results.append(info)
    print()  # Newline after progress

    # Output to CSV
    out_csv = os.path.join(os.path.dirname(__file__), 'stats.csv')

    # Prepare summary row for CSV
    summary_row = {}
    for field in FIELDS:
        if field == 'file':
            summary_row[field] = len(results)
        elif field in ['line_count', 'function_count']:
            summary_row[field] = sum(int(row.get(field, 0)) for row in results)
        else:
            summary_row[field] = sum(1 for row in results if row.get(field))

    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
        writer.writerow(summary_row)
    print(f'Statistics written to {out_csv}')

    # Print summary in readable form
    print("\nSummary:")
    for field in FIELDS:
        print(f"{field}: {summary_row[field]}")

if __name__ == '__main__':
    main()
