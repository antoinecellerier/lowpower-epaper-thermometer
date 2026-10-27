#!/usr/bin/env python3
"""Minimal STEP AP214 entity parser + helpers shared by the J3 land analysis.

Not a CAD kernel: it reads the flat entity table, resolves references, and
exposes (a) the gold-coloured geometry, (b) ADVANCED_FACEs with their surface
type / plane origin / plane normal, and (c) each face's vertex point cloud.
That is enough to isolate a *flat, planar, board-contacting* face without
guessing at anything.
"""
import re
import numpy as np

STEP = "local.3dmodels/USB_C_Receptacle_HRO_TYPE-C-31-M-12.step"

ENT_RE = re.compile(r"#(\d+)\s*=\s*(.*?);", re.S)
REF_RE = re.compile(r"#(\d+)")
NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[EeDd][-+]?\d+)?")


class Step:
    def __init__(self, path=STEP):
        self.raw = open(path, encoding="latin-1").read()
        self.ent = {}
        self.kind = {}
        for m in ENT_RE.finditer(self.raw):
            i, body = int(m.group(1)), m.group(2)
            self.ent[i] = body
            k = re.match(r"\s*([A-Z_0-9]+)\s*\(", body)
            self.kind[i] = k.group(1) if k else "COMPLEX"
        self.refs = {i: [int(x) for x in REF_RE.findall(b)]
                     for i, b in self.ent.items()}
        # cartesian points
        self.pt = {}
        for i, b in self.ent.items():
            if self.kind[i] == "CARTESIAN_POINT":
                n = NUM_RE.findall(b[b.index("(", b.index(",")):])
                if len(n) >= 3:
                    self.pt[i] = np.array([float(x) for x in n[:3]])
        self.dir = {}
        for i, b in self.ent.items():
            if self.kind[i] == "DIRECTION":
                n = NUM_RE.findall(b[b.index("(", b.index(",")):])
                if len(n) >= 3:
                    self.dir[i] = np.array([float(x) for x in n[:3]])

    def walk(self, root, want=None, seen=None):
        """Collect all descendant entity ids (optionally of a given kind)."""
        seen = seen if seen is not None else set()
        st, out = [root], []
        while st:
            n = st.pop()
            if n in seen:
                continue
            seen.add(n)
            if want is None or self.kind.get(n) == want:
                out.append(n)
            st.extend(c for c in self.refs.get(n, ()) if c not in seen)
        return out

    # --- colour -----------------------------------------------------------
    def colour_of(self, i):
        b = self.ent[i]
        m = re.match(r"\s*COLOUR_RGB\s*\(\s*'[^']*'\s*,\s*([-+0-9.Ee]+)\s*,"
                     r"\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)", b)
        return tuple(map(float, m.groups())) if m else None

    def styled_items(self):
        """[(styled_item_id, rgb_or_None, geometry_root_id)]"""
        out = []
        for i, b in self.ent.items():
            if not b.strip().startswith("STYLED_ITEM"):
                continue
            r = self.refs[i]
            if not r:
                continue
            rgb = None
            for s in r[:-1]:
                for c in self.walk(s):
                    cc = self.colour_of(c) if self.kind.get(c) == "COLOUR_RGB" else None
                    if cc:
                        rgb = cc
                        break
                if rgb:
                    break
            out.append((i, rgb, r[-1]))
        return out

    # --- faces ------------------------------------------------------------
    def face_info(self, fid):
        """ADVANCED_FACE -> dict(surface kind, plane origin/normal, verts)."""
        b = self.ent[fid]
        r = self.refs[fid]
        surf = r[-1]
        sk = self.kind.get(surf, "?")
        origin = normal = None
        if sk == "PLANE":
            ax = self.refs[surf][0]           # AXIS2_PLACEMENT_3D
            ar = self.refs[ax]
            origin = self.pt.get(ar[0])
            if len(ar) > 1:
                normal = self.dir.get(ar[1])
        verts = [self.pt[v] for f in self.walk(fid, "VERTEX_POINT")
                 for v in self.refs[f] if v in self.pt]
        return dict(id=fid, surf=sk, origin=origin, normal=normal,
                    verts=np.array(verts) if verts else np.zeros((0, 3)))
