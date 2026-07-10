"""Generate placeholder README screenshots.

These are temporary visuals for the README. Replace them with real app
screenshots once the frontend can be rendered reliably in this environment.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PAGES = [
    ("chat", "Chat"),
    ("documents", "Documents"),
    ("upload", "Upload"),
    ("dashboard", "Dashboard"),
    ("evaluate", "Evaluate"),
    ("login", "Login"),
]

WIDTH, HEIGHT = 800, 450
OUTPUT_DIR = Path(__file__).parent


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def gradient_background(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    top = hex_to_rgb("#0f172a")
    bottom = hex_to_rgb("#1e293b")
    for y in range(height):
        ratio = y / height
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)


def make_placeholder(filename: str, label: str) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), "#0f172a")
    draw = ImageDraw.Draw(img)
    gradient_background(draw, WIDTH, HEIGHT)

    # Try to use a nice font, fall back to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        subtitle_font = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = title_font

    # Title
    bbox = draw.textbbox((0, 0), label, font=title_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text(
        ((WIDTH - text_width) // 2, (HEIGHT - text_height) // 2 - 30),
        label,
        fill="#f8fafc",
        font=title_font,
    )

    # Subtitle
    sub = "AI Document Q&A"
    bbox = draw.textbbox((0, 0), sub, font=subtitle_font)
    sub_width = bbox[2] - bbox[0]
    draw.text(
        ((WIDTH - sub_width) // 2, (HEIGHT + text_height) // 2),
        sub,
        fill="#94a3b8",
        font=subtitle_font,
    )

    out_path = OUTPUT_DIR / filename
    img.save(out_path, "PNG")
    print(f"Saved {out_path}")


if __name__ == "__main__":
    for name, label in PAGES:
        make_placeholder(f"{name}.png", label)
