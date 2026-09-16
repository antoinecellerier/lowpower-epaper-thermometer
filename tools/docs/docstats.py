#!/usr/bin/env python3
"""Size and readability figures for markdown docs, optionally before/after two revisions.

  docs/docstats.py FILE...                    -> current working-tree figures
  docs/docstats.py -b REV [-c REV] FILE...    -> REV -> REV (default second REV: working tree)
  docs/docstats.py --tree [-b REV] [-c REV]   -> docs/ layout: files in root and archive/,
                                                 loose images, docs with no inbound link

Per file: lines, KB, prose words, words per sentence, dash-as-parenthesis asides
(" — "), table cells over 200 characters. Prose excludes tables, headings, code
fences and image lines. Run from the repo root.
"""
import re, subprocess, sys, argparse

LONG_CELL = 200

def text(rev, path):
    if rev is None:
        return open(path, encoding='utf-8').read()
    r = subprocess.run(['git', 'show', f'{rev}:{path}'], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ''

def stats(s):
    fence = False; prose = []; cells = []
    lines = s.split('\n')
    for l in lines:
        if l.startswith('```'): fence = not fence; continue
        if fence: continue
        if l.startswith('|') and not re.match(r'\|\s*-', l):
            cells += [len(c.strip()) for c in l.strip('|').split('|')]
        elif l.strip() and not l.startswith(('#', '!')):
            prose.append(l)
    sents = re.findall(r'[^.!?]+[.!?]', ' '.join(prose))
    return dict(
        lines=len(lines), kb=len(s.encode()) / 1024,
        words=sum(len(l.split()) for l in prose),
        wps=(sum(len(x.split()) for x in sents) / len(sents)) if sents else 0.0,
        dashes=sum(l.count(' — ') for l in prose),
        longcells=sum(1 for c in cells if c > LONG_CELL))

COLS = [('lines', 'lines', '{:d}'), ('kb', 'KB', '{:.0f}'), ('words', 'prose words', '{:d}'),
        ('wps', 'words/sent', '{:.1f}'), ('dashes', 'dash asides', '{:d}'), ('longcells', f'cells>{LONG_CELL}', '{:d}')]

def cell(a, b, fmt):
    return fmt.format(a) if b is None else f'{fmt.format(a)}->{fmt.format(b)}'

def ls(rev, path):
    if rev is None:
        r = subprocess.run(['git', 'ls-files', path], capture_output=True, text=True)
    else:
        r = subprocess.run(['git', 'ls-tree', '-r', '--name-only', rev, path], capture_output=True, text=True)
    return [x for x in r.stdout.split('\n') if x]

def tree(rev):
    files = ls(rev, 'docs/')
    root_md = [f for f in files if f.count('/') == 1 and f.endswith('.md')]
    arch_md = [f for f in files if f.startswith('docs/archive/') and f.endswith('.md')]
    root_img = [f for f in files if f.count('/') == 1 and re.search(r'\.(png|jpg)$', f)]
    orphans = 0
    for f in root_md + arch_md:
        if f.endswith('README.md'): continue
        base = f.rsplit('/', 1)[1]
        cmd = ['git', 'grep', '-l', '-F', base] + ([rev] if rev else []) + ['--', ':!hardware', f':!{f}']
        if not subprocess.run(cmd, capture_output=True, text=True).stdout.strip(): orphans += 1
    return dict(root_md=len(root_md), archive_md=len(arch_md), root_images=len(root_img), no_inbound_link=orphans)

def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('-b', '--base'); ap.add_argument('-c', '--compare'); ap.add_argument('--tree', action='store_true')
    ap.add_argument('files', nargs='*')
    a = ap.parse_args()
    if not a.files and not a.tree: print(__doc__); sys.exit(2)
    if a.tree:
        before = tree(a.base) if a.base else None; after = tree(a.compare)
        for k, v in after.items():
            print(f'{k:18s} {cell(before[k], v, "{:d}") if before else v}')
        if not a.files: return
    fmtw = 34
    print(f'{"file":{fmtw}s} ' + ' '.join(f'{h:>14s}' for _, h, _ in COLS))
    for f in a.files:
        after = stats(text(a.compare, f)); before = stats(text(a.base, f)) if a.base else None
        row = [cell(before[k], after[k], fmt) if before else fmt.format(after[k]) for k, _, fmt in COLS]
        print(f'{f:{fmtw}s} ' + ' '.join(f'{c:>14s}' for c in row))

main()
