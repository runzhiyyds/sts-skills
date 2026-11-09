"""Copy the reviewed local skill folder without overwriting another installation."""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
from package_skill import FILES, SKILL


def install(parent):
    parent = Path(parent).expanduser()
    if parent.is_symlink(): raise ValueError('Do not install through a symlink')
    target = parent / 'solve2ship'
    expected = {name: hashlib.sha256((SKILL / name).read_bytes()).hexdigest() for name in FILES}
    if target.exists() or target.is_symlink():
        actual = {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file() and not p.is_symlink()}
        if not target.is_symlink() and actual == expected and not any(p.is_symlink() for p in target.rglob('*')):
            return {'status': 'already_installed', 'path': str(target)}
        raise ValueError('An existing skill differs; preserve it and review an explicit upgrade')
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.sts-install-', dir=parent) as temporary:
        stage = Path(temporary) / 'solve2ship'; stage.mkdir()
        for name in FILES:
            source = SKILL / name
            if source.is_symlink() or not source.is_file(): raise ValueError('Unsafe source')
            destination = stage / name; destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        # mkdir claims the absent destination. A racing installation is never replaced.
        target.mkdir()
        try:
            for child in stage.iterdir(): shutil.move(str(child), target / child.name)
        except BaseException:
            # Leave a partial directory visible for manual review, never overwrite/retry.
            raise
    return {'status': 'installed', 'path': str(target)}


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(); parser.add_argument('--agent', choices=('codex', 'claude'))
    parser.add_argument('--destination', type=Path, help='Parent directory in which solve2ship/ will be created')
    args = parser.parse_args()
    if args.destination is None:
        if args.agent == 'codex': args.destination = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'skills'
        elif args.agent == 'claude': args.destination = Path.home() / '.claude/skills'
        else: parser.error('Choose an agent or an explicit skill-directory destination')
    try: print(json.dumps(install(args.destination)))
    except (ValueError, OSError) as error: raise SystemExit(str(error)) from None
