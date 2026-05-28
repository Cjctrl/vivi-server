# Python Imaging Library (PIL)

The Python Imaging Library (PIL) is a free library for the Python programming language that adds support for opening, manipulating, and saving many different image file formats. It is available for Windows, Mac OS X and Linux. The last version of PIL was 1.1.7, released in 2009. Since then, its development has been continued by the Pillow project, a friendly fork of PIL.

## Overview

PIL provides a set of tools for image processing that includes:
- Image opening and saving in various formats
- Image manipulation (cropping, resizing, rotating, etc.)
- Image enhancement (contrast, brightness, color balance)
- Image analysis (histograms, statistics)
- Support for various image formats including JPEG, PNG, GIF, BMP, TIFF, and more

## History

PIL was developed by Fredrik Lundh and contributors. The original library was last updated in 2009. Due to the lack of active maintenance, a group of volunteers created Pillow in 2010 as a fork of PIL to provide continued support and development. Pillow aims to be a drop-in replacement for PIL while adding new features and improvements.

## Pillow - The Modern Fork

Pillow is the actively maintained fork of PIL. It provides:
- Continued support for modern Python versions
- Additional image formats
- Performance improvements
- Bug fixes
- Active community maintenance

## Basic Usage

### Opening and Displaying Images
```python
from PIL import Image

# Open an image file
img = Image.open("example.jpg")

# Display the image (uses default image viewer)
img.show()

# Get image information
print(f"Format: {img.format}")
print(f"Size: {img.size}")
print(f"Mode: {img.mode}")
```

### Basic Image Operations
```python
from PIL import Image

# Open an image
img = Image.open("input.jpg")

# Resize the image
resized_img = img.resize((800, 600))

# Rotate the image
rotated_img = img.rotate(45)

# Convert to grayscale
gray_img = img.convert("L")

# Save the modified image
resized_img.save("output.jpg")
```

### Image Enhancement
```python
from PIL import Image, ImageEnhance

# Open an image
img = Image.open("input.jpg")

# Enhance contrast
enhancer = ImageEnhance.Contrast(img)
enhanced_img = enhancer.enhance(1.5)  # Increase contrast by 50%

# Enhance brightness
enhancer = ImageEnhance.Brightness(img)
bright_img = enhancer.enhance(1.2)  # Increase brightness by 20%

# Enhance color saturation
enhancer = ImageEnhance.Color(img)
colorful_img = enhancer.enhance(1.3)  # Increase saturation by 30%
```

### Drawing on Images
```python
from PIL import Image, ImageDraw, ImageFont

# Create a new image or open existing one
img = Image.new("RGB", (200, 200), color="white")
draw = ImageDraw.Draw(img)

# Draw shapes
draw.rectangle([20, 20, 180, 180], outline="black", width=2)
draw.ellipse([50, 50, 150, 150], fill="red")
draw.line([0, 0, 200, 200], fill="blue", width=3)

# Add text
try:
    font = ImageFont.truetype("arial.ttf", 20)
except IOError:
    font = ImageFont.load_default()
draw.text((10, 10), "Hello, World!", fill="black", font=font)

# Save the result
img.save("output.png")
```

## Supported Image Formats

PIL/Pillow supports a wide variety of image formats:

### Read and Write
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tiff, .tif)

### Read Only
- EPS
- PS
- ICNS
- SPD
- XPM
- XV

### Write Only
- PALM
- PDF
- XV

## Advanced Features

### Image Sequences and Animation
PIL/Pillow can handle multi-frame images like animated GIFs:
```python
from PIL import Image

# Open an animated GIF
img = Image.open("animation.gif")

# Iterate through frames
for i in range(img.n_frames):
    img.seek(i)
    # Process each frame
    frame = img.copy()
    # ... do something with frame ...
```

### Image Filters
```python
from PIL import Image, ImageFilter

# Open an image
img = Image.open("input.jpg")

# Apply filters
blurred = img.filter(ImageFilter.BLUR)
sharpened = img.filter(ImageFilter.SHARPEN)
edges = img.filter(ImageFilter.FIND_EDGES)
embossed = img.filter(ImageFilter.EMBOSS)
```

### Color Management
PIL/Pillow includes support for color profiles and color space conversions:
```python
from PIL import Image, ImageCms

# Load color profiles
srgb_profile = ImageCms.createProfile("sRGB")
adobe_rgb_profile = ImageCms.createProfile("AdobeRGB1998")

# Transform image from sRGB to Adobe RGB
transform = ImageCms.buildTransformFromOpenProfiles(srgb_profile, adobe_rgb_profile, "RGB", "RGB")
converted_img = ImageCms.applyTransform(img, transform)
```

## Performance Considerations

While PIL/Pillow is powerful and easy to use, for high-performance image processing tasks, consider:
- Using NumPy for vectorized operations on image data
- Utilizing hardware acceleration through libraries like OpenCV
- Processing images in batches
- Using appropriate image formats for your use case

## Installation

Pillow can be installed using pip:
```bash
pip install pillow
```

For the original PIL (not recommended for new projects):
```bash
pip install PIL
```

## Comparison with Alternatives

### OpenCV
- OpenCV is more focused on computer vision and real-time processing
- PIL/Pillow is better for general image manipulation and processing
- OpenCV has better performance for video processing and real-time applications

### scikit-image
- scikit-image is built on NumPy and is part of the SciPy ecosystem
- It offers more advanced algorithms for image analysis
- PIL/Pillow is generally simpler for basic image manipulation tasks

### ImageMagick
- ImageMagick is a command-line tool with bindings for many languages
- PIL/Pillow is a pure Python library that's easier to integrate into Python applications
- ImageMagick may offer better performance for batch processing

## See Also
- [[Pillow (PIL fork)]]
- [[Image processing]]
- [[Computer graphics]]
- [[Digital image]]
- [[File format]]
- [[Graphics file format]]
- [[Python (programming language)]]
- [[NumPy]]
- [[OpenCV]]
- [[scikit-image]]
- [[ImageMagick]]
"
