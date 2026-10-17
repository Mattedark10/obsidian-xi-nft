from PIL import Image, ImageDraw, ImageFont
import json
import os


# ============================================================
# OBSIDIAN XI NFT GENERATOR
# ============================================================

TEMPLATES_DIR = "templates"
PLAYERS_FILE = "players.json"
OUTPUT_DIR = "output"


# ------------------------------------------------------------
# RARITY
# ------------------------------------------------------------

def get_rarity(rating):
    rating = int(rating)

    if rating >= 96:
        return "mythic"
    elif rating >= 90:
        return "legendary"
    elif rating >= 85:
        return "epic"
    elif rating >= 79:
        return "rare"
    else:
        return "common"


# ------------------------------------------------------------
# FONT
# ------------------------------------------------------------

def load_font(size, bold=False):
    fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    ]

    for path in fonts:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


# ------------------------------------------------------------
# CENTER TEXT
# ------------------------------------------------------------

def draw_centered_text(draw, text, y, font, width, fill="white"):
    bbox = draw.textbbox((0, 0), text, font=font)

    text_width = bbox[2] - bbox[0]

    x = (width - text_width) // 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill
    )


# ------------------------------------------------------------
# GENERATE CARD
# ------------------------------------------------------------

def generate_card(player):

    name = str(player.get("name", "Unknown"))
    rating = int(player.get("rating", 0))
    position = str(player.get("position", ""))

    rarity = get_rarity(rating)

    template_path = os.path.join(
        TEMPLATES_DIR,
        f"{rarity}.jpg"
    )

    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Template not found: {template_path}"
        )

    print(f"\nGenerating: {name}")
    print(f"  Rating: {rating}")
    print(f"  Rarity: {rarity.upper()}")

    # --------------------------------------------------------
    # LOAD TEMPLATE
    # --------------------------------------------------------

    card = Image.open(template_path).convert("RGBA")

    width, height = card.size

    draw = ImageDraw.Draw(card)

    # --------------------------------------------------------
    # FONTS
    # --------------------------------------------------------

    rating_font = load_font(
        max(24, int(width * 0.075)),
        bold=True
    )

    position_font = load_font(
        max(18, int(width * 0.045)),
        bold=True
    )

    name_font = load_font(
        max(18, int(width * 0.045)),
        bold=True
    )

    rarity_font = load_font(
        max(14, int(width * 0.032)),
        bold=True
    )

    title_font = load_font(
        max(14, int(width * 0.025)),
        bold=True
    )

    # --------------------------------------------------------
    # RATING
    # --------------------------------------------------------

    draw.text(
        (
            int(width * 0.12),
            int(height * 0.105)
        ),
        str(rating),
        font=rating_font,
        fill="white"
    )

    # --------------------------------------------------------
    # POSITION
    # --------------------------------------------------------

    draw.text(
        (
            int(width * 0.125),
            int(height * 0.185)
        ),
        position,
        font=position_font,
        fill="white"
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    draw_centered_text(
        draw,
        "OBSIDIAN XI",
        int(height * 0.70),
        title_font,
        width
    )

    # --------------------------------------------------------
    # PLAYER NAME
    # --------------------------------------------------------

    draw_centered_text(
        draw,
        name.upper(),
        int(height * 0.76),
        name_font,
        width
    )

    # --------------------------------------------------------
    # RARITY
    # --------------------------------------------------------

    draw_centered_text(
        draw,
        rarity.upper(),
        int(height * 0.83),
        rarity_font,
        width
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    safe_name = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in name
    )

    player_id = str(player.get("id", "unknown"))

    output_path = os.path.join(
        OUTPUT_DIR,
        f"{player_id}_{safe_name}.png"
    )

    card.convert("RGB").save(
        output_path,
        "PNG"
    )

    print(f"  Saved: {output_path}")


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    print("=" * 60)
    print("              OBSIDIAN XI NFT GENERATOR")
    print("=" * 60)

    if not os.path.exists(PLAYERS_FILE):
        raise FileNotFoundError(
            f"{PLAYERS_FILE} not found"
        )

    with open(
        PLAYERS_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        players = json.load(f)

    if not isinstance(players, list):
        raise ValueError(
            "players.json must contain an array"
        )

    print(f"\nPlayers found: {len(players)}")

    for player in players:

        try:
            generate_card(player)

        except Exception as e:

            print(
                f"\nERROR generating "
                f"{player.get('name', 'UNKNOWN')}:"
            )

            print(e)

    print("\n" + "=" * 60)
    print("Generation completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()