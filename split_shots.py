"""
split_shots.py — Split xeb_full_shots.txt into <25MB GitHub-friendly chunks.
Run from inside the XEB/ folder:
    python3 split_shots.py
"""
import os

INPUT   = "xeb_full_shots.txt"
MAX_MB  = 20          # stay well under GitHub's 25MB limit
MAX_BYTES = MAX_MB * 1024 * 1024

def split():
    if not os.path.exists(INPUT):
        print(f"[ERROR] {INPUT} not found. Run alg12_xeb_1m.py first.")
        return

    size = os.path.getsize(INPUT)
    print(f"Input: {INPUT}  ({size/1024/1024:.1f} MB)")

    # Read header lines (start with '#')
    with open(INPUT, "r") as f:
        lines = f.readlines()

    header = [l for l in lines if l.startswith("#")]
    data   = [l for l in lines if not l.startswith("#")]
    print(f"Header lines: {len(header)} | Data lines (shots): {len(data)}")

    chunk_idx   = 1
    chunk_lines = []
    chunk_bytes = sum(len(h.encode()) for h in header)
    written     = 0

    def write_chunk(idx, hdr, body):
        fname = f"xeb_full_shots_part{idx:02d}.txt"
        with open(fname, "w") as f:
            f.writelines(hdr)
            f.write(f"# Part {idx}\n")
            f.writelines(body)
        sz = os.path.getsize(fname)
        print(f"  Wrote {fname}  ({sz/1024/1024:.1f} MB, {len(body)} shots)")

    for line in data:
        lb = len(line.encode())
        if chunk_bytes + lb > MAX_BYTES and chunk_lines:
            write_chunk(chunk_idx, header, chunk_lines)
            written += len(chunk_lines)
            chunk_idx  += 1
            chunk_lines = []
            chunk_bytes = sum(len(h.encode()) for h in header)
        chunk_lines.append(line)
        chunk_bytes += lb

    if chunk_lines:
        write_chunk(chunk_idx, header, chunk_lines)
        written += len(chunk_lines)

    print(f"\nDone. {chunk_idx} chunk(s) written, {written} shots total.")
    print("You can now delete xeb_full_shots.txt and push the parts to GitHub.")

if __name__ == "__main__":
    split()
