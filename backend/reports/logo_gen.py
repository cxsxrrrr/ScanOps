"""Generate Vigia logo PNG (recreates frontend sidebar brand: gradient + shield + 'Vigia' wordmark)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def _find_bold_font(size):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _linear_gradient(size, start_rgb, end_rgb, direction="diagonal"):
    """Top-left -> bottom-right diagonal gradient."""
    w, h = size
    base = Image.new("RGB", size, start_rgb)
    px = base.load()
    sx = float(end_rgb[0] - start_rgb[0])
    sy = float(end_rgb[1] - start_rgb[1])
    sz = float(end_rgb[2] - start_rgb[2])
    for y in range(h):
        for x in range(w):
            t = (x / max(w - 1, 1) + y / max(h - 1, 1)) / 2.0
            px[x, y] = (
                int(start_rgb[0] + sx * t),
                int(start_rgb[1] + sy * t),
                int(start_rgb[2] + sz * t),
            )
    return base


def _rounded_alpha_mask(size, radius):
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([(0, 0), (size[0] - 1, size[1] - 1)], radius=radius, fill=255)
    return mask


def _draw_shield(draw, cx, cy, w, h, fill, stroke_width=None):
    """Outlined shield-check glyph (lucide ShieldCheck style) centered at (cx, cy).

    Drawn as an outline, not a solid fill, so the checkmark stays visible
    against it instead of disappearing into a same-color fill.
    """
    left = cx - w // 2
    top = cy - h // 2
    right = left + w
    bottom = top + h
    points = [
        (cx, top),
        (right, top + int(h * 0.18)),
        (right, top + int(h * 0.62)),
        (cx, bottom),
        (left, top + int(h * 0.62)),
        (left, top + int(h * 0.18)),
    ]
    sw = stroke_width or max(3, w // 14)
    draw.line(points + [points[0]], fill=fill, width=sw, joint="curve")
    # Check mark inside
    cm_w = int(w * 0.45)
    cm_h = int(h * 0.30)
    cm_cx = cx
    cm_cy = cy + int(h * 0.05)
    p1 = (cm_cx - cm_w // 2, cm_cy)
    p2 = (cm_cx - cm_w // 6, cm_cy + cm_h // 2)
    p3 = (cm_cx + cm_w // 2, cm_cy - cm_h // 2)
    draw.line([p1, p2, p3], fill=fill, width=sw, joint="curve")


def build_logo(width=420, height=120, out_path=None):
    import os
    if out_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        out_path = os.path.join(here, "static", "logo_vigia.png")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out_path_rgba = out_path.replace(".png", "_rgba.png")

    # Supersample at 4x then downscale — kills the jagged/halo look the
    # single-pass render had around the shield box and checkmark.
    ss = 4
    W, H = width * ss, height * ss
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Shield box (gradient) — no drop shadow: the PDF/Excel canvas is always
    # a flat white page, so the soft blurred shadow the sidebar uses just
    # showed up as a smudgy halo instead of a shadow.
    box_size = 84 * ss
    box_x = 6 * ss
    box_y = (H - box_size) // 2
    grad = _linear_gradient(
        (box_size, box_size), (37, 99, 235), (124, 58, 237)
    )
    mask = _rounded_alpha_mask((box_size, box_size), radius=18 * ss)
    img.paste(grad, (box_x, box_y), mask)
    draw = ImageDraw.Draw(img)

    # Shield icon on box
    _draw_shield(draw, box_x + box_size // 2, box_y + box_size // 2, 52 * ss, 60 * ss, fill=(255, 255, 255))

    # Emerald status dot
    dot_d = 14 * ss
    dot_x = box_x + box_size - dot_d // 2 - 4 * ss
    dot_y = box_y - 2 * ss
    draw.ellipse(
        [(dot_x, dot_y), (dot_x + dot_d, dot_y + dot_d)],
        fill=(52, 211, 153, 255),
        outline=(255, 255, 255, 255),
        width=2 * ss,
    )

    img = img.resize((width, height), Image.LANCZOS)
    draw = ImageDraw.Draw(img)

    # Back to logical (non-supersampled) units for the text pass below.
    box_size = 84
    box_x = 6

    # Wordmark "Vigia" — gradient text
    word_font = _find_bold_font(52)
    text = "Vigia"
    # Measure
    try:
        tb = draw.textbbox((0, 0), text, font=word_font)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        tx_off = tb[0]
        ty_off = tb[1]
    except AttributeError:
        tw, th = draw.textsize(text, font=word_font)
        tx_off, ty_off = 0, 0

    text_x = box_x + box_size + 16
    text_y = (height - th) // 2 - ty_off

    # Gradient text via second layer with mask
    text_layer = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(text_layer)
    tdraw.text((2 - tx_off, 2 - ty_off), text, font=word_font, fill=(255, 255, 255, 255))
    text_alpha = text_layer.getchannel("A")
    grad_text = _linear_gradient((tw + 4, th + 4), (96, 165, 250), (192, 132, 252))
    grad_text.putalpha(text_alpha)
    img.paste(grad_text, (text_x, text_y), text_alpha)

    # Subtitle
    sub_font = _find_bold_font(14)
    sub_text = "CYBERSECURITY AUDITING"
    try:
        sb = draw.textbbox((0, 0), sub_text, font=sub_font)
        sw = sb[2] - sb[0]
    except AttributeError:
        sw = draw.textsize(sub_text, font=sub_font)[0]
    sub_x = text_x + 4
    sub_y = text_y + th + 4
    sub_color = (148, 163, 184, 255)
    draw.text((sub_x, sub_y), sub_text, font=sub_font, fill=sub_color)

    # Keep RGBA original aside (for web/sidebar) and also save a flattenable copy
    img.save(out_path_rgba, format="PNG")

    # Flatten alpha onto white background for crisp rendering in PDF / Excel
    # (ReportLab and openpyxl do not reliably preserve alpha; white also
    # matches the PDF page background, avoiding black boxes around the logo.)
    flat_bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    flat_bg = Image.alpha_composite(flat_bg, img).convert("RGB")
    flat_bg.save(out_path, format="PNG")
    print(f"Logo saved: {out_path} ({img.size}, RGB on white)")


if __name__ == "__main__":
    build_logo()