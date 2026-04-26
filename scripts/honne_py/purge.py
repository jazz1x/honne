import shutil
import sys
from pathlib import Path


def purge(all_: bool = False, keep_assets: bool = False, force: bool = False) -> int:
    """Purge .honne cache in current working directory."""
    if not (all_ or keep_assets):
        print("error: required: --all or --keep-assets", file=sys.stderr)
        return 1

    honne_dir = Path.cwd() / ".honne"

    if not honne_dir.exists():
        print("Nothing to purge")
        return 0

    if honne_dir.is_symlink():
        print("error: .honne is a symlink — refusing to delete", file=sys.stderr)
        return 1

    # Confirm deletion
    if not force:
        sys.stdout.write("Delete .honne? Type 'DELETE' to confirm: ")
        sys.stdout.flush()
        response = sys.stdin.readline().strip()
        if response != "DELETE":
            print("error: aborted — .honne not deleted", file=sys.stderr)
            return 1

    # Purge
    if all_:
        shutil.rmtree(honne_dir)
    elif keep_assets:
        for item in honne_dir.iterdir():
            if item.name != "assets":
                if item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--keep-assets", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    sys.exit(purge(args.all, args.keep_assets, args.force))
