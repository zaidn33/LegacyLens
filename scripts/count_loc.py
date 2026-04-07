import os

def count_loc():
    exclude_dirs = {'.git', 'node_modules', '.next', 'venv', 'env', 'runs', 'output', '.claude', '.vscode', '__pycache__'}
    extensions = {'.py', '.js', '.ts', '.tsx', '.css', '.html', '.cbl', '.cpy', '.yml', '.yaml', '.sql'}
    
    stats = {} # {ext: {'files': 0, 'lines': 0}}
    
    for root, dirs, files in os.walk('.'):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in extensions:
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                        if ext not in stats:
                            stats[ext] = {'files': 0, 'lines': 0}
                        stats[ext]['files'] += 1
                        stats[ext]['lines'] += lines
                except Exception:
                    continue

    print(f"{'Language':<15} {'Files':<10} {'Lines':<10}")
    print("-" * 35)
    total_files = 0
    total_lines = 0
    for ext, data in sorted(stats.items(), key=lambda x: x[1]['lines'], reverse=True):
        lang = ext[1:].upper() if ext else "Other"
        print(f"{lang:<15} {data['files']:<10} {data['lines']:<10}")
        total_files += data['files']
        total_lines += data['lines']
    print("-" * 35)
    print(f"{'SUM:':<15} {total_files:<10} {total_lines:<10}")

if __name__ == "__main__":
    count_loc()
