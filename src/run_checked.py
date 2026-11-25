"""Run a command and report the last output as a GitHub Actions annotation on failure."""
from collections import deque
import subprocess
import sys

if len(sys.argv) < 2:
    raise SystemExit('Usage: python src/run_checked.py COMMAND [ARG ...]')
process = subprocess.Popen(sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace', bufsize=1)
last = deque(maxlen=60)
for line in process.stdout:
    print(line, end='', flush=True)
    last.append(line)
code = process.wait()
if code:
    message=''.join(last)[-8000:].replace('%','%25').replace('\r','%0D').replace('\n','%0A')
    print(f'::error title=Command failed::{message}', flush=True)
raise SystemExit(code)
