from PIL import Image
import pytesseract
from pathlib import Path
import json


def main():
    card_images = Path("../../Originals").glob("*.png")
    data_file_path = Path("../../cards.json")

    with open(data_file_path, "r") as readable_file_stream:
        cards_data = json.load(readable_file_stream).get("cards")

        for card_image in card_images:
            card_id = card_image.name.split(" ")[0]
            card_text = pytesseract.image_to_string(Image.open(card_image))
            card_to_update = next(
                item for item in cards_data if int(item["id"]) == int(card_id)
            )
            card_to_update["text"] = card_text

        with open(data_file_path, "w") as writeable_file_stream:
            json.dump(cards_data, writeable_file_stream, indent=2)


main()