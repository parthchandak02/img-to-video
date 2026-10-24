<div align="center">

<h1>img-to-video</h1>

<p><b>Scrolling text and image MP4s for bar displays.</b></p>

<p><i>A long, thin LED or LCD bar plays video. This script makes the ticker video it needs from one command.</i></p>

<h6>

![Python](https://img.shields.io/badge/Python-3-111111?style=flat-square&logo=python&logoColor=white)
![MoviePy](https://img.shields.io/badge/MoviePy-1.0.3-E0A526?style=flat-square)
![ImageMagick](https://img.shields.io/badge/needs-ImageMagick-E0A526?style=flat-square)
![Status](https://img.shields.io/badge/status-experiment-555555?style=flat-square)

</h6>

<a href="#how-it-works"><b>How it works</b></a> ·
<a href="#install"><b>Install</b></a> ·
<a href="#usage"><b>Usage</b></a>

<br><br>

<img src="docs/assets/readme/frames.png" width="720" alt="Six frames, one second apart, from a 1280 by 96 video: yellow bold text reading Platform 4: the 08:15 express is running on time enters from the right edge and scrolls off the left">

<sub>Frames sampled once a second from a real 6-second render. Made-up message.</sub>

</div>

<br>

## Why

Stretched bar displays (448×32, 1280×120, 1920×100) usually play a looping video file rather
than taking text input. Making a ticker for one in a video editor is slow for a one-line
message. `img_to_video.py` renders that video directly: pick the text or images, the frame
size and the duration, and it writes an H.264 MP4.

## How it works

<table>
<tr>
<td width="33%" valign="top">

**1 · Pick the content**

A line of text (`--text-only`), or every JPG and PNG in `input/` (`--use-image-bg`), one
video per image.

</td>
<td width="33%" valign="top">

**2 · Size the frame**

Defaults to 448×32. Set `--width` and `--height`, or `--aspect 20:1` to derive the height
from the width.

</td>
<td width="33%" valign="top">

**3 · Render**

MoviePy draws each frame, moving the text right to left so it crosses the whole frame once
per `--duration`, and writes `output/*.mp4`.

</td>
</tr>
</table>

<div align="center">
<img src="docs/assets/readme/cli.png" width="720" alt="Terminal: the img_to_video.py command for the frames above, MoviePy build and write messages, then ffprobe reporting an h264 stream at 1280 by 96, 24 fps, 144 frames">
<br><sub>The run that produced the frames above, checked with ffprobe.</sub>
</div>

## What it does

- **Scrolling or static text.** Text enters from the right and exits left; `--no-scroll` centres it instead.
- **Speed control.** By default one pass takes the whole duration; `--scroll-speed` sets pixels per second.
- **Colours.** `--color` for the text, `--bg-color` for the frame (named colours or `#RRGGBB`).
- **Images in, one video each.** Every image in `input/` becomes its own MP4, stretched to the frame, fitted with black bars (`--fit`) or centre-cropped (`--fill`), and scrolled across the `--bg-color` frame like the text (or centred with `--no-scroll`).
- **Falls back to text.** With no images in `input/`, it renders the text video instead.

## Install

Needs MoviePy 1.x (2.x removed the `moviepy.editor` and `set_fps` API this uses), ffmpeg, and
ImageMagick, which MoviePy calls to draw text.

```bash
git clone https://github.com/parthchandak02/img-to-video.git
cd img-to-video
pip install "moviepy==1.0.3" numpy pillow opencv-python
brew install imagemagick      # or set IMAGEMAGICK_BINARY to a magick binary
```

## Usage

```bash
python img_to_video.py --text-only --text "Doors open at 9"     # 448x32 scrolling text, 10 s
python img_to_video.py --text-only --no-scroll --bg-color blue  # static, centred
python img_to_video.py --text-only --width 1280 --height 120    # bigger bar
python img_to_video.py --use-image-bg --fit                     # each image in input/ -> output/
python img_to_video.py --aspect 20:1 --duration 30              # 448 wide, height from ratio
```

<details>
<summary><b>All options</b></summary>

| Option | |
|---|---|
| `--input-folder DIR` | Images to read (default `input`) |
| `--output-folder DIR` | Where MP4s go (default `output`) |
| `--text TEXT` | The message |
| `--duration N` | Seconds (default 10) |
| `--width`, `--height` | Frame size (default 448×32) |
| `--aspect W:H` | Overrides height from width |
| `--fontsize N` | Default 24 |
| `--font NAME` | ImageMagick font name or a `.ttf` path (default `Arial-Bold`, falling back to an Arial Bold or DejaVu Sans Bold file when ImageMagick has no such font) |
| `--color`, `--bg-color` | Text and background colour |
| `--fps N` | Default 24 |
| `--no-scroll` | Static instead of scrolling |
| `--scroll-speed PX` | Pixels per second |
| `--text-only` | Ignore `input/`, make `output/text_only.mp4` |
| `--use-image-bg` | Use the images in `input/` |
| `--fit`, `--fill` | Letterbox or crop images to the frame |
| `--horizontal-bar` | 448×32 unless `--width`/`--height` are set, text at 3/4 of the bar height unless `--fontsize` is set |
| `--center-crop`, `--center-height N` | Keep only the middle N rows of the rendered text (default: frame height) |

</details>

<br>

<div align="center">
<sub>One Python script on MoviePy, ImageMagick and ffmpeg.</sub>
</div>
