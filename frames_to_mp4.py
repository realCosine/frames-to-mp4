#!/usr/bin/env python3
"""Convert a naturally sorted folder of image frames to an H.264 MP4."""
import argparse
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp', '.ppm'}


def natural_key(path):
    return [(1, int(part)) if part.isdigit() else (0, part.casefold())
            for part in re.split(r'(\d+)', path.name)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', '-s', required=True, type=Path, help='Folder containing frames (non-recursive)')
    parser.add_argument('--destination', '-d', required=True, type=Path, help='Output .mp4 file')
    parser.add_argument('--fps', type=float, default=30, help='Frames per second (default: 30)')
    parser.add_argument('--crf', type=int, default=18, help='H.264 quality, 0–51; lower is better (default: 18)')
    parser.add_argument('--overwrite', action='store_true', help='Replace an existing output file')
    args = parser.parse_args()
    if not math.isfinite(args.fps) or args.fps <= 0:
        parser.error('--fps must be a finite positive number')
    if not 0 <= args.crf <= 51:
        parser.error('--crf must be between 0 and 51')
    source = args.source.resolve()
    destination = args.destination.resolve()
    if not source.is_dir():
        parser.error(f'Source folder does not exist: {source}')
    if destination.suffix.lower() != '.mp4':
        parser.error('--destination must be an .mp4 file')
    if destination.exists() and not args.overwrite:
        parser.error(f'Output already exists: {destination}; use --overwrite to replace it')
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        parser.error('FFmpeg is required on PATH. On Windows: winget install Gyan.FFmpeg')
    frames = sorted((p for p in source.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS), key=natural_key)
    if not frames:
        parser.error(f'No supported image frames found in {source}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Encode to a temporary file first so a failed encode preserves existing output.
    with tempfile.TemporaryDirectory(prefix='frames-to-mp4-', dir=destination.parent) as temp:
        manifest = Path(temp) / 'frames.ffconcat'
        output = Path(temp) / 'output.mp4'
        def entry(path):
            escaped = path.as_posix().replace("'", "'\\''")
            return f"file '{escaped}'\noption framerate {args.fps}\n"
        with manifest.open('w', encoding='utf-8', newline='\n') as handle:
            handle.write('ffconcat version 1.0\n')
            for frame in frames:
                handle.write(entry(frame))
                handle.write(f'duration {1 / args.fps:.15f}\n')
            handle.write(entry(frames[-1]))
        command = [ffmpeg, '-hide_banner', '-loglevel', 'warning', '-nostdin', '-xerror',
                   '-f', 'concat', '-safe', '0', '-i', str(manifest),
                   '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(args.crf),
                   '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-pix_fmt', 'yuv420p',
                   '-r', str(args.fps), '-frames:v', str(len(frames)),
                   '-movflags', '+faststart', str(output)]
        print(f'Encoding {len(frames)} frames at {args.fps:g} fps...', flush=True)
        subprocess.run(command, check=True)
        if args.overwrite:
            output.replace(destination)
        else:
            # Hard-link creation fails if another process created the destination.
            destination.hardlink_to(output)
    print(f'Created: {destination}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        sys.exit(1)
