import os
import sys
import asyncio
import httpx
import json
from pathlib import Path
from pyquery import PyQuery as pq
import urllib.parse as urlparse
from urllib.parse import parse_qs
from operator import itemgetter
from PIL import Image
from io import BytesIO
import asyncclick as click
from rich.console import Console
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn
import jsonstreams

console = Console()

BASE_URL = "https://pop-life.com/foursouls"
STACKS = {
    "treasure": f"{BASE_URL}/treasure-card.php",
    "loot": f"{BASE_URL}/loot-card.php",
    "monster": f"{BASE_URL}/monster-card.php",
    "character": f"{BASE_URL}/character-card.php",
    "starting_item": f"{BASE_URL}/starting-item.php",
    "bonus_souls": f"{BASE_URL}/bonus-soul.php",
    "expansion_pack": f"{BASE_URL}/expansion-pack.php",
    "four_souls_plus": f"{BASE_URL}/new-expansion-pack.php",
}


def get_pages(html):
    q = pq(html)
    pagination = q("ul.pagination").html()

    if pagination == None:
        return 1

    q = pq(pagination)
    last_page = q("li:last > a").attr("href")

    last_page_url = urlparse.urlparse(last_page)
    return parse_qs(last_page_url.query)["page"][0]


def parse_page(html, stack):
    cards = []

    def parse_single_card(index, element):
        q = pq(element)

        card_url = q("a").attr("href")
        card_id = int(parse_qs(urlparse.urlparse(card_url).query)["id"][0])

        img = q("img").attr("src")
        img_url = f"{BASE_URL}/{img}"

        title = q("h2").text()
        cards.append({"id": card_id, "img": img_url, "title": title, "stack": stack})

    q = pq(html)
    q(".pageContent > .container > .row").find(".single-team").each(parse_single_card)

    return cards


@click.group()
def cli():
    pass


@click.command()
@click.option("--file", "file_name", default="cards.json", type=click.Path())
@click.option("--rewrite", is_flag=True)
async def fetch(file_name, rewrite):
    if not Path(file_name).exists() or rewrite:
        async with httpx.AsyncClient() as client:
            with jsonstreams.Stream(
                jsonstreams.Type.object, filename=file_name, indent=2, pretty=True
            ) as file_stream:
                with file_stream.subarray("cards") as cards:
                    for stack, url in STACKS.items():
                        console.print(f"Fetching {stack}")
                        response = await client.get(url)
                        pages = int(get_pages(response.text))
                        for page in range(1, pages + 1):
                            page_url = f"{url}?page={page}"
                            response = await client.get(page_url)
                            page_cards = parse_page(response.text, stack)
                            cards.iterwrite(page_cards)
    else:
        message = (
            f"File [bold magenta]{file_name}[/bold magenta] already exists!\n\n"
            "If you want to rewrite, use [bold yellow]--rewrite[/bold yellow] option.\n"
            "You can also specify different file name with [bold yellow]--file [FILENAME][/bold yellow] option."
        )
        console.print(message)


@click.command()
@click.option("--file", "file_name", default="cards.json", type=click.Path())
@click.option("--path", "directory", default="cards", type=click.Path())
@click.option("--rewrite", is_flag=True)
async def download(file_name, directory, rewrite):
    try:
        with open(file_name, "r") as file_stream:
            data = json.load(file_stream)
            if not Path(directory).exists():
                Path(directory).mkdir()
            async with httpx.AsyncClient() as client:
                for card in data.get("cards", []):
                    image_name = f"{card.get('id')} {card.get('title')}.png".replace(
                        "/", "-"
                    )
                    if not Path(f"{directory}/{image_name}").exists() or rewrite:
                        response = await client.get(card.get("img"))
                        img = Image.open(BytesIO(response.content))
                        img.save(Path(f"{directory}/{image_name}"))
    except FileNotFoundError as error:
        print("File doesn't exist", error)
    except json.decoder.JSONDecodeError as error:
        print("JSON parsing error", error)
    except:
        print("Error", sys.exc_info()[0])
    finally:
        print("Finished")


cli.add_command(fetch)
cli.add_command(download)

if __name__ == "__main__":
    cli()
