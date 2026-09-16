#!/usr/bin/env python3
# Gate for restructuring a logbook (.claude/rules/docs-style.md): run diff both ways.
"""Inventory the data tokens in a markdown logbook, or diff two files' inventories.

  docinv.py list  FILE            -> one token per line, sorted, with count
  docinv.py diff  OLD NEW         -> tokens in OLD not in NEW, each with OLD's first context line
  docinv.py lines OLD NEW         -> same, but grouped by OLD line number (for a rewrite pass)

Tokens: numbers with a unit, dates, times, commit-ish hashes, repo paths, pio envs,
board/arm/boot ids, temperatures, percentages. Normalised (µ/u, −/-, spaces).
"""
import re, sys, collections

UNIT = r'(?:mV|V|µA|uA|mA|A|mC|C|µW|uW|mW|W|ppm|ms|s|min|h|d|°C|%|kB|KB|MB|B|Hz|kHz|MHz|pF|fF|Ω|ohm|kSps|Sps|mAh|Ah|cm|mm|px|x|×|σ|days?|hours?|hrs?|minutes?|seconds?|wakes|records|rows|hourly|bytes|samples|points|erases|calls)'
NUM = r'[-+−~≈≲≳<>]?\d+(?:[.,]\d+)?'
PATTERNS = [
    ('date',  re.compile(r'\b20\d\d-\d\d-\d\d(?:[ T]\d\d:\d\d(?::\d\d)?Z?)?')),
    ('time',  re.compile(r'\b\d\d:\d\d(?::\d\d)?Z\b')),
    ('path',  re.compile(r'\b[\w][\w./-]*\.(?:md|py|c|h|hpp|cpp|bin|png|jpg|csv|ini|txt|json|sh)\b')),
    ('env',   re.compile(r'\b[a-z0-9]+(?:_[a-z0-9]+)*_(?:debug|release)\b')),
    ('hash',  re.compile(r'\b[0-9a-f]{7,10}\b(?:-dirty)?')),
    ('id',    re.compile(r'\b(?:board|arm|boot|seq|rev|phase|capture|n)\s?[#=]?\s?\d+\b', re.I)),
    ('num',   re.compile(NUM + r'\s?' + UNIT + r'\b(?![\w-])')),
    ('num',   re.compile(NUM + r'\s?' + r'(?:°C|%|µA|uA|mV|mC|ppm|σ|×|x)')),
    ('range', re.compile(NUM + r'\s?[-–.]{1,2}\s?' + NUM + r'\s?' + UNIT)),
    ('footer',re.compile(r'`#\d+ r\d+ [^`]{5,80}`')),
    ('ppm',   re.compile(r'[-+−]\d+(?:\.\d+)?\s?/\s?\d+(?:\.\d+)?d')),
]
DROP = re.compile(r'^(?:\d{1,2}\s?(?:x|×)|\d+\s?B)$')

def norm(t):
    t = t.replace('µ', 'u').replace('−', '-').replace('–', '-').replace('×', 'x').replace('≈', '~')
    t = re.sub(r'\s+', '', t)
    t = re.sub(r'^[~<>≲≳]', '', t)
    t = t.rstrip('.,;:')
    return t

def tokens(path):
    out = collections.OrderedDict()
    for ln, line in enumerate(open(path, encoding='utf-8'), 1):
        if re.match(r'\s*\|?-{3,}', line):
            continue
        for kind, rx in PATTERNS:
            for m in rx.finditer(line):
                t = norm(m.group(0))
                if not t or DROP.match(t):
                    continue
                if kind == 'hash' and (t.isdigit() or not re.search(r'[a-f]', t) or not re.search(r'\d', t)):
                    continue
                if kind == 'hash' and t in ('default', 'deadbeef'):
                    continue
                out.setdefault(t, []).append((ln, line.rstrip()))
    return out

def main():
    cmd, *args = sys.argv[1:]
    if cmd == 'list':
        for t, occ in sorted(tokens(args[0]).items()):
            print(f'{len(occ):3d}  {t}')
    elif cmd in ('diff', 'lines'):
        old, new = tokens(args[0]), tokens(args[1])
        newkeys = set(new)
        # a token also counts as present if it appears inside any new-file line verbatim
        newtext = open(args[1], encoding='utf-8').read()
        newnorm = norm(newtext.replace('\n', ' '))
        missing = {t: occ for t, occ in old.items() if t not in newkeys and t not in newnorm}
        print(f'# old tokens {len(old)}, new tokens {len(new)}, missing {len(missing)}')
        if cmd == 'diff':
            for t, occ in sorted(missing.items()):
                ln, line = occ[0]
                print(f'{t:28s}  L{ln}: {line[:110]}')
        else:
            byline = collections.defaultdict(list)
            for t, occ in missing.items():
                for ln, line in occ:
                    byline[ln].append(t)
            for ln in sorted(byline):
                print(f'L{ln}: {", ".join(sorted(byline[ln]))}')
    else:
        print(__doc__); sys.exit(2)

main()
