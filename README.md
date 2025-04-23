# Image to Video Generator

A simple script to create MP4 videos with horizontally scrolling text or images, optimized for horizontal bar displays.

## Features

- Create scrolling or static text videos
- Use images as content (either scrolling or static)
- Customize dimensions, colors, and text properties
- Optimized for horizontal bar displays
- Adjustable aspect ratios
- Control scrolling speed
- Set custom background colors

## Requirements

```
pip install moviepy numpy opencv-python
```

Note: `opencv-python` is required for proper image processing.

## Usage Examples

### Text-Based Videos

#### Basic Usage - Scrolling Text

Create a default scrolling text video (10 seconds):

```bash
python img_to_video.py
```

or explicitly specify text-only mode:

```bash
python img_to_video.py --text-only
```

#### Static Text (No Scrolling)

```bash
python img_to_video.py --text-only --no-scroll
```

#### Custom Text

```bash
python img_to_video.py --text-only --text "Your custom message here"
```

### Image-Based Videos

#### Scrolling Image

Create a video with an image scrolling from right to left:

```bash
python img_to_video.py --use-image-bg
```

This will process all images in the `input` folder and create corresponding videos in the `output` folder.

#### Static Image

Create a video with a static image displayed for the duration:

```bash
python img_to_video.py --use-image-bg --no-scroll
```

#### Image Fitting Options

Fit the entire image within the frame (may add letterboxing):

```bash
python img_to_video.py --use-image-bg --fit
```

Fill the frame with the image (may crop parts of the image):

```bash
python img_to_video.py --use-image-bg --fill
```

### Customization Options

#### Horizontal Bar Display

Create a video optimized for horizontal bar displays:

```bash
python img_to_video.py --horizontal-bar
```

#### Custom Dimensions

```bash
python img_to_video.py --width 1920 --height 100
```

#### Custom Aspect Ratio

```bash
python img_to_video.py --aspect 20:1
```

#### Custom Colors (for text-based videos)

```bash
python img_to_video.py --text-only --color yellow --bg-color blue
```

#### Custom Scroll Speed

```bash
python img_to_video.py --scroll-speed 150
```

#### Longer Duration

```bash
python img_to_video.py --duration 30
```

## All Options

```
  --input-folder DIR     Folder containing input JPG and PNG files (default: 'input')
  --output-folder DIR    Folder to save output MP4 files (default: 'output')
  --text TEXT            Text to display in the video
  --duration DURATION    Duration of the video in seconds (default: 10)
  --width WIDTH          Width of the video (default: 448 for horizontal bar)
  --height HEIGHT        Height of the video (default: 32 for horizontal bar)
  --aspect ASPECT        Aspect ratio in format W:H (e.g. 16:1, 10:1)
  --fontsize FONTSIZE    Font size of the text (default: 24)
  --color COLOR          Color of the text (default: white)
  --bg-color BG_COLOR    Background color (e.g., black, blue, #FF0000) (default: black)
  --fps FPS              Frames per second (default: 24)
  --no-scroll            Disable scrolling (static text/image)
  --scroll-speed SPEED   Custom scroll speed in pixels per second
  --center-crop          Crop to the center of the text vertically
  --center-height HEIGHT Height of the center crop
  --horizontal-bar       Optimize for horizontal bar display
  --use-image-bg         Use images from input folder as content
  --text-only            Create a text-only video without using input images
  --fill                 Fill the video frame with the image (may crop parts of the image)
  --fit                  Fit the entire image within the video frame (may add letterboxing)
```

## Workflow Examples

### Creating a Scrolling Banner with Your Logo

1. Place your logo image in the `input` folder
2. Run: `python img_to_video.py --use-image-bg --width 1280 --height 120`

### Creating a Static Display for Digital Signage

1. Place your image in the `input` folder
2. Run: `python img_to_video.py --use-image-bg --no-scroll --width 1920 --height 1080`

### Creating Multiple Videos at Once

Place multiple images in the `input` folder and run the script. It will process all JPG and PNG files and create corresponding videos in the `output` folder.

## Troubleshooting

If you encounter errors related to image processing, make sure you have `opencv-python` installed:

```bash
pip install opencv-python
```
