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

def make_text_clip(text="Scrolling Text", duration=10, fps=24, 
                  width=1280, height=120, fontsize=70, color='white',
                  bg_color='black', scroll=True, scroll_speed=None,
                  center_crop=False, center_height=None):
    """Generate a clip with text that can be static or scrolling.
    
    Args:
        text (str): Text to display
        duration (int): Duration of the video in seconds
        fps (int): Frames per second
        width (int): Width of the video
        height (int): Height of the video
        fontsize (int): Font size of the text
        color (str): Color of the text
        scroll (bool): Whether to scroll the text or keep it static
        scroll_speed (float): Optional custom scroll speed (pixels per second)
                             If None, speed is calculated to ensure text moves 
                             completely across screen in duration
    """
    
    # Create a text clip
    txt_clip = TextClip(text, fontsize=fontsize, color=color, font='Arial-Bold')
    txt_width = txt_clip.w
    txt_height = txt_clip.h
    
    # Function to animate the text position
    def make_frame(t):
        # Create a frame with specified background color
        if bg_color == 'black':
            frame = np.zeros((height, width, 3), dtype=np.uint8)
        else:
            # Convert color string to RGB
            if bg_color.startswith('#'):
                # Hex color code
                r = int(bg_color[1:3], 16)
                g = int(bg_color[3:5], 16)
                b = int(bg_color[5:7], 16)
            else:
                # Named color (simple implementation for common colors)
                color_map = {
                    'white': (255, 255, 255),
                    'red': (255, 0, 0),
                    'green': (0, 255, 0),
                    'blue': (0, 0, 255),
                    'yellow': (255, 255, 0),
                    'cyan': (0, 255, 255),
                    'magenta': (255, 0, 255),
                    'gray': (128, 128, 128),
                    'black': (0, 0, 0)
                }
                r, g, b = color_map.get(bg_color.lower(), (0, 0, 0))
            
            frame = np.ones((height, width, 3), dtype=np.uint8) * np.array([r, g, b], dtype=np.uint8)
        
        # Get text frame
        txt_frame = txt_clip.get_frame(0)
        
        if scroll:
            # Calculate speed if not provided
            if scroll_speed is None:
                total_width = width + txt_width
                speed = total_width / duration
            else:
                speed = scroll_speed
            
            # Calculate position: start from right edge and move to left
            x_pos = width - (t * speed) % (width + txt_width)
            
            # Calculate vertical position (center)
            y_pos = int((height - txt_height) // 2)
            
            # Only paste the visible part of text
            if x_pos > 0:
                visible_width = int(min(txt_width, width - x_pos))
                if visible_width > 0:
                    frame[y_pos:y_pos+txt_height, int(x_pos):int(x_pos+visible_width)] = txt_frame[:, :visible_width]
            
            # If text wraps around, paste the second part
            if x_pos < 0:
                visible_width = int(min(txt_width + x_pos, width))
                if visible_width > 0:
                    frame[y_pos:y_pos+txt_height, :int(visible_width)] = txt_frame[:, int(-x_pos):int(-x_pos+visible_width)]
        else:
            # Static text centered in frame
            x_pos = int((width - txt_width) // 2)
            y_pos = int((height - txt_height) // 2)
            
            # Ensure text fits within frame
            if txt_width <= width and txt_height <= height:
                frame[y_pos:y_pos+txt_height, x_pos:x_pos+txt_width] = txt_frame
            else:
                # Scale down text if it's too large
                scale = min(width / txt_width, height / txt_height)
                new_w, new_h = int(txt_width * scale), int(txt_height * scale)
                resized_frame = np.array(txt_clip.resize((new_w, new_h)).get_frame(0))
                x_pos = int((width - new_w) // 2)
                y_pos = int((height - new_h) // 2)
                frame[y_pos:y_pos+new_h, x_pos:x_pos+new_w] = resized_frame
        
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
    parser.add_argument('--width', type=int, default=448,
                        help='Width of the video (default: 448 for horizontal bar)')
    parser.add_argument('--height', type=int, default=32,
                        help='Height of the video (default: 32 for horizontal bar)')
    parser.add_argument('--aspect', type=str,
                        help='Aspect ratio in format W:H (e.g. 16:1, 10:1). Overrides width/height if provided')
    parser.add_argument('--fontsize', type=int, default=24,
                        help='Font size of the text')
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
                        help='Crop to the center of the text vertically')
    parser.add_argument('--center-height', type=int, default=None,
                        help='Height of the center crop (if center-crop is enabled)')
    parser.add_argument('--horizontal-bar', action='store_true',
                        help='Optimize for horizontal bar display (sets width=448, height=32 if not specified)')
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
    if args.center_crop and center_height is None:
        # Default to 1/3 of the height if not specified
        center_height = args.height // 3
    
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
        center_height=center_height
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
            
            # When using an image, we either scroll it or display it statically
            try:
                # Set duration and fps for the image clip
                img_clip = img_clip.set_duration(args.duration)
                img_clip = img_clip.set_fps(args.fps)
                
                if not args.no_scroll:
                    # For scrolling mode, create a function to animate the image position
                    def make_frame_for_image(t):
                        # Calculate speed if not provided
                        if args.scroll_speed is None:
                            # Calculate speed based on image width and duration
                            total_width = args.width + img_clip.w
                            speed = total_width / args.duration
                        else:
                            speed = args.scroll_speed
                        
                        # Calculate position: start from right edge and move to left
                        x_pos = args.width - (t * speed) % (args.width + img_clip.w)
                        return [int(x_pos), 0]
                    
                    # Apply the scrolling animation to the image clip
                    img_clip = img_clip.set_position(make_frame_for_image)
                    print("Created scrolling image video")
                else:
                    # For static mode, just center the image
                    img_clip = img_clip.set_position('center')
                    print("Created static image video")
                
                final_clip = img_clip
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
    
    # Set horizontal bar defaults if requested
    if args.horizontal_bar:
        if args.width is None:
            args.width = 448
        if args.height is None:
            args.height = 32
        print(f"Using horizontal bar display mode: {args.width}x{args.height}")
    
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
    
    # Create input and output folders if they don't exist
    os.makedirs(args.input_folder, exist_ok=True)
    os.makedirs(args.output_folder, exist_ok=True)
    
    if args.text_only:
        # Create a single text-only video
        center_height = args.center_height
        if args.center_crop and center_height is None:
            center_height = args.height // 3
        
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
            center_height=center_height
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
            if args.center_crop and center_height is None:
                center_height = args.height // 3
            
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
                center_height=center_height
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
