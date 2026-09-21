#!/usr/bin/env python3
"""Put the Blue Robotics M200 motor STEP where the toroidal-thruster build expects it.

The M200 CAD is Blue Robotics' file, published by them for their customers. This
repository does not redistribute it: it is 5.7 MB of someone else's binary, and vendor
CAD is not ours to relicense. Same policy as SVA's PPTC geometry, which
cad/underwater/controllable-pitch/fetch-geometry.sh fetches the same way.

    python3 projects/toroidal-rov-thruster/fetch_m200_cad.py --from-zip ~/Downloads/M200_STANDARD_BR-101376_PUBLIC.zip
    python3 projects/toroidal-rov-thruster/fetch_m200_cad.py --from-step ~/Downloads/M200.STEP
    python3 projects/toroidal-rov-thruster/fetch_m200_cad.py --url https://...          # if you have a direct link

Nothing here guesses a download URL. Blue Robotics reorganises their CAD downloads, and a
stale URL baked into a repository is worse than no URL: it fails in a way that looks like
your fault. Get the file from the product page, then point this script at it.

YOU DO NOT NEED THIS FILE to build the thruster. Without it, source/hardware.py falls back
to parametric_m200() -- a model built from the dimensions in source/parameters.json -- and
source/motor_step.py records "VENDOR STEP UNAVAILABLE: parametric M200 model used;
interface not cross-checked". You get the geometry. What you lose is the cross-check of
this repo's numbers against the vendor's own solid, which is the whole point of having it.
"""
import argparse, os, shutil, sys, zipfile
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
DEST_DIR = os.path.normpath(os.path.join(
    HERE, "toroidal_rov_prototype2A", "thruster_proto2A", "hardware", "vendor"))
DEST = os.path.join(DEST_DIR, "M200_STANDARD_BR-101376_PUBLIC.STEP")

PRODUCT_PAGE = "https://bluerobotics.com/store/thrusters/motors/m200-motor-r1/"
MIN_BYTES = 1_000_000          # the real file is about 5.7 MB; a 404 page is not

WHERE_TO_GET_IT = f"""
Where to get the file
---------------------
  1. Open the Blue Robotics M200 product page:
         {PRODUCT_PAGE}
  2. Find the CAD / technical details download (the M200 STANDARD, part BR-101376).
  3. Download it, then re-run this script pointing at what you downloaded:

         python3 projects/toroidal-rov-thruster/fetch_m200_cad.py --from-zip  <the .zip you downloaded>
         python3 projects/toroidal-rov-thruster/fetch_m200_cad.py --from-step <the .STEP you downloaded>

Blue Robotics' terms apply to their file. Do not commit it to this repository -- the
vendor/ folder is gitignored so that accident cannot happen.
""".rstrip()


def looks_like_step(path):
    """A STEP file starts with ISO-10303-21. Catches an HTML error page saved as .STEP."""
    try:
        with open(path, "rb") as f:
            return f.read(13).startswith(b"ISO-10303-21")
    except OSError:
        return False


def verify(path):
    size = os.path.getsize(path)
    if not looks_like_step(path):
        sys.exit(f"ERROR: {path} does not start with ISO-10303-21, so it is not a STEP "
                 f"file. A download error page saved under a .STEP name looks exactly "
                 f"like this.")
    if size < MIN_BYTES:
        sys.exit(f"ERROR: {path} is only {size/1e6:.2f} MB. The M200 STEP is about "
                 f"5.7 MB, so this is probably a partial download.")
    return size


def record_source(origin):
    """Leave a note saying where this copy came from. Untracked, but the habit matters."""
    with open(os.path.join(DEST_DIR, "SOURCE.txt"), "w") as f:
        f.write(f"Blue Robotics M200 STANDARD (BR-101376)\n"
                f"Obtained from: {origin}\n"
                f"On: {date.today().isoformat()}\n"
                f"Vendor's file, under Blue Robotics' terms. Not redistributed by this\n"
                f"repository.\n")


def from_zip(src):
    with zipfile.ZipFile(src) as z:
        names = [n for n in z.namelist() if n.upper().endswith((".STEP", ".STP"))]
        if not names:
            sys.exit(f"ERROR: no .STEP or .STP inside {src}. It holds: "
                     f"{', '.join(z.namelist()[:8]) or '(nothing)'}")
        if len(names) > 1:
            print(f"note: {len(names)} STEP files inside; taking {names[0]}")
        with z.open(names[0]) as fin, open(DEST, "wb") as fout:
            shutil.copyfileobj(fin, fout)
    return f"{os.path.abspath(src)} (zip)"


def from_url(url):
    import urllib.request
    print(f"fetching {url}")
    tmp = DEST + ".part"
    try:
        with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
    except Exception as e:                       # noqa: BLE001 - report and stop
        if os.path.exists(tmp):
            os.remove(tmp)
        sys.exit(f"ERROR: download failed: {e}\n{WHERE_TO_GET_IT}")
    if zipfile.is_zipfile(tmp):
        os.replace(tmp, tmp + ".zip")
        from_zip(tmp + ".zip")
        os.remove(tmp + ".zip")
    else:
        os.replace(tmp, DEST)
    return url


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--from-zip", help="a .zip you downloaded from Blue Robotics")
    g.add_argument("--from-step", help="a .STEP you downloaded from Blue Robotics")
    g.add_argument("--url", default=os.environ.get("M200_STEP_URL"),
                   help="direct download URL (or set M200_STEP_URL)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing copy")
    a = ap.parse_args()

    if os.path.exists(DEST) and not a.force:
        print(f"have    {DEST}  ({os.path.getsize(DEST)/1e6:.1f} MB)")
        print("        --force to replace it")
        return 0

    if not (a.from_zip or a.from_step or a.url):
        print("No source given, and no copy in hardware/vendor/.")
        print(WHERE_TO_GET_IT)
        return 2

    # Only now, when there is something to write, create the folder. Creating it earlier
    # left an empty tree behind that a later `git mv` moved the whole project into.
    os.makedirs(DEST_DIR, exist_ok=True)

    if a.from_zip:
        origin = from_zip(a.from_zip)
    elif a.from_step:
        shutil.copyfile(a.from_step, DEST)
        origin = os.path.abspath(a.from_step)
    else:
        origin = from_url(a.url)

    size = verify(DEST)
    record_source(origin)
    print(f"wrote   {DEST}  ({size/1e6:.1f} MB)")
    print("Now re-run the build to pick up the cross-check:")
    print("    python3 toroidal_rov_prototype2A/thruster_proto2A/source/run_all.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
