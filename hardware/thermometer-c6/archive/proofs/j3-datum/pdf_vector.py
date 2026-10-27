#!/usr/bin/env python3
"""Exact vector extraction from the HRO TYPE-C-31-M-12 datasheet PDF.

Parses the page content streams directly (no external PDF lib), composing the
full CTM stack (q/Q/cm), so every segment and every text-show is reported in
PAGE user space (points).  Also decodes text strings with their text-matrix
positions so dimension labels can be located.

Outputs a pickle + a text dump to archive/proofs/j3-datum/.
"""
import re
import sys
import zlib
import json
import math

PDF = "datasheets/HRO_TYPE-C-31-M-12_datasheet.pdf"


def content(pdf_path):
    d = open(pdf_path, "rb").read()
    out = b""
    for n in (8, 13, 20, 23):
        m = re.search((str(n) + " 0 obj").encode() + rb".*?stream\r?\n", d, re.S)
        start = m.end()
        e = d.index(b"endstream", start)
        out += zlib.decompress(d[start:e]) + b"\n"
    return out.decode("latin-1")


def mul(a, b):
    """a then b  (row-vector convention: v * a * b)."""
    return (
        a[0] * b[0] + a[1] * b[2],
        a[0] * b[1] + a[1] * b[3],
        a[2] * b[0] + a[3] * b[2],
        a[2] * b[1] + a[3] * b[3],
        a[4] * b[0] + a[5] * b[2] + b[4],
        a[4] * b[1] + a[5] * b[3] + b[5],
    )


def apply(m, x, y):
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


NUM = r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?"
TOKEN = re.compile(
    r"(?P<str>\((?:\\.|[^\\()])*\))"
    r"|(?P<hex><[0-9A-Fa-f\s]*>)"
    r"|(?P<name>/[^\s/\[\]<>(){}]*)"
    r"|(?P<num>" + NUM + r")"
    r"|(?P<arr>[\[\]])"
    r"|(?P<dict><<|>>)"
    r"|(?P<op>[A-Za-z'\"*]+)"
)


