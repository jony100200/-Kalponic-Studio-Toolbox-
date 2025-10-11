import os
import re
import argparse
from typing import Iterable, List, Tuple


DEFAULT_SEPARATORS = ['_', '-', '.', ' ']  # separators to consider when matching suffixes


def remove_suffix(name: str, suffixes: Iterable[str], separators: Iterable[str] = DEFAULT_SEPARATORS, case_insensitive: bool = True) -> str:
    """Remove any of the provided suffixes from the end of `name`.

    Behavior and contract:
    - Only removes a suffix if it appears at the very end of the base name (before extension).
    - Suffixes may be prefixed by one of the provided separators; the separator will also be removed.
    - Matching is optionally case-insensitive.
    - If multiple suffixes match, the longest matching suffix is removed (greedy by suffix length).

    Examples:
    - name='model_01', suffixes=['01'] -> 'model'
    - name='model-v02', suffixes=['v02','02'] -> 'model' (v02 matches)

    Args:
        name: base filename (without extension)
        suffixes: iterable of suffix strings to remove (like '01', 'v1', 'low', 'thumb')
        separators: separators that may appear before the suffix (e.g. '_', '-', '.', ' ')
        case_insensitive: whether to match suffixes case-insensitively

    Returns:
        The name with the suffix removed if a match was found, otherwise the original name.
    """
    if case_insensitive:
        cmp_name = name.lower()
        suffix_list = sorted((s.lower() for s in suffixes), key=len, reverse=True)
    else:
        cmp_name = name
        suffix_list = sorted(suffixes, key=len, reverse=True)

    # Try each separator and each suffix (longest suffixes first)
    for suf in suffix_list:
        for sep in separators:
            candidate = sep + suf
            if cmp_name.endswith(candidate):
                # remove the separator + suffix from the original name preserving case
                return name[: -len(candidate)]
        # Also allow the suffix to appear without a separator (e.g. 'model1')
        if cmp_name.endswith(suf):
            return name[: -len(suf)]

    return name


def collect_suffixes_from_args(s: str) -> List[str]:
    # split comma/semicolon separated user input into suffix list
    parts = re.split(r'[;,\s]+', s.strip())
    return [p for p in parts if p]


def rename_local_files(folder_path: str, suffixes: Iterable[str], separators: Iterable[str] = DEFAULT_SEPARATORS, dry_run: bool = True, case_insensitive: bool = True) -> List[Tuple[str, str]]:
    """Rename files in folder_path by removing suffixes from their base names.

    Returns list of tuples (old_name, new_name) for changes that would be or were made.
    """
    changed = []
    for filename in os.listdir(folder_path):
        # skip directories
        full_path = os.path.join(folder_path, filename)
        if os.path.isdir(full_path):
            continue

        name, ext = os.path.splitext(filename)
        new_base = remove_suffix(name, suffixes, separators, case_insensitive)
        new_name = new_base + ext
        if new_name != filename:
            changed.append((filename, new_name))
            if not dry_run:
                src = os.path.join(folder_path, filename)
                dst = os.path.join(folder_path, new_name)
                os.rename(src, dst)
    return changed


def auto_detect_suffixes(folder_path: str, separators: Iterable[str] = DEFAULT_SEPARATORS, min_count: int = 2, min_ratio: float = 0.05, max_tokens: int = 3) -> List[str]:
    """Auto-detect common trailing token sequences across filenames in folder_path.

    Approach:
    - Split base names on separators into tokens (lowercased).
    - Consider trailing sequences of 1..max_tokens tokens as candidates.
    - Count how many files end with each candidate.
    - Return candidates that meet min_count and min_ratio thresholds, sorted by count desc and length desc.
    """
    counts = {}
    total = 0
    sep_pattern = '[' + re.escape(''.join(separators)) + ']' if separators else r'\s+'
    for filename in os.listdir(folder_path):
        full = os.path.join(folder_path, filename)
        if os.path.isdir(full):
            continue
        name, _ = os.path.splitext(filename)
        total += 1
        # split into tokens by separators
        tokens = re.split(sep_pattern, name.lower())
        tokens = [t for t in tokens if t]
        if not tokens:
            continue
        for k in range(1, min(max_tokens, len(tokens)) + 1):
            candidate = '_'.join(tokens[-k:])
            counts[candidate] = counts.get(candidate, 0) + 1

    if total == 0:
        return []

    # select candidates meeting thresholds
    threshold = max(min_count, int(total * min_ratio))
    candidates = [(c, cnt) for c, cnt in counts.items() if cnt >= threshold]
    # sort by count desc then token length desc (prefer longer sequences)
    candidates.sort(key=lambda x: ( -x[1], -len(x[0]) ))
    return [c for c, _ in candidates]


