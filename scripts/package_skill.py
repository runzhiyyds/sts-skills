"""Build a deterministic product-only skill ZIP; never scans user workspaces."""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/solve2ship'
FILES = ('SKILL.md', 'LICENSE', 'NOTICE', 'INSTALL.md', 'agents/openai.yaml', 'references/execution.md',
         'references/adapters.md', 'references/evaluation.md', 'references/delivery.md', 'scripts/evidence.py')
VERSION = '0.1.1'


def build(destination):
    destination = Path(destination)
    if destination.is_symlink(): raise ValueError('Unsafe output')
    payloads = {}
    for name in FILES:
        path = SKILL / name
        if path.is_symlink() or not path.is_file(): raise ValueError('Missing or unsafe product file')
        payloads['solve2ship/' + name] = path.read_bytes()
    manifest = {'name': 'solve2ship', 'version': VERSION, 'files_sha256': {
        path.removeprefix('solve2ship/'): hashlib.sha256(body).hexdigest() for path, body in payloads.items()}}
    payloads['solve2ship/manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path, body in sorted(payloads.items()):
            info = zipfile.ZipInfo(path, (2026, 11, 9, 0, 0, 0)); info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED; archive.writestr(info, body)
    return {'path': str(destination.resolve()), 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'version': VERSION}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, default=ROOT / 'dist/solve2ship-skill-v0.1.1.zip')
    print(json.dumps(build(parser.parse_args().output)))
