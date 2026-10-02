"""Create a portable ShareCircle ZIP without runtime/cache artifacts."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'sharecircle.zip'
EXCLUDED_DIRS = {'.git', '.venv', 'venv', '__pycache__'}
EXCLUDED_SUFFIXES = {'.db', '.zip', '.pyc'}


def include(path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return False
    if path.is_file() and path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


def main():
    files = sorted(path for path in ROOT.rglob('*') if include(path))
    with ZipFile(OUTPUT, 'w', compression=ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
    print(f'Created {OUTPUT} with {len(files)} files.')


if __name__ == '__main__':
    main()