def main():
    parser = argparse.ArgumentParser(description='Remove configured suffixes from filenames in a folder (non-recursive).')
    parser.add_argument('--path', '-p', default=os.path.dirname(os.path.abspath(__file__)), help='Target folder (default: script folder)')
    parser.add_argument('--suffixes', '-s', required=False, help="Comma/space-separated list of suffixes to remove (e.g. '01,_low,thumb'). If omitted, the script will try to auto-detect common trailing tokens and numeric patterns.")
    parser.add_argument('--separators', help="Optional list of separators to consider (default: '_ - . space'). Provide them as a continuous string, e.g. '_-. '" )
    parser.add_argument('--dry-run', action='store_true', help='Preview renames without applying them (default: apply immediately).')
    parser.add_argument('--case-sensitive', dest='case_sensitive', action='store_true', help='Make suffix matching case-sensitive.')
    args = parser.parse_args()

    # resolve separators list
    separators = list(args.separators) if args.separators is not None else DEFAULT_SEPARATORS

    # determine suffixes: explicit or auto-detected or fallback
    if args.suffixes:
        suffixes = collect_suffixes_from_args(args.suffixes)
    else:
        detected = auto_detect_suffixes(args.path, separators)
        if detected:
            print('Auto-detected common trailing tokens (will try removing):', ', '.join(detected))
            suffixes = detected
        else:
            suffixes = ['thumb', 'low', 'cleaned', 'clean']
            print('No --suffixes and no strong auto-detection; using safe defaults:', ', '.join(suffixes))

    # collect planned changes (preview always first)
    changes = rename_local_files(args.path, suffixes, separators, dry_run=True, case_insensitive=not args.case_sensitive)

    # additionally collect numeric suffix patterns iteratively when suffixes were not explicitly provided
    if not args.suffixes:
        print('Also checking numeric suffix patterns like "_123", "(123)", or " 123" where present.')
        for filename in os.listdir(args.path):
            full = os.path.join(args.path, filename)
            if os.path.isdir(full):
                continue
            name, ext = os.path.splitext(filename)
            new_base = name
            while True:
                candidate = re.sub(r'(_\d+|\s*\(\d+\)|\s+\d+)$', '', new_base)
                if candidate == new_base:
                    break
                new_base = candidate
            new_name = new_base + ext
            if new_name != filename and (filename, new_name) not in changes:
                changes.append((filename, new_name))

    if not changes:
        print('No files would be changed.')
        return

    print('\nPlanned renames:')
    for old, new in changes:
        print(f"  {old} -> {new}")

    if args.dry_run:
        print('\nDry-run mode (no files changed).')
        return

    # Apply immediately: write undo log then rename
    undo_log_path = os.path.join(args.path, 'remove_suffix_undo.csv')
    try:
        with open(undo_log_path, 'w', encoding='utf-8') as f:
            f.write('old_name,new_name\n')
            for old, new in changes:
                f.write(f'"{old}","{new}"\n')
    except Exception as e:
        print(f'Warning: could not write undo log to {undo_log_path}: {e}')

    print('\nApplying renames now... (undo log saved at ' + undo_log_path + ')')
    for old, new in changes:
        src = os.path.join(args.path, old)
        dst = os.path.join(args.path, new)
        try:
            if not os.path.exists(src):
                print(f"Skipping {old}: source no longer exists")
                continue
            if os.path.exists(dst):
                print(f"Skipping {old}: destination {new} already exists")
                continue
            os.rename(src, dst)
            print(f"Renamed: {old} -> {new}")
        except Exception as e:
            print(f"Failed to rename {old} -> {new}: {e}")


if __name__ == '__main__':
    main()
