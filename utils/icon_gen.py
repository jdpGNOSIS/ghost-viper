import os
import sys
import struct
import zlib
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def _create_png(width, height, pixels):
    """Create a minimal PNG from raw RGBA pixel data."""
    def write_chunk(chunk_type, data):
        chunk = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
        return struct.pack('>I', len(data)) + chunk + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)

    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'
        for x in range(width):
            idx = (y * width + x) * 4
            raw_data += bytes(pixels[idx:idx+4])

    compressed = zlib.compress(raw_data)

    return header + write_chunk(b'IHDR', ihdr) + write_chunk(b'IDAT', compressed) + write_chunk(b'IEND', b'')

def _make_ghost_viper_icon(size=256):
    """Generate a custom Jake the Snake / hacking icon with RGBA data."""
    pixels = []
    cx, cy = size // 2, size // 2
    r = size // 3
    eye_r = size // 12

    for y in range(size):
        for x in range(size):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            angle = __import__('math').atan2(y - cy, x - cx)

            # Snake body spiral
            spiral_factor = 1.0 + 0.3 * __import__('math').sin(angle * 3 + dist * 0.02)
            if dist < r * spiral_factor and dist > r * 0.3:
                # Snake scales pattern
                scale_pattern = ((x // 8 + y // 8) % 2 == 0)
                if scale_pattern:
                    r_c, g_c, b_c = 0, 200, 0  # Bright green
                else:
                    r_c, g_c, b_c = 0, 100, 0  # Dark green
            elif dist < eye_r * 1.5 and abs(x - cx) < eye_r * 2 and y < cy:
                # Eyes - red glowing
                eye_center_x = cx + (-eye_r if x < cx else eye_r)
                eye_dist = ((x - eye_center_x) ** 2 + (y - (cy - r * 0.5)) ** 2) ** 0.5
                if eye_dist < eye_r:
                    r_c, g_c, b_c = 255, 0, 0  # Red eye
                else:
                    r_c, g_c, b_c = 0, 60, 0
            elif dist < r and y > cy:
                # Mouth area - fangs
                if abs(x - cx) < 6 and y > cy + r * 0.3 and y < cy + r * 0.6:
                    r_c, g_c, b_c = 255, 255, 255  # Fang
                else:
                    r_c, g_c, b_c = 0, 30, 0
            else:
                # Background - dark with gradient
                bg_factor = 1.0 - min(dist / size, 1.0)
                r_c = int(5 + bg_factor * 10)
                g_c = int(5 + bg_factor * 15)
                b_c = int(10 + bg_factor * 20)

            # Russian flag tint overlay in a subtle pattern
            if y < size // 3:
                r_c = min(r_c + 8, 255)
            elif y < 2 * size // 3:
                g_c = min(g_c + 8, 255)
            else:
                b_c = min(b_c + 8, 255)

            # Glow effect around snake
            if r * 0.95 < dist < r * 1.05 and (y < cy or True):
                glow = int(20 * __import__('math').sin(angle * 6 + dist * 0.1) ** 2)
                r_c = min(r_c + glow, 255)
                g_c = min(g_c + glow, 200)

            pixels.extend([max(0, min(255, r_c)), max(0, min(255, g_c)), max(0, min(255, b_c)), 255])

    return pixels

def generate_app_icon(output_path=None):
    if output_path is None:
        output_path = os.path.join(os.environ.get('GHOST_VIPER_ROOT', os.path.expanduser('~')), 'assets', 'ghost_viper_icon.png')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pixels = _make_ghost_viper_icon(256)
    png_data = _create_png(256, 256, pixels)
    with open(output_path, 'wb') as f:
        f.write(png_data)
    return output_path

def generate_small_icon(output_path=None):
    if output_path is None:
        output_path = os.path.join(os.environ.get('GHOST_VIPER_ROOT', os.path.expanduser('~')), 'assets', 'ghost_viper_small.ico')
    from PIL import Image
    png_path = generate_app_icon()
    img = Image.open(png_path)
    img.save(output_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return output_path
