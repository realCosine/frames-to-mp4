# Frames to MP4

Convert a folder of image frames into a silent H.264 MP4. Requires Python 3.10+ and FFmpeg on PATH; no Python packages needed.

On Windows, install FFmpeg with `winget install Gyan.FFmpeg` and open a new terminal.

```powershell
python E:\frames-to-mp4\frames_to_mp4.py --source "D:\youtube-shorts\02-gold-ball-precision-collar\GOLD_BALL_PRECISION_COLLAR_R10B" --destination "D:\youtube-shorts\02-gold-ball-precision-collar\gold-ball.mp4" --fps 30
```

`--source` / `-s` selects the frame folder. `--destination` / `-d` selects the output file; parent folders are created automatically. `--fps` defaults to 30. `--crf` defaults to 18 (0–51, lower means better quality and larger files). Add `--overwrite` to replace existing output.

PNG, JPEG, BMP, TIFF, WebP and PPM files directly inside the source folder are included. Names sort naturally (`frame2.png` before `frame10.png`); missing frame numbers are fine. Each image contributes one frame. Use frames with matching dimensions and format. Odd image dimensions are padded to even dimensions for broad playback compatibility. There is no audio.

Encoding happens in a temporary folder beside the destination. Failed encodes preserve existing output. Source images are never modified.

Run the integration checks (requires FFmpeg and ffprobe):

```powershell
python -m unittest discover -s tests -v
```
