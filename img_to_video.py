#!/usr/bin/env python3
"""
Simple script to create MP4 videos with horizontally scrolling text.
Processes all JPG and PNG files from an input folder and creates MP4s in an output folder.
Ideal for horizontal bar displays.
"""

import numpy as np
import argparse
import os
import glob
import sys

# Import PIL for image handling
try:
    from PIL import Image
    # Check if we're using Pillow 9.0.0+ (which deprecated ANTIALIAS)
    pillow_version = getattr(Image, '__version__', '0.0.0')
    if tuple(map(int, pillow_version.split('.'))) >= (9, 0, 0):
        # For Pillow 9.0.0+
        RESAMPLING_FILTER = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
    else:
        # For older Pillow versions
        RESAMPLING_FILTER = Image.ANTIALIAS
except ImportError:
    print("Error: Pillow not installed. Please install with pip install Pillow")
    sys.exit(1)
    
# Define a custom image loading function to handle Pillow version differences
def load_image_with_proper_resampling(image_path, target_size=None):
    """Load an image with the proper resampling filter based on the installed Pillow version."""
    img = Image.open(image_path)
    if target_size:
        img = img.resize(target_size, RESAMPLING_FILTER)
    return np.array(img)

# Try different MoviePy import approaches
try:
    # For MoviePy 1.x
    from moviepy.editor import VideoClip, TextClip, ImageClip, ColorClip, CompositeVideoClip
    print("Using MoviePy editor imports")
except ImportError:
    try:
        # For MoviePy 2.x
        from moviepy import VideoClip, TextClip, ImageClip
        from moviepy import ColorClip, CompositeVideoClip
        print("Using direct MoviePy imports")
    except ImportError:
        try:
            # Alternative approach
            import moviepy
            # Create TextClip function
            def TextClip(text, fontsize=70, color='white', font='Arial-Bold'):
                # Create a simple numpy array with text
                height = fontsize + 20
                width = len(text) * fontsize // 2
                img = np.zeros((height, width, 3), dtype=np.uint8)
                # We can't actually render text without PIL, so this is a placeholder
                print(f"Created placeholder for text: {text}")
                return moviepy.ImageClip(img)
            
            # Create ColorClip function
            def ColorClip(size, color):
                # Create a simple numpy array with solid color
                img = np.zeros((size[1], size[0], 3), dtype=np.uint8)
                if isinstance(color, tuple) and len(color) == 3:
                    img[:, :, 0] = color[0]
                    img[:, :, 1] = color[1]
                    img[:, :, 2] = color[2]
                return moviepy.ImageClip(img)
            
            # Create CompositeVideoClip function
            def CompositeVideoClip(clips):
                # Just return the first clip for simplicity
                return clips[0] if clips else None
            
            # Use VideoClip from moviepy
            VideoClip = moviepy.VideoClip
            ImageClip = moviepy.ImageClip
            print("Using custom text rendering")
        except ImportError:
            print("Error: MoviePy not properly installed. Please install with pip install moviepy==1.0.3")
            sys.exit(1)

def parse_color(value):
    """Return an (r, g, b) tuple for a colour name or #RRGGBB string."""
    from PIL import ImageColor
    try:
        return ImageColor.getrgb(value)[:3]
    except ValueError:
        print(f"Unknown colour {value!r}, using black")
        return (0, 0, 0)

# Font files tried when ImageMagick has no font registered under the requested name
FALLBACK_FONT_FILES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",   # macOS
    "/Library/Fonts/Arial Bold.ttf",                       # macOS (older)
    "C:/Windows/Fonts/arialbd.ttf",                        # Windows
    "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]

def resolve_font(font):
    """Return a font ImageMagick can render: a file path, a registered font name, or a bold fallback file."""
    if os.path.isfile(font):
        return font
    try:
        if font in TextClip.list('font'):
            return font
    except Exception:
        pass
    for path in FALLBACK_FONT_FILES:
        if os.path.isfile(path):
            print(f"ImageMagick has no font named {font!r}, using {path}")
            return path
    return font

