#!/usr/bin/env python3
"""Draw the 25 November 2026 front page as a 680x1024 PNG.

THE WORLD IN A DAY: one day on one page. A broadsheet front page with a
nameplate and dateline, a lead story on Shenzhou-24 with a tall portrait
file photo of a Long March 2F launch, two stories below it (Asia's
Wednesday market slide, the Bogor mine rescue) with small photos, and an
"Also today" strip of three briefs. Everything is drawn with Pillow at
double size and shrunk with LANCZOS so the small type stays sharp when
the page is read at 300 pixels across.

The photographs are real freely licensed file photos (none taken today);
the words are the day's verified news. Run from the repository root:

    python3 tools/render.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SS = 2                                  # supersample factor
PAGE = (680 * SS, 1024 * SS)
SIDE = 30 * SS                          # side margin
INNER = PAGE[0] - 2 * SIDE              # text width

PAPER = (247, 243, 232)
SHADE = (232, 227, 214)
INK = (18, 18, 18)
RED = (158, 28, 32)
MUTED = (96, 91, 82)
RULE = (150, 143, 128)

F_SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
F_SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
F_SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
F_SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
F_SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def face(path, pts):
    return ImageFont.truetype(path, pts * SS)


def wrap(draw, text, font, width):
    """Greedy word wrap into lines no wider than width."""
    out, current = [], ""
    for word in text.split():
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font) <= width:
            current = trial
        else:
            if current:
                out.append(current)
            current = word
    if current:
        out.append(current)
    return out


def para(draw, text, font, x, y, width, leading, color=INK):
    """Draw a wrapped paragraph; return the y just below it."""
    for line in wrap(draw, text, font, width):
        draw.text((x, y), line, font=font, fill=color)
        y += leading
    return y


def fill_frame(path, target_w, target_h, anchor_y=0.5, anchor_x=0.5):
    """Centre-crop a photo to the target frame, honouring an anchor."""
    img = Image.open(path).convert("RGB")
    sw, sh = img.size
    scale = max(target_w / sw, target_h / sh)
    img = img.resize((round(sw * scale), round(sh * scale)), Image.LANCZOS)
    w, h = img.size
    left = int((w - target_w) * anchor_x)
    top = int((h - target_h) * anchor_y)
    return img.crop((left, top, left + target_w, top + target_h))


def rule(draw, y, weight=1):
    draw.line([(SIDE, y), (PAGE[0] - SIDE, y)], fill=RULE, width=weight * SS)


def kicker(draw, text, x, y):
    f = face(F_SANS_B, 12)
    draw.text((x, y), text, font=f, fill=RED)
    return y + int(20 * SS)


def headline(draw, text, font, x, y, width, leading):
    for line in wrap(draw, text, font, width):
        draw.text((x, y), line, font=font, fill=INK)
        y += leading
    return y


def build():
    page = Image.new("RGB", PAGE, PAPER)
    d = ImageDraw.Draw(page)
    x0 = SIDE
    x1 = PAGE[0] - SIDE
    y = 16 * SS

    # --- Nameplate -------------------------------------------------------
    dateline = "WEDNESDAY, 25 NOVEMBER 2026  ·  ONE DAY'S NEWS ON ONE PAGE"
    f_date = face(F_SANS_B, 12)
    d.text(((PAGE[0] - d.textlength(dateline, font=f_date)) / 2, y),
           dateline, font=f_date, fill=MUTED)
    y += int(22 * SS)
    name = "THE WORLD IN A DAY"
    f_name = face(F_SERIF_B, 50)
    d.text(((PAGE[0] - d.textlength(name, font=f_name)) / 2, y),
           name, font=f_name, fill=INK)
    y += int(60 * SS)
    d.line([(x0, y), (x1, y)], fill=INK, width=3 * SS)
    y += int(4 * SS)
    d.line([(x0, y), (x1, y)], fill=INK, width=1 * SS)
    y += int(10 * SS)

    # --- Lead story: Shenzhou-24 -----------------------------------------
    # Left column: kicker, headline, deck, body. Right column: photo.
    photo_w = 292 * SS
    photo_h = 330 * SS
    gap = 18 * SS
    col_w = INNER - photo_w - gap

    y_lead = y
    y = kicker(d, "SPACE  —  JIUQUAN, CHINA", x0, y)
    y = headline(d, "Pakistan's first astronaut reaches orbit "
                    "as Shenzhou-24 docks with Tiangong",
                 face(F_SERIF_B, 30), x0, y, col_w, int(35 * SS))
    y += int(8 * SS)
    deck = ("A Long March 2F lifted off at 8:18 a.m. Beijing time, "
            "carrying three crew — and the first foreign visitor to "
            "China's space station.")
    y = para(d, deck, face(F_SERIF_I, 15), x0, y, col_w, int(21 * SS),
             color=MUTED)
    y += int(10 * SS)
    body = ("China's Shenzhou-24 launched on Wednesday morning and "
            "docked with the Tiangong station at 11:56 a.m. Aboard "
            "were commander Tang Hongbo, flight engineer Wu Yi and "
            "Pakistani payload specialist Muhammad Zeeshan Ali, 40 — "
            "the first Pakistani in orbit and the first foreign "
            "astronaut to visit Tiangong. He will spend five to ten "
            "days aboard running experiments, then return to Earth "
            "on Shenzhou-23.")
    y = para(d, body, face(F_SERIF, 14), x0, y, col_w, int(20 * SS))

    photo = fill_frame(os.path.join(REPO, "assets", "rocket.jpg"),
                       photo_w, photo_h, anchor_y=0.42)
    page.paste(photo, (x1 - photo_w, y_lead))
    d.rectangle([x1 - photo_w, y_lead, x1, y_lead + photo_h],
                outline=INK, width=1 * SS)
    cap = "File photo: a Long March 2F lifts off from Jiuquan. Shenzhou-24 flew the same rocket."
    cy = y_lead + photo_h + int(5 * SS)
    cy = para(d, cap, face(F_SERIF_I, 10), x1 - photo_w, cy, photo_w,
              int(13 * SS), color=MUTED)

    y = max(y, cy) + int(10 * SS)
    rule(d, y, 1)
    y += int(12 * SS)

    # --- Two stories side by side ----------------------------------------
    half = (INNER - 20 * SS) // 2
    sub_h = 128 * SS
    stories = [
        ("MARKETS  —  TOKYO & SEOUL",
         "Asia's shares slide as the tariff threat returns",
         "Asian shares tumbled on Wednesday as fresh US tariff "
         "threats soured sentiment. Japan's Nikkei 225 fell as much "
         "as 2.9%, South Korea's Kospi sank 5.3% and Taiwan dropped "
         "5.1%. Washington is preparing findings from a trade probe "
         "into 16 partners that could bring new import duties.",
         "markets.jpg",
         "File photo: the market centre at the Tokyo Stock Exchange."),
        ("INDONESIA  —  BOGOR, WEST JAVA",
         "Race to reach 26 miners trapped in a flooded gold mine",
         "Rescuers were searching on Wednesday for 26 miners still "
         "trapped in a flooded illegal gold mine near Bogor. Heavy "
         "rain on Monday night sent river water into two shafts 100 "
         "metres deep; 11 of about 30 men inside escaped. A "
         "landslide at 30 metres has slowed the rescue.",
         "mine.jpg",
         "File photo: a flooded gold-mine tunnel."),
    ]
    row_top = y
    row_bottom = y
    for i, (kick, head, text, img_name, cap) in enumerate(stories):
        cx = x0 + i * (half + 20 * SS)
        yy = kicker(d, kick, cx, row_top)
        yy = headline(d, head, face(F_SERIF_B, 17), cx, yy, half,
                      int(21 * SS))
        yy += int(6 * SS)
        pic = fill_frame(os.path.join(REPO, "assets", img_name),
                         half, sub_h, anchor_y=0.45)
        page.paste(pic, (cx, yy))
        d.rectangle([cx, yy, cx + half, yy + sub_h], outline=INK,
                    width=1 * SS)
        yy += sub_h + int(5 * SS)
        yy = para(d, cap, face(F_SERIF_I, 10), cx, yy, half,
                  int(13 * SS), color=MUTED)
        yy += int(4 * SS)
        yy = para(d, text, face(F_SERIF, 12), cx, yy, half,
                  int(17 * SS))
        row_bottom = max(row_bottom, yy)

    y = row_bottom + int(10 * SS)
    rule(d, y, 1)
    y += int(10 * SS)

    # --- Also today: three briefs -----------------------------------------
    d.text((x0, y), "ALSO TODAY", font=face(F_SANS_B, 12), fill=RED)
    y += int(20 * SS)
    briefs = [
        ("SAHEL",
         "Insurgents across Mali, Burkina Faso and Niger are waging "
         "war with off-the-shelf drones, a Reuters investigation "
         "published today finds. One jihadist alliance has carried "
         "out 187 drone attacks since 2023."),
        ("SYDNEY",
         "Australia's October inflation came in hotter than "
         "expected: the trimmed mean was 3.8%, piling pressure on "
         "the Reserve Bank, which has raised rates 125 basis "
         "points this year."),
        ("ANTIQUE",
         "A magnitude 5.1 earthquake struck the Philippine "
         "province of Antique at 7:29 a.m. local time on "
         "Wednesday, ABS-CBN News reported."),
    ]
    third = (INNER - 2 * 16 * SS) // 3
    strip_top = y
    strip_bottom = y
    for i, (place, text) in enumerate(briefs):
        cx = x0 + i * (third + 16 * SS)
        yy = strip_top
        d.text((cx, yy), place, font=face(F_SANS_B, 11), fill=RED)
        yy += int(17 * SS)
        yy = para(d, text, face(F_SERIF, 11.5), cx, yy, third,
                  int(15 * SS))
        strip_bottom = max(strip_bottom, yy)
    y = strip_bottom + int(10 * SS)

    # --- Footer ------------------------------------------------------------
    rule(d, y, 1)
    y += int(8 * SS)
    foot = ("Sources: Reuters, Xinhua, West Java Police, ABS-CBN News. "
            "All photographs are file photos, not taken today. "
            "The World in a Day — 25 November 2026.")
    fw = face(F_SANS, 9.5)
    d.text(((PAGE[0] - d.textlength(foot, font=fw)) / 2, y), foot,
           font=fw, fill=MUTED)

    out = page.resize((680, 1024), Image.LANCZOS)
    out.save(os.path.join(REPO, "entry.png"), optimize=True)
    print("wrote entry.png", out.size)


if __name__ == "__main__":
    build()
