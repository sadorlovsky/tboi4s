import asyncclick as click
from downloader import fetch, download
from checker import checker

@click.group()
def cli():
    pass

cli.add_command(fetch)
cli.add_command(download)
cli.add_command(checker)

if __name__ == "__main__":
    cli()