def make_text_clip(text="Scrolling Text", duration=10, fps=24, 
                  width=1280, height=120, fontsize=70, color='white',
                  bg_color='black', scroll=True, scroll_speed=None,
                  center_crop=False, center_height=None, font='Arial-Bold'):
    """Generate a clip with text that can be static or scrolling.
    
    Args:
        text (str): Text to display
        duration (int): Duration of the video in seconds
        fps (int): Frames per second
        width (int): Width of the video
        height (int): Height of the video
        fontsize (int): Font size of the text
        color (str): Color of the text
        bg_color (str): Background colour (name or #RRGGBB)
        center_crop (bool): Keep only the middle center_height rows of the rendered text
        center_height (int): Rows kept by center_crop (default: the frame height)
        font (str): ImageMagick font name or path to a font file
        scroll (bool): Whether to scroll the text or keep it static
        scroll_speed (float): Optional custom scroll speed (pixels per second)
                             If None, speed is calculated to ensure text moves 
                             completely across screen in duration
    """
    
    # Create a text clip
    txt_clip = TextClip(text, fontsize=fontsize, color=color, font=resolve_font(font))

    # Text pixels plus an alpha mask, so the glyphs sit on the background colour
    # instead of on the black box ImageMagick renders around them.
    txt_rgb = txt_clip.get_frame(0).astype(np.float32)
    if txt_clip.mask is not None:
        txt_alpha = txt_clip.mask.get_frame(0).astype(np.float32)
    else:
        txt_alpha = np.ones(txt_rgb.shape[:2], dtype=np.float32)

    # Optionally keep only the vertical middle of the rendered text
    if center_crop:
        band = center_height or height
        if band < txt_rgb.shape[0]:
            top = (txt_rgb.shape[0] - band) // 2
            txt_rgb = txt_rgb[top:top + band]
            txt_alpha = txt_alpha[top:top + band]

    # Static text that is larger than the frame is scaled down to fit
    if not scroll and (txt_rgb.shape[1] > width or txt_rgb.shape[0] > height):
        scale = min(width / txt_rgb.shape[1], height / txt_rgb.shape[0])
        new_size = (max(1, int(txt_rgb.shape[1] * scale)), max(1, int(txt_rgb.shape[0] * scale)))
        txt_rgb = np.array(Image.fromarray(txt_rgb.astype(np.uint8)).resize(new_size, RESAMPLING_FILTER), dtype=np.float32)
        txt_alpha = np.array(Image.fromarray((txt_alpha * 255).astype(np.uint8)).resize(new_size, RESAMPLING_FILTER), dtype=np.float32) / 255.0

    txt_height, txt_width = txt_rgb.shape[:2]
    background = np.empty((height, width, 3), dtype=np.uint8)
    background[:, :] = parse_color(bg_color)

    def paste(frame, x_pos, y_pos):
        """Alpha-blend the text onto frame at (x_pos, y_pos), clipped to the frame."""
        x0, y0 = max(0, x_pos), max(0, y_pos)
        x1, y1 = min(width, x_pos + txt_width), min(height, y_pos + txt_height)
        if x1 <= x0 or y1 <= y0:
            return
        src = txt_rgb[y0 - y_pos:y1 - y_pos, x0 - x_pos:x1 - x_pos]
        alpha = txt_alpha[y0 - y_pos:y1 - y_pos, x0 - x_pos:x1 - x_pos, None]
        region = frame[y0:y1, x0:x1].astype(np.float32)
        frame[y0:y1, x0:x1] = (src * alpha + region * (1 - alpha)).astype(np.uint8)

    # Function to animate the text position
    def make_frame(t):
        frame = background.copy()
        y_pos = int((height - txt_height) // 2)

        if scroll:
            # Calculate speed if not provided
            if scroll_speed is None:
                speed = (width + txt_width) / duration
            else:
                speed = scroll_speed

            # Start at the right edge and move left until the text has fully left the frame
            x_pos = int(width - (t * speed) % (width + txt_width))
        else:
            # Static text centered in frame
            x_pos = int((width - txt_width) // 2)

        paste(frame, x_pos, y_pos)
        return frame

    # Create and return the clip
    clip = VideoClip(make_frame, duration=duration)
    return clip

def parse_args():
    parser = argparse.ArgumentParser(description='Create videos with scrolling or static text from images')
    parser.add_argument('--input-folder', type=str, default='input',
                        help='Folder containing input JPG and PNG files')
    parser.add_argument('--output-folder', type=str, default='output',
                        help='Folder to save output MP4 files')
    parser.add_argument('--text', type=str, default='Horizontal Scrolling Text Example',
                        help='Text to display in the video')
    parser.add_argument('--duration', type=int, default=10,
                        help='Duration of the video in seconds')
    parser.add_argument('--width', type=int, default=None,
                        help='Width of the video (default: 448 for horizontal bar)')
    parser.add_argument('--height', type=int, default=None,
                        help='Height of the video (default: 32 for horizontal bar)')
    parser.add_argument('--aspect', type=str,
                        help='Aspect ratio in format W:H (e.g. 16:1, 10:1). Overrides width/height if provided')
    parser.add_argument('--fontsize', type=int, default=None,
                        help='Font size of the text (default: 24, or 3/4 of the bar height with --horizontal-bar)')
    parser.add_argument('--font', type=str, default='Arial-Bold',
                        help='ImageMagick font name or path to a .ttf/.otf file (default: Arial-Bold)')
    parser.add_argument('--color', type=str, default='white',
                        help='Color of the text')
    parser.add_argument('--bg-color', type=str, default='black',
                        help='Background color (e.g., black, blue, #FF0000)')
    parser.add_argument('--fps', type=int, default=24,
                        help='Frames per second')
    parser.add_argument('--no-scroll', action='store_true',
                        help='Disable scrolling (static text)')
    parser.add_argument('--scroll-speed', type=float,
                        help='Custom scroll speed in pixels per second')
    parser.add_argument('--center-crop', action='store_true',
                        help='Keep only the vertical middle of the rendered text (see --center-height)')
    parser.add_argument('--center-height', type=int, default=None,
                        help='Rows of text kept by --center-crop (default: the frame height)')
    parser.add_argument('--horizontal-bar', action='store_true',
                        help='Horizontal bar preset: 448x32 unless --width/--height are given, and text sized to 3/4 of the bar height unless --fontsize is given')
    parser.add_argument('--use-image-bg', action='store_true',
                        help='Use the input image as background instead of a solid color')
    parser.add_argument('--text-only', action='store_true',
                        help='Create a text-only video without using input images')
    parser.add_argument('--fill', action='store_true',
                        help='Fill the video frame with the image (may crop parts of the image)')
    parser.add_argument('--fit', action='store_true',
                        help='Fit the entire image within the video frame (may add letterboxing)')
    return parser.parse_args()

def create_video_from_image(image_path, args):
    # Get base filename without extension
    base_name = os.path.basename(image_path)
    name_without_ext = os.path.splitext(base_name)[0]
    output_path = os.path.join(args.output_folder, f"{name_without_ext}.mp4")
    
    # Determine center crop height if needed
    center_height = args.center_height
    
    # Create the text clip
    text_clip = make_text_clip(
        text=args.text,
        duration=args.duration,
        width=args.width,
        height=args.height,
        fontsize=args.fontsize,
        color=args.color,
        bg_color=args.bg_color,
        scroll=not args.no_scroll,
        scroll_speed=args.scroll_speed,
        center_crop=args.center_crop,
        center_height=center_height,
        font=args.font
    )
    
    # Set the fps
    text_clip = text_clip.set_fps(args.fps)
    
    # Try to use the image if requested
    if args.use_image_bg:
        try:
            # Load the image using our custom function
            img_array = load_image_with_proper_resampling(image_path)
            img_clip = ImageClip(img_array)
            
            # Get original dimensions
            orig_width, orig_height = img_clip.size
            
            # Determine how to resize based on fill/fit options
            if args.fill:
                # Fill mode: maintain aspect ratio but ensure the entire frame is filled
                # This may crop parts of the image
                scale = max(args.width / orig_width, args.height / orig_height)
                new_width = int(orig_width * scale)
                new_height = int(orig_height * scale)
                # Load and resize with our custom function
                img_array = load_image_with_proper_resampling(image_path, target_size=(new_width, new_height))
                img_clip = ImageClip(img_array)
                
                # Crop to the target dimensions from the center
                x_center = new_width // 2
                y_center = new_height // 2
                x1 = int(max(0, x_center - args.width // 2))
                y1 = int(max(0, y_center - args.height // 2))
                img_clip = img_clip.crop(x1=x1, y1=y1, width=args.width, height=args.height)
                
            elif args.fit:
                # Fit mode: maintain aspect ratio and fit entire image within frame
                # This may add black bars (letterboxing/pillarboxing)
                scale = min(args.width / orig_width, args.height / orig_height)
                new_width = int(orig_width * scale)
                new_height = int(orig_height * scale)
                # Load and resize with our custom function
                img_array = load_image_with_proper_resampling(image_path, target_size=(new_width, new_height))
                img_clip = ImageClip(img_array)
                
                # Create a black background of the target dimensions
                bg_clip = ColorClip((args.width, args.height), color=(0, 0, 0))
                bg_clip = bg_clip.set_duration(args.duration)
                
                # Position the resized image in the center of the frame
                x_pos = int((args.width - new_width) // 2)
                y_pos = int((args.height - new_height) // 2)
                img_clip = img_clip.set_position((x_pos, y_pos))
                
                # Composite the image onto the background
                img_clip = CompositeVideoClip([bg_clip, img_clip])
            else:
                # Default: stretch to fit the target dimensions
                img_clip = img_clip.resize((args.width, args.height))
            
            # Set duration to match text clip
            img_clip = img_clip.set_duration(args.duration)
            img_clip = img_clip.set_fps(args.fps)
            
            # When using an image, we either scroll it or display it statically.
            # Either way it is composited onto a frame-sized background, otherwise the
            # position set on the clip is never rendered.
            try:
                bg = ColorClip((args.width, args.height), color=parse_color(args.bg_color))
                bg = bg.set_duration(args.duration)

                if not args.no_scroll:
                    img_w = img_clip.w
                    if args.scroll_speed is None:
                        # One full pass (enter right, leave left) per duration
                        speed = (args.width + img_w) / args.duration
                    else:
                        speed = args.scroll_speed

                    def image_position(t):
                        # Start at the right edge and move left until the image has left the frame
                        x_pos = args.width - (t * speed) % (args.width + img_w)
                        return (int(x_pos), int((args.height - img_clip.h) // 2))

                    img_clip = img_clip.set_position(image_position)
                    print("Created scrolling image video")
                else:
                    # For static mode, just center the image
                    img_clip = img_clip.set_position('center')
                    print("Created static image video")

                final_clip = CompositeVideoClip([bg, img_clip], size=(args.width, args.height))
                final_clip = final_clip.set_duration(args.duration).set_fps(args.fps)
            except Exception as e:
                print(f"Error processing image animation: {e}")
                print("Falling back to text-only clip")
                final_clip = text_clip
            
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            print("Falling back to text-only clip")
            final_clip = text_clip
    else:
        # Use text-only clip
        final_clip = text_clip
    
    # Write the result to a file
    print(f"Creating {args.duration}s video for {base_name}...")
    final_clip.write_videofile(output_path, codec='libx264')
    print(f"Video saved as {output_path}")
    
    return output_path

def main():
    # Parse command line arguments
    args = parse_args()
    
    # Fill in the frame size (448x32 bar by default) and the font size
    if args.width is None:
        args.width = 448
    if args.height is None:
        args.height = 32
    # Calculate dimensions if aspect ratio is provided
    if args.aspect:
        try:
            w_ratio, h_ratio = map(int, args.aspect.split(':'))
            # For horizontal bar displays, we typically want to preserve width
            # and adjust height based on the aspect ratio
            new_height = int(args.width * h_ratio / w_ratio)
            args.height = new_height
            print(f"Using aspect ratio {args.aspect}, dimensions: {args.width}x{args.height}")
        except ValueError:
            print(f"Invalid aspect ratio format: {args.aspect}. Using default dimensions.")
    
    if args.horizontal_bar:
        if args.fontsize is None:
            args.fontsize = max(8, int(args.height * 0.75))
        print(f"Using horizontal bar display mode: {args.width}x{args.height}, font size {args.fontsize}")
    if args.fontsize is None:
        args.fontsize = 24
    
    # Create input and output folders if they don't exist
    os.makedirs(args.input_folder, exist_ok=True)
    os.makedirs(args.output_folder, exist_ok=True)
    
    if args.text_only:
        # Create a single text-only video
        center_height = args.center_height
        
        clip = make_text_clip(
            text=args.text,
            duration=args.duration,
            width=args.width,
            height=args.height,
            fontsize=args.fontsize,
            color=args.color,
            bg_color=args.bg_color,
            scroll=not args.no_scroll,
            scroll_speed=args.scroll_speed,
            center_crop=args.center_crop,
            center_height=center_height,
            font=args.font
        )
        
        clip = clip.set_fps(args.fps)
        output_path = os.path.join(args.output_folder, "text_only.mp4")
        print(f"Creating {args.duration}s text-only video...")
        clip.write_videofile(output_path, codec='libx264')
        print(f"Video saved as {output_path}")
    else:
        # Find all JPG and PNG files in the input folder
        image_files = []
        for ext in ['jpg', 'jpeg', 'png', 'JPG', 'JPEG', 'PNG']:
            image_files.extend(glob.glob(os.path.join(args.input_folder, f"*.{ext}")))
        
        if not image_files:
            print(f"No JPG or PNG files found in {args.input_folder}")
            print("Creating a text-only video instead")
            # Create a text-only video
            center_height = args.center_height
            
            clip = make_text_clip(
                text=args.text,
                duration=args.duration,
                width=args.width,
                height=args.height,
                fontsize=args.fontsize,
                color=args.color,
                bg_color=args.bg_color,
                scroll=not args.no_scroll,
                scroll_speed=args.scroll_speed,
                center_crop=args.center_crop,
                center_height=center_height,
                font=args.font
            )
            
            clip = clip.set_fps(args.fps)
            output_path = os.path.join(args.output_folder, "text_only.mp4")
            print(f"Creating {args.duration}s text-only video...")
            clip.write_videofile(output_path, codec='libx264')
            print(f"Video saved as {output_path}")
        else:
            # Process each image file
            for image_file in image_files:
                try:
                    output_path = create_video_from_image(image_file, args)
                    print(f"Successfully processed {image_file} -> {output_path}")
                except Exception as e:
                    print(f"Error processing {image_file}: {e}")

if __name__ == "__main__":
    main()
