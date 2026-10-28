"""Render the parrot's animations with Rev2D: looping GIFs and a showcase video.

    python3 tools/render_previews.py --rev2d /path/to/Rev2D [--only dance,flap] [--no-video]

Needs Node 22+ with Rev2D's dependencies installed (npm install in the Rev2D checkout) and ffmpeg.
Frames come from `rev2d frames` with a physics warm-up, so every loop starts in the steady state
and closes seamlessly; ffmpeg turns them into palette-optimised GIFs and an H.264 video.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(ROOT, 'parrot', 'parrot.r2d.json')
OUT = os.path.join(ROOT, 'renders')

# name: (layers, seconds in the GIF, seconds in the video)
CLIPS = {
    'idle': (['idle'], 6.0, 6.0),
    'curious': (['curious'], 4.0, 4.0),
    'talk': (['idle', 'talk,add'], 6.0, 6.0),
    'dance': (['dance'], 2.0, 6.0),
    'flap': (['flap'], 2.4, 4.8),
}
GIF_FPS, GIF_SCALE = 25, 1.5      # 450 x 540
VIDEO_FPS, VIDEO_SCALE = 30, 3    # 900 x 1080
FADE = 0.4
# the pose sheet: one cell per control of the rig
POSES = [
    ('rest', ''), ('tilt back', 'AngleZ=-30'), ('tilt forward', 'AngleZ=30'),
    ('turn', 'AngleX=30'), ('look up', 'AngleY=30'), ('blink', 'EyeOpen=0'),
    ('gaze', 'EyeBallX=1,EyeBallY=0.6'), ('beak closed', 'MouthOpen=0'), ('beak open', 'MouthOpen=1'),
    ('wing up', 'WingFlap=1'), ('tail up', 'TailWag=1'), ('crouch', 'Bounce=1'),
]


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def frames(rev2d, layers, seconds, fps, scale, out_dir):
    cmd = ['node', rev2d, 'frames', MODEL, '-o', out_dir, '--fps', str(fps), '--warmup', '10',
           '--scale', str(scale), '--to', str(seconds)]
    for layer in layers:
        cmd += ['--anim', layer]
    run(cmd)
    # the window is inclusive of its end; a loop's last frame equals its first, so drop it
    files = sorted(f for f in os.listdir(out_dir) if f.endswith('.png'))
    os.remove(os.path.join(out_dir, files[-1]))


def gif(frame_dir, fps, dst):
    pattern = os.path.join(frame_dir, 'frame_%04d.png')
    palette = os.path.join(frame_dir, 'palette.png')
    run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', pattern,
         '-vf', 'palettegen=max_colors=256:stats_mode=full', palette])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', pattern, '-i', palette,
         '-lavfi', 'paletteuse=dither=sierra2_4a:diff_mode=rectangle', '-loop', '0', dst])


def pose_sheet(rev2d, work, dst, cols=6, scale=1.2):
    """One labelled cell per rig control, rendered with `rev2d render --param`."""
    from PIL import Image, ImageDraw, ImageFont
    cells = []
    for i, (label, params) in enumerate(POSES):
        png = os.path.join(work, f'pose{i}.png')
        cmd = ['node', rev2d, 'render', MODEL, '-o', png, '--scale', str(scale),
               '--viewbox', '30,30,240,316']
        if params:
            cmd += ['--param', params]
        run(cmd)
        cells.append((label, params, Image.open(png).convert('RGB')))
    w, h = cells[0][2].size
    pad, cap = 6, 34
    rows = -(-len(cells) // cols)
    sheet = Image.new('RGB', (cols * (w + pad) + pad, rows * (h + cap + pad) + pad), (24, 24, 28))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 15)
        small = ImageFont.truetype('DejaVuSans.ttf', 11)
    except OSError:
        font = small = ImageFont.load_default()
    for i, (label, params, im) in enumerate(cells):
        x, y = pad + (i % cols) * (w + pad), pad + (i // cols) * (h + cap + pad)
        sheet.paste(im, (x, y))
        draw.text((x + 4, y + h + 3), label, fill=(235, 235, 240), font=font)
        draw.text((x + 4, y + h + 20), params or 'defaults', fill=(150, 150, 160), font=small)
    sheet.save(dst, optimize=True)


def video(clips, dst):
    """Concatenate the clips with short crossfades."""
    cmd = ['ffmpeg', '-y', '-loglevel', 'error']
    for d, _ in clips:
        cmd += ['-framerate', str(VIDEO_FPS), '-i', os.path.join(d, 'frame_%04d.png')]
    chains, last, offset = [], '[0:v]', 0.0
    for i in range(1, len(clips)):
        offset += clips[i - 1][1] - FADE
        label = f'[x{i}]'
        chains.append(f'{last}[{i}:v]xfade=transition=fade:duration={FADE}:offset={offset:.3f}{label}')
        last = label
    cmd += ['-filter_complex', ';'.join(chains) + f';{last}format=yuv420p[out]', '-map', '[out]',
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-movflags', '+faststart', dst]
    run(cmd)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--rev2d', default=os.environ.get('REV2D_DIR', os.path.join(ROOT, '..', 'Rev2D')),
                    help='Rev2D checkout (default: $REV2D_DIR or ../Rev2D)')
    ap.add_argument('--only', help='comma-separated clip names')
    ap.add_argument('--no-video', action='store_true')
    ap.add_argument('--poses-only', action='store_true', help='only renders/poses.png')
    args = ap.parse_args()
    rev2d = os.path.join(args.rev2d, 'bin', 'rev2d.js')
    if not os.path.exists(rev2d):
        sys.exit(f'Rev2D not found at {args.rev2d} (use --rev2d or REV2D_DIR)')
    names = args.only.split(',') if args.only else list(CLIPS)
    os.makedirs(OUT, exist_ok=True)
    work = tempfile.mkdtemp(prefix='parrot-frames-')
    try:
        pose_sheet(rev2d, work, os.path.join(OUT, 'poses.png'))
        print('renders/poses.png')
        if args.poses_only:
            return
        # one rev2d process per clip, in parallel (each renders on one core)
        jobs = []
        for name in names:
            layers, gif_s, _ = CLIPS[name]
            jobs.append((f'{name}-gif', layers, gif_s, GIF_FPS, GIF_SCALE))
        video_names = [] if args.no_video else ['idle', 'curious', 'talk', 'dance', 'flap']
        for name in video_names:
            layers, _, video_s = CLIPS[name]
            jobs.append((f'{name}-video', layers, video_s, VIDEO_FPS, VIDEO_SCALE))
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as pool:
            for f in [pool.submit(frames, rev2d, layers, s, fps, scale, os.path.join(work, key))
                      for key, layers, s, fps, scale in jobs]:
                f.result()
        for name in names:
            gif(os.path.join(work, f'{name}-gif'), GIF_FPS, os.path.join(OUT, f'{name}.gif'))
            print(f'renders/{name}.gif')
        if video_names:
            video([(os.path.join(work, f'{n}-video'), CLIPS[n][2]) for n in video_names],
                  os.path.join(OUT, 'showcase.mp4'))
            print('renders/showcase.mp4')
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    main()
