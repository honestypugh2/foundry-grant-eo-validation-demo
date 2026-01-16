"""
Create Azure AI Grant Compliance Logo
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_logo():
    # Create image with Azure blue background
    width, height = 400, 100
    azure_blue = (0, 120, 212)  # Azure brand color
    white = (255, 255, 255)
    
    # Create base image
    img = Image.new('RGB', (width, height), azure_blue)
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fall back to default if not available
    try:
        # Try different font paths
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            'C:\\Windows\\Fonts\\arial.ttf',
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 32)
                break
        
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Draw Azure AI icon (simplified cloud shape)
    # Cloud circle 1
    draw.ellipse([20, 30, 60, 70], fill=white)
    # Cloud circle 2
    draw.ellipse([35, 20, 75, 60], fill=white)
    # Cloud circle 3
    draw.ellipse([50, 30, 90, 70], fill=white)
    # Cloud base
    draw.rectangle([25, 45, 85, 70], fill=white)
    
    # Draw text
    text = "Grant Compliance"
    # Get text size for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Position text
    text_x = 110
    text_y = (height - text_height) // 2 - 5
    
    draw.text((text_x, text_y), text, fill=white, font=font)
    
    # Draw AI subtitle
    try:
        small_font = ImageFont.truetype(font_paths[0], 16) if os.path.exists(font_paths[0]) else ImageFont.load_default()
    except:
        small_font = ImageFont.load_default()
    
    subtitle = "Powered by Azure AI"
    draw.text((text_x, text_y + 35), subtitle, fill=white, font=small_font)
    
    return img

if __name__ == "__main__":
    # Create assets directory if it doesn't exist
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    
    # Generate and save logo
    logo = create_logo()
    output_path = os.path.join(os.path.dirname(__file__), 'logo.png')
    logo.save(output_path)
    print(f"✓ Logo created: {output_path}")
