#!/usr/bin/env python3
"""Check an STL is actually printable: closed, consistently wound, no degenerate faces.

A slicer will happily accept a mesh with holes and produce something that looks fine in
preview and prints as a shell with a missing wall. A propeller blade is exactly the shape
that provokes it -- thin sections, a square tip, a sharp trailing edge.

    python3 cad/tools/check_stl.py my_propeller.stl
    python3 cad/tools/check_stl.py build/*.stl

What it checks:
  closed          every edge is shared by exactly two triangles
  winding         each shared edge runs in opposite directions in its two triangles
  degenerate      no zero-area triangles
  volume          signed volume via the divergence theorem; negative means inside out

Standard library only, so it runs anywhere. Binary STL only, which is what this
repository's exporters write.
"""
import collections, math, os, struct, sys


def read_binary_stl(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 84:
        raise ValueError("file is too short to be a binary STL")
    if data[:5].lower().lstrip() == b"solid" and b"facet" in data[:512]:
        raise ValueError("this looks like an ASCII STL; only binary is supported")
    n = struct.unpack("<I", data[80:84])[0]
    if len(data) != 84 + n * 50:
        raise ValueError(f"header says {n} triangles, which does not match the file size")
    tris = []
    for i in range(n):
        off = 84 + i * 50
        v = struct.unpack("<12f", data[off:off + 48])
        tris.append((v[3:6], v[6:9], v[9:12]))
    return tris


def check(path):
    try:
        tris = read_binary_stl(path)
    except (OSError, ValueError) as e:
        print(f"  x cannot read: {e}")
        return False

    # Quantise to 1 nm so that vertices meant to be identical compare equal.
    q = lambda p: (round(p[0], 6), round(p[1], 6), round(p[2], 6))
    edges = collections.Counter()
    directed = collections.Counter()
    degenerate = 0
    vol2 = 0.0

    for a, b, c in tris:
        qa, qb, qc = q(a), q(b), q(c)
        if qa == qb or qb == qc or qc == qa:
            degenerate += 1
            continue
        # twice the signed volume of the tetrahedron to the origin
        vol2 += (qa[0]*(qb[1]*qc[2] - qb[2]*qc[1])
                 - qa[1]*(qb[0]*qc[2] - qb[2]*qc[0])
                 + qa[2]*(qb[0]*qc[1] - qb[1]*qc[0]))
        for u, v in ((qa, qb), (qb, qc), (qc, qa)):
            edges[frozenset((u, v))] += 1
            directed[(u, v)] += 1

    open_edges = [e for e, k in edges.items() if k != 2]
    # A consistently wound closed mesh traverses every edge once in each direction.
    flipped = [e for e, k in directed.items() if k > 1]

    volume = vol2 / 6.0
    ok = not open_edges and not flipped and not degenerate and volume > 0

    print(f"  triangles   {len(tris)}")
    print(f"  closed      {'yes' if not open_edges else f'NO - {len(open_edges)} edge(s) not shared by exactly 2 triangles'}")
    print(f"  winding     {'consistent' if not flipped else f'INCONSISTENT - {len(flipped)} edge(s) traversed twice the same way'}")
    print(f"  degenerate  {degenerate}")
    print(f"  volume      {volume:.1f} mm3" + ("" if volume > 0 else "   <-- NEGATIVE: normals point inward"))
    return ok


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    bad = 0
    for path in argv:
        # Print the path as given: relpath mangles anything outside the repo
        # into a row of '../..'.
        print(path)
        if not check(path):
            bad += 1
        print()
    if bad:
        print(f"{bad} of {len(argv)} file(s) FAILED")
        return 1
    print(f"all {len(argv)} file(s) pass")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