def parse(cs):
    """Return (segments, texts).

    segments: list of dicts {p0,p1, op:'L', ctm_scale, layer, closed_path_id}
    texts:    list of dicts {s, x, y, size, layer}
    """
    ctm = (1, 0, 0, 1, 0, 0)
    stack = []
    operands = []
    segs = []
    texts = []
    cur = None          # current point (user space, pre-CTM)
    startpt = None
    layer = None
    layer_stack = []
    tm = None
    tlm = None
    tf_size = 1.0
    pathid = 0
    subpaths = []       # accumulate points of current path (page space)

    for m in TOKEN.finditer(cs):
        kind = m.lastgroup
        tok = m.group()
        if kind == "num":
            operands.append(float(tok))
            continue
        if kind in ("str", "hex", "name", "arr", "dict"):
            operands.append(tok)
            continue
        op = tok
        try:
            if op == "q":
                stack.append(ctm)
            elif op == "Q":
                if stack:
                    ctm = stack.pop()
            elif op == "cm":
                a = tuple(operands[-6:])
                ctm = mul(a, ctm)
            elif op == "m":
                x, y = operands[-2:]
                cur = apply(ctm, x, y)
                startpt = cur
                pathid += 1
            elif op == "l":
                x, y = operands[-2:]
                p = apply(ctm, x, y)
                if cur is not None:
                    segs.append((cur[0], cur[1], p[0], p[1], pathid, layer))
                cur = p
            elif op in ("c", "v", "y"):
                # bezier: record endpoints only (drawing has few/none)
                pts = operands[-6:] if op == "c" else operands[-4:]
                x, y = pts[-2], pts[-1]
                p = apply(ctm, x, y)
                if cur is not None:
                    segs.append((cur[0], cur[1], p[0], p[1], pathid, layer))
                cur = p
            elif op == "h":
                if cur is not None and startpt is not None:
                    segs.append((cur[0], cur[1], startpt[0], startpt[1], pathid, layer))
                    cur = startpt
            elif op == "re":
                x, y, w, hh = operands[-4:]
                c = [apply(ctm, x, y), apply(ctm, x + w, y),
                     apply(ctm, x + w, y + hh), apply(ctm, x, y + hh)]
                pathid += 1
                for i in range(4):
                    a, b = c[i], c[(i + 1) % 4]
                    segs.append((a[0], a[1], b[0], b[1], pathid, layer))
                cur = None
            elif op == "BDC":
                layer_stack.append(layer)
                # operands like /OC /oc1
                names = [o for o in operands if isinstance(o, str) and o.startswith("/")]
                if names:
                    layer = names[-1]
            elif op == "EMC":
                layer = layer_stack.pop() if layer_stack else None
            elif op == "BT":
                tm = (1, 0, 0, 1, 0, 0)
                tlm = tm
            elif op == "ET":
                tm = None
            elif op == "Tf":
                tf_size = operands[-1] if operands else 1.0
            elif op == "Tm":
                tm = tuple(operands[-6:])
                tlm = tm
            elif op == "Td":
                tx, ty = operands[-2:]
                tlm = mul((1, 0, 0, 1, tx, ty), tlm)
                tm = tlm
            elif op == "TD":
                tx, ty = operands[-2:]
                tlm = mul((1, 0, 0, 1, tx, ty), tlm)
                tm = tlm
            elif op == "T*":
                tlm = mul((1, 0, 0, 1, 0, -tf_size), tlm)
                tm = tlm
            elif op in ("Tj", "TJ", "'", '"'):
                s = ""
                for o in operands:
                    if isinstance(o, str) and o.startswith("("):
                        s += decode_lit(o)
                    elif isinstance(o, str) and o.startswith("<"):
                        s += decode_hex(o)
                if tm is not None and s:
                    full = mul(tm, ctm)
                    x, y = full[4], full[5]
                    sc = math.hypot(full[0], full[1])
                    texts.append({"s": s, "x": x, "y": y,
                                  "size": tf_size * sc, "layer": layer,
                                  "m": full})
        except Exception:
            pass
        operands = []
    return segs, texts


def decode_lit(tok):
    body = tok[1:-1]
    out = []
    i = 0
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            n = body[i + 1]
            mapc = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f",
                    "(": "(", ")": ")", "\\": "\\"}
            if n in mapc:
                out.append(mapc[n]); i += 2; continue
            if n.isdigit():
                j = i + 1
                oct_ = ""
                while j < len(body) and len(oct_) < 3 and body[j].isdigit():
                    oct_ += body[j]; j += 1
                out.append(chr(int(oct_, 8))); i = j; continue
            out.append(n); i += 2; continue
        out.append(c); i += 1
    return "".join(out)


def decode_hex(tok):
    h = re.sub(r"\s", "", tok[1:-1])
    if len(h) % 2:
        h += "0"
    b = bytes.fromhex(h)
    # Identity-H CID font -> 2-byte codes; ASCII fonts -> 1 byte.
    try:
        return b.decode("latin-1")
    except Exception:
        return ""


if __name__ == "__main__":
    cs = content(sys.argv[1] if len(sys.argv) > 1 else PDF)
    segs, texts = parse(cs)
    print(f"segments: {len(segs)}  texts: {len(texts)}")
    xs = [s[0] for s in segs] + [s[2] for s in segs]
    ys = [s[1] for s in segs] + [s[3] for s in segs]
    print(f"bbox x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}]")
    json.dump({"segs": segs, "texts": [{k: v for k, v in t.items() if k != 'm'} | {'m': list(t['m'])} for t in texts]},
              open("archive/proofs/j3-datum/vector.json", "w"))
    print("wrote archive/proofs/j3-datum/vector.json")
