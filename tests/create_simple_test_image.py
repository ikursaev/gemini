#!/usr/bin/env python3
"""Create a simple test image for testing the Document Extractor."""

import sys

from PIL import Image, ImageDraw, ImageFont


def create_test_image():
    """Create a simple test image with text content."""
    # Create a white image
    width, height = 800, 600
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Try to use a basic font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        small_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16
        )
    except (OSError, IOError):
        # Fallback to default font
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Add text content
    y_position = 50
    line_height = 40
    small_line_height = 25

    # Title
    draw.text(
        (50, y_position), "Document Extractor Test Image", fill="black", font=font
    )
    y_position += line_height + 20

    # Content
    content_lines = [
        "This is a test image for the Document Extractor application.",
        "",
        "Test Features:",
        "• Task persistence across page reloads",
        "• Colorful badge counters for task states",
        "• Modern button styling with hover effects",
        "• Enhanced error handling and state management",
        "",
        "Date: July 4, 2025",
        "Application: Document Extractor",
        "Test Type: Task Management UI Enhancement",
        "",
        "The AI should be able to extract this text content",
        "and process it through the improved task system.",
    ]

    for line in content_lines:
        if line:  # Skip empty lines for drawing but keep spacing
            draw.text((50, y_position), line, fill="black", font=small_font)
        y_position += small_line_height

    # Save the image
    image.save("/workspace/test_image.png")
    print("✅ Test image created: test_image.png")


if __name__ == "__main__":
    try:
        create_test_image()
    except Exception as e:
        print(f"❌ Error creating test image: {e}")
        sys.exit(1)
