import re
import httpx
import json
from pyquery import PyQuery as pq
from pathlib import Path
import asyncclick as click

BASE_URL = "https://pop-life.com/foursouls"


def get_cards_count(html):
    stacks = []

    def parse_single_stack(index, element):
        q = pq(element)
        stack_title = re.split(r"[ ](?=x\d+)", q("a").text())[0]
        count = int(q("a > small").text()[1:])
        stacks.append({"title": stack_title, "count": count})

    q = pq(html)
    q("div.container > ul.headmenu").find("li").each(parse_single_stack)

    total = sum(item["count"] for item in stacks)

    return (total, stacks)


@click.command()
@click.option("--file", "file_name", default="cards.json", type=click.Path())
def checker(file_name):
    # card_images = Path("../../Originals").glob("*.png")
    data_file_path = Path(file_name)

    with open(data_file_path, "r") as readable_file_stream:
        data = json.load(readable_file_stream)
        client = httpx.Client()
        response = client.get(BASE_URL)
        total, _ = get_cards_count(response.text)

        print(f"Card count: {len(data.get('cards'))}/{total}")
