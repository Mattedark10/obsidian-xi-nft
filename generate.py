from PIL import Image, ImageDraw, ImageFont
import json
import os
import requests
from io import BytesIO
import re
import unicodedata


# ============================================================
# RARITY
# ============================================================

def get_rarity(rating):
    if rating >= 96:
        return "MYTHIC"
    elif rating >= 90:
        return "LEGENDARY"
    elif rating >= 85:
        return "EPIC"
    elif rating >= 79:
        return "RARE"
    else:
        return "COMMON"


# ============================================================
# FONT
# ============================================================

def load_font(size):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
    ]

    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ============================================================
# FIND PLAYER IMAGE - WIKIPEDIA
# ============================================================

def find_player_image(name):

    print(f"  Searching photo for: {name}")

    headers = {
        "User-Agent": "ObsidianXI-NFT/1.0"
    }

    api_url = "https://en.wikipedia.org/w/api.php"

    # --------------------------------------------------------
    # 1. Try exact Wikipedia title
    # --------------------------------------------------------

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "pageimages",
        "piprop": "thumbnail",
        "pithumbsize": "800",
        "redirects": "1",
        "titles": name
    }

    try:
        response = requests.get(
            api_url,
            params=params,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        pages = data.get("query", {}).get("pages", [])

        for page in pages:

            if page.get("thumbnail", {}).get("source"):
                image_url = page["thumbnail"]["source"]

                print(f"  Found Wikipedia photo: {image_url}")

                return image_url

    except Exception as e:
        print(f"  Wikipedia direct search error: {e}")


    # --------------------------------------------------------
    # 2. Search Wikipedia
    # --------------------------------------------------------

    search_params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "list": "search",
        "srsearch": name,
        "srlimit": 10
    }

    try:

        response = requests.get(
            api_url,
            params=search_params,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("query", {}).get("search", [])

        target = normalize_text(name)

        for result in results:

            title = result.get("title", "")
            normalized_title = normalize_text(title)

            # Prefer a very close title match
            if (
                normalized_title == target
                or target in normalized_title
                or normalized_title in target
            ):

                page_title = title

                image_params = {
                    "action": "query",
                    "format": "json",
                    "formatversion": "2",
                    "prop": "pageimages",
                    "piprop": "thumbnail",
                    "pithumbsize": 800,
                    "redirects": "1",
                    "titles": page_title
                }

                image_response = requests.get(
                    api_url,
                    params=image_params,
                    headers=headers,
                    timeout=15
                )

                image_response.raise_for_status()

                image_data = image_response.json()

                image_pages = image_data.get(
                    "query", {}
                ).get("pages", [])

                for page in image_pages:

                    if page.get("thumbnail", {}).get("source"):

                        image_url = page["thumbnail"]["source"]

                        print(
                            f"  Found Wikipedia photo: {image_url}"
                        )

                        return image_url

    except Exception as e:
        print(f"  Wikipedia search error: {e}")


    print("  Player not found on Wikipedia.")

    return None


# ============================================================
# DOWNLOAD PLAYER IMAGE
# ============================================================

def download_player_image(url):

    if not url:
        return None

    try:

        headers = {
            "User-Agent": "ObsidianXI-NFT/1.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        image = Image.open(
            BytesIO(response.content)
        ).convert("RGBA")

        return image

    except Exception as e:

        print(
            f"  Error downloading player photo: {e}"
        )

        return None


# ============================================================
# FIT PLAYER IMAGE
# ============================================================

def fit_player_image(image, max_width, max_height):

    if image is None:
        return None

    image.thumbnail(
        (max_width, max_height),
        Image.Resampling.LANCZOS
    )

    return image


# ============================================================
# CENTER TEXT
# ============================================================

def draw_centered_text(
    draw,
    text,
    y,
    font,
    fill
):

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    width = bbox[2] - bbox[0]

    x = (draw._image.width - width) / 2

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

    name = player["name"]
    rating = player["rating"]
    position = player["position"]

    rarity = get_rarity(rating)

    print()
    print(f"Generating: {name}")
    print(f"  Rating: {rating}")
    print(f"  Rarity: {rarity}")

    # --------------------------------------------------------
    # TEMPLATE
    # --------------------------------------------------------

    template_path = os.path.join(
        "templates",
        rarity.lower() + ".jpg"
    )

    if not os.path.exists(template_path):

        print(
            f"  ERROR: Template not found: {template_path}"
        )

        return

    card = Image.open(
        template_path
    ).convert("RGBA")

    card_width, card_height = card.size

    draw = ImageDraw.Draw(card)

    # --------------------------------------------------------
    # PLAYER PHOTO
    # --------------------------------------------------------

    image_url = find_player_image(name)

    player_image = download_player_image(
        image_url
    )

    if player_image:

        # Maximum area for player photo
        max_width = int(card_width * 0.65)
        max_height = int(card_height * 0.48)

        player_image = fit_player_image(
            player_image,
            max_width,
            max_height
        )

        if player_image:

            x = (
                card_width
                - player_image.width
            ) // 2

            y = int(
                card_height * 0.17
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

    rating_font = load_font(
        max(30, int(card_width * 0.08))
    )

    position_font = load_font(
        max(20, int(card_width * 0.045))
    )

    name_font = load_font(
        max(22, int(card_width * 0.055))
    )

    rarity_font = load_font(
        max(16, int(card_width * 0.035))
    )

    text_color = (255, 255, 255, 255)

    # Rating
    draw_centered_text(
        draw,
        str(rating),
        int(card_height * 0.07),
        rating_font,
        text_color
    )

    # Position
    draw_centered_text(
        draw,
        position,
        int(card_height * 0.14),
        position_font,
        text_color
    )

    # Player name
    draw_centered_text(
        draw,
        name.upper(),
        int(card_height * 0.73),
        name_font,
        text_color
    )

    # Rarity
    draw_centered_text(
        draw,
        rarity,
        int(card_height * 0.79),
        rarity_font,
        text_color
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    os.makedirs(
        "output",
        exist_ok=True
    )

    safe_name = re.sub(
        r"[^A-Za-z0-9_-]",
        "_",
        name
    )

    output_path = os.path.join(
        "output",
        f"{player['id']}_{safe_name}.png"
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
    print("OBSIDIAN XI NFT GENERATOR")
    print("=" * 60)

    with open(
        "players.json",
        "r",
        encoding="utf-8"
    ) as f:

        players = json.load(f)

    for player in players:

        generate_card(player)

    print()
    print("=" * 60)
    print("Generation completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()