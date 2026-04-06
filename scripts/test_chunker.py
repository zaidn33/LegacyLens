import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.chunker import extract_global_context, extract_logic_chunks

source = open('samples/sample.cbl', 'r').read()

gc = extract_global_context(source)
print(f"Global Context: {len(gc)} chars, {len(gc.splitlines())} lines")
if gc:
    print(f"  First line: {gc.splitlines()[0].strip()}")
    print(f"  Last line:  {gc.splitlines()[-1].strip()}")
print()

chunks = extract_logic_chunks(source)
print(f"Logic Chunks: {len(chunks)}")
for i, c in enumerate(chunks):
    lines = c.splitlines()
    first = lines[0].strip()[:60] if lines else "(empty)"
    print(f"  Chunk {i+1}: {len(lines)} lines | {first}")
