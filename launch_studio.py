"""Start Studio, wait for health, then open a browser; Ctrl+C stops the child."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import webbrowser


def ready(url):
    try:
        with urllib.request.urlopen(url + '/api/health', timeout=1) as response:
            return json.load(response).get('app') == 'SplintFit Studio'
    except (OSError, ValueError):
        return False


def main():
    root = Path(__file__).resolve().parent
    port = int(os.environ.get('SPLINTFIT_PORT', '8765'))
    url = f'http://127.0.0.1:{port}'
    if ready(url):
        print('Studio is already running. Close its console before testing a new version.', flush=True)
        webbrowser.open(url)
        return 0
    process = subprocess.Popen([sys.executable, str(root / 'backend/server.py')], cwd=root)
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                return process.returncode or 1
            if ready(url):
                print(f'Open {url}. Keep this console open; Ctrl+C stops Studio.', flush=True)
                webbrowser.open(url)
                return process.wait()
            time.sleep(.25)
        print('Server did not become ready. Review the error above.', flush=True)
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


if __name__ == '__main__':
    raise SystemExit(main())
