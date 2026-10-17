from PIL import Image, ImageDraw, ImageFont
import json
import os
import requests
from io import BytesIO


TEMPLATES_DIR = "templates"
PLAYERS_FILE = "players.json"
OUTPUT_DIR = "output"


# ============================================================
# RARITY
# ============================================================

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


# ============================================================
# FONT
# ============================================================

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


# ============================================================
# FIND PLAYER ON ESPN
# ============================================================

def find_player_image(name):

    print(f"  Searching photo for: {name}")

    try:

        url = "https://site.web.api.espn.com/apis/search/v2"

        response = requests.get(
            url,
            params={
                "query": name,
                "limit": 10,
                "sport": "soccer"
            },
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        normalized_name = name.lower().strip()

        for result in results:

            contents = result.get("contents", [])

            for item in contents:

                title = str(
                    item.get("title", "")
                ).lower().strip()

                if normalized_name in title or title in normalized_name:

                    athlete = item.get("athlete", {})

                    player_id = athlete.get("id")

                    if player_id:

                        image_url = (
                            "https://a.espncdn.com/"
                            f"i/headshots/soccer/players/full/"
                            f"{player_id}.png"
                        )

                        print(
                            f"  Found ESPN ID: {player_id}"
                        )

                        return image_url

        print("  Player not found on ESPN.")

    except Exception as e:

        print(f"  ESPN search error: {e}")

    return None


# ============================================================
# DOWNLOAD PLAYER IMAGE
# ============================================================

def download_player_image(url):

    if not url:
        return None

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=20
        )

        response.raise_for_status()

        return Image.open(
            BytesIO(response.content)
        ).convert("RGBA")

    except Exception as e:

        print(f"  Image download error: {e}")

        return None


# ============================================================
# RESIZE PLAYER
# ============================================================

def fit_player_image(image, max_width, max_height):

    image = image.copy()

    image.thumbnail(
        (max_width, max_height),
        Image.Resampling.LANCZOS
    )

    return image


# ============================================================
# CENTERED TEXT
# ============================================================

def draw_centered_text(
    draw,
    text,
    y,
    font,
    width,
    fill="white"
):

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    text_width = bbox[2] - bbox[0]

    x = (width - text_width) // 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill
    )


# ============================================================
# GENERATE CARD
# ============================================================

def generate_card(player):

    name = str(
        player.get("name", "Unknown")
    )

    rating = int(
        player.get("rating", 0)
    )

    position = str(
        player.get("position", "")
    )

    rarity = get_rarity(rating)

    template_path = os.path.join(
        TEMPLATES_DIR,
        f"{rarity}.jpg"
    )

    if not os.path.exists(template_path):

        raise FileNotFoundError(
            f"Template not found: {template_path}"
        )

    print()
    print(f"Generating: {name}")
    print(f"  Rating: {rating}")
    print(f"  Rarity: {rarity.upper()}")

    # --------------------------------------------------------
    # TEMPLATE
    # --------------------------------------------------------

    card = Image.open(
        template_path
    ).convert("RGBA")

    width, height = card.size

    # --------------------------------------------------------
    # PLAYER PHOTO
    # --------------------------------------------------------

    image_url = find_player_image(name)

    player_image = download_player_image(
        image_url
    )

    if player_image:

        player_image = fit_player_image(
            player_image,
            int(width * 0.60),
            int(height * 0.48)
        )

        x = (
            width - player_image.width
        ) // 2

        y = int(
            height * 0.20
        )

        card.alpha_composite(
            player_image,
            (x, y)
        )

        print("  Player photo added.")

    else:

        print(
            "  Player photo unavailable."
        )

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    draw = ImageDraw.Draw(card)

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

    # Rating
    draw.text(
        (
            int(width * 0.12),
            int(height * 0.105)
        ),
        str(rating),
        font=rating_font,
        fill="white"
    )

    # Position
    draw.text(
        (
            int(width * 0.125),
            int(height * 0.185)
        ),
        position,
        font=position_font,
        fill="white"
    )

    # Name
    draw_centered_text(
        draw,
        name.upper(),
        int(height * 0.76),
        name_font,
        width
    )

    # Rarity
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

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    safe_name = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in name
    )

    player_id = str(
        player.get("id", "unknown")
    )

    output_path = os.path.join(
        OUTPUT_DIR,
        f"{player_id}_{safe_name}.png"
    )

    card.convert("RGB").save(
        output_path,
        "PNG"
    )

    print(
        f"  Saved: {output_path}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("              OBSIDIAN XI NFT GENERATOR")
    print("=" * 60)

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

    print(
        f"\nPlayers found: {len(players)}"
    )

    for player in players:

        try:

            generate_card(player)

        except Exception as e:

            print(
                f"\nERROR generating "
                f"{player.get('name', 'UNKNOWN')}:"
            )

            print(e)

    print()
    print("=" * 60)
    print("Generation completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()