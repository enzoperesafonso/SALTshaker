"""Command-line interface: ``saltshaker visibility``, ``saltshaker observable``."""

import argparse
import sys

import astropy.units as u
from astropy.coordinates import SkyCoord

from saltshaker import __version__
from saltshaker.planning import get_visibility_windows, is_target_observable


def _target_from_args(args, dec_only=False):
    if args.name:
        return SkyCoord.from_name(args.name)
    if dec_only and args.dec is not None:
        return SkyCoord(ra=0 * u.deg, dec=args.dec * u.deg)  # RA is irrelevant here
    if args.ra is None or args.dec is None:
        raise SystemExit("Provide a target NAME, or both --ra and --dec (degrees).")
    return SkyCoord(ra=args.ra * u.deg, dec=args.dec * u.deg)


def _add_target_args(parser):
    parser.add_argument("name", nargs="?", help="Target name (resolved online, e.g. 'Sirius').")
    parser.add_argument("--ra", type=float, help="Right ascension in degrees (not needed for 'observable').")
    parser.add_argument("--dec", type=float, help="Declination in degrees.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="saltshaker",
        description="SALT pre-planning tools. Validate everything in the official PIPT.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    vis = sub.add_parser("visibility", help="Print visibility windows for a date.")
    _add_target_args(vis)
    vis.add_argument("date", help="UTC date, e.g. 2026-01-15 (window starts 12:00 UTC).")
    vis.add_argument("--night-only", action="store_true",
                     help="Clip windows to astronomical night.")

    obs = sub.add_parser("observable", help="Check whether a declination is ever observable.")
    _add_target_args(obs)

    args = parser.parse_args(argv)
    target = _target_from_args(args, dec_only=args.command == "observable")

    if args.command == "observable":
        ok = is_target_observable(target)
        print(f"dec={target.dec.deg:+.3f} deg: {'observable' if ok else 'never observable'}")
        return 0 if ok else 1

    windows = get_visibility_windows(target, args.date, night_only=args.night_only)
    if not windows:
        print("No visibility windows in this 24-hour period.")
        return 1
    for w in windows:
        print(f"{w.start_time_utc} -> {w.end_time_utc}  ({w.duration / 60:.1f} min)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
