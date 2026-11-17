#!/usr/bin/env python3
"""Cuts the loop that plays at the top of the home page: the board alone, from the app's own screen recordings.
usage: python3 tools/demo_clip.py <raw-dir>

<raw-dir> holds row.mp4, quincunx.mp4, reef.mp4 and stairs.mp4: a few turns on each of four starting layouts,
recorded from the app on the iPhone simulator at 1206×2622 by record.py, which sits beside them (on the drive at
swanroad/swanroad-marketing/trailer/pipeline/raw-2026-11-17). Each is played the way a hand plays it: a square is
tapped, the pull lines show, the move is confirmed, the pearls drift and the computer answers.

The loop takes one move from each layout and joins them with short cross-fades. Its last half second fades back
into its own first frame, so the restart cannot be seen. Output: assets/demo.mp4 (720×720, H.264, no sound) and
assets/demo-poster.jpg, which is that first frame: what a browser shows before the video plays, and all it shows to a
visitor who has asked for less motion. Needs ffmpeg."""
import pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
if len(sys.argv) != 2:
    sys.exit(__doc__)
raw = sys.argv[1]
BOARD = "crop=1146:1146:30:697"   # the board in the recording, shore to shore
FRAME = f"{BOARD},scale=720:720:flags=lanczos,setsar=1"
# (recording, where the move begins in it, seconds shown): the pull lines, the confirm, the drift. A screen recording
# holds no frames while the screen is still, so each is given a steady 30 a second before it is cut; otherwise the cut
# skips the quiet second in which the pull lines are showing.
MOVES = [("row.mp4", 4.9, 4.8), ("quincunx.mp4", 16.2, 4.6), ("reef.mp4", 4.8, 4.4), ("stairs.mp4", 4.8, 4.6)]
CROSS = 0.5
total = sum(seconds for _, _, seconds in MOVES) - (len(MOVES) - 1) * CROSS
still = int(CROSS * 30)   # the first frame, held for the closing cross-fade

parts, args = [], ["ffmpeg", "-v", "error", "-y"]
for n, (name, start, seconds) in enumerate(MOVES):
    args += ["-i", f"{raw}/{name}"]
    parts.append(f"[{n}:v]fps=30,trim=start={start}:duration={seconds},setpts=PTS-STARTPTS,{FRAME}" + (",split[s0][first];" if n == 0 else f"[s{n}];"))
parts.append(f"[first]trim=end_frame=1,loop=loop={still - 1}:size=1:start=0,setpts=N/30/TB,fps=30[still];")
shown, last = MOVES[0][2], "s0"
for n in range(1, len(MOVES)):
    parts.append(f"[{last}][s{n}]xfade=transition=fade:duration={CROSS}:offset={shown - CROSS}[x{n}];")
    shown += MOVES[n][2] - CROSS
    last = f"x{n}"
parts.append(f"[{last}][still]xfade=transition=fade:duration={CROSS}:offset={total - CROSS},format=yuv420p[v]")
video = str(ROOT / "assets" / "demo.mp4")
subprocess.run(args + ["-filter_complex", "".join(parts), "-map", "[v]", "-an", "-c:v", "libx264", "-profile:v", "high",
                       "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "slow", "-r", "30", "-t", str(total),
                       "-movflags", "+faststart", video], check=True)
# The poster is the first frame: an anchor about to be placed, with its pull drawn on the board.
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-frames:v", "1", "-q:v", "4",
                str(ROOT / "assets" / "demo-poster.jpg")], check=True)
print(f"assets/demo.mp4: {total} seconds, {pathlib.Path(video).stat().st_size // 1024} KB")
