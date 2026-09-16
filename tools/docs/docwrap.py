#!/usr/bin/env python3
"""Check or fix paragraph wrapping in a markdown doc (.claude/rules/docs-style.md).

  docs/docwrap.py check FILE...           -> lines over WIDTH+20, ragged paragraphs, links or
                                        code spans split across lines; exit 1 if any
  docs/docwrap.py fix   FILE[:START]...   -> reflow the offending paragraphs and list items at
                                        WIDTH, whitespace only; START skips earlier lines

Never touched: tables, headings, code fences, image lines, blocks of one-word lines.
Links `[text](url)` and code spans `...` are never split; a span longer than WIDTH
stays on its own line. A block with an unpaired backtick is reported, not reflowed.
"""
import re, sys, textwrap

WIDTH = 80
NB = '⁠'  # placeholder for spaces inside links and code spans

def protect(t):
    t = re.sub(r'\[[^\]]*\]\([^)]*\)', lambda m: m.group(0).replace(' ', NB), t)
    t = re.sub(r'`[^`]*`', lambda m: m.group(0).replace(' ', NB), t)
    return t

def prose(l):
    return bool(l.strip()) and l == l.lstrip() and not re.match(r'(- |\* |> |#|\||!\[)', l) \
        and not l.startswith('```')

ITEM = re.compile(r'^( *)([-*] )')

def item(l): return ITEM.match(l) is not None

def cont(l, indent):
    """A continuation of a list item: indented past its marker and not a marker itself."""
    return l.strip() != '' and l.startswith(' ' * indent) and not ITEM.match(l)

def blocks(lines, start):
    """Yield (i, j, kind) for prose paragraphs and list items; kind '' or '- '."""
    i = 0; fence = False
    while i < len(lines):
        l = lines[i]
        if l.startswith('```'): fence = not fence
        if fence or i + 1 < start:
            i += 1; continue
        if prose(l):
            j = i
            while j < len(lines) and prose(lines[j]): j += 1
            yield i, j, ''
        elif item(l):
            m = ITEM.match(l); indent = len(m.group(0))
            j = i + 1
            while j < len(lines) and cont(lines[j], indent): j += 1
            yield i, j, m.group(0)
        else:
            j = i + 1
        i = j

def split_span(l): return l.count('`') % 2 == 1 or re.search(r'\[[^\]]*$', l) is not None

def first_token(l):
    """Length of the first unbreakable unit on a line (a whole link or code span)."""
    return len(protect(l).split()[0]) if l.strip() else 0

def problems(block, kind):
    over = [l for l in block if len(l) > WIDTH + 20 and not re.search(r'https?://|\]\(', l)
            and not (l.startswith('`') and l.rstrip().endswith('`') and l.count('`') == 2)]
    # a short line is ragged only if the next line's first unit would have fitted on it
    ragged = kind == '' and len(block) > 1 and all(len(l.split()) >= 3 for l in block) and any(
        len(a) < WIDTH - 35 and len(a) + 1 + first_token(b) <= WIDTH for a, b in zip(block, block[1:]))
    split = any(split_span(l) for l in block)
    return over, ragged, split

def check(path):
    lines = open(path).read().split('\n'); bad = 0
    for i, j, kind in blocks(lines, 1):
        over, ragged, split = problems(lines[i:j], kind)
        for l in over: print(f'{path}:{lines.index(l, i)+1}: over {len(l)} cols'); bad += 1
        if ragged: print(f'{path}:{i+1}: ragged paragraph'); bad += 1
        if split: print(f'{path}:{i+1}: link or code span split across lines'); bad += 1
    return bad

def fix(path, start):
    lines = open(path).read().split('\n'); out = []; last = 0; n = 0
    for i, j, kind in blocks(lines, start):
        out.extend(lines[last:i]); last = j
        block = lines[i:j]
        over, ragged, split = problems(block, kind)
        text = ' '.join(x.strip() for x in block)
        if kind: text = text[len(kind.strip()) + 1:]
        if (over or ragged or split) and text.count('`') % 2 == 0:
            new = textwrap.wrap(protect(text), WIDTH, initial_indent=kind, subsequent_indent=' ' * len(kind),
                                break_long_words=False, break_on_hyphens=False)
            out.extend(w.replace(NB, ' ') for w in new); n += 1
        else:
            if over or ragged or split: print(f'{path}:{i+1}: unpaired backtick, left as is')
            out.extend(block)
    out.extend(lines[last:])
    open(path, 'w').write('\n'.join(out))
    return n

def main():
    if len(sys.argv) < 3: print(__doc__); sys.exit(2)
    cmd, *args = sys.argv[1:]
    if cmd == 'check':
        sys.exit(1 if sum(check(p) for p in args) else 0)
    elif cmd == 'fix':
        for spec in args:
            p, _, s = spec.partition(':')
            print(f'{p}: {fix(p, int(s or 1))} blocks reflowed')
    else:
        print(__doc__); sys.exit(2)

main()
