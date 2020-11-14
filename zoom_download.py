from playwright import sync_playwright

from time import sleep
import json
import os
import glob

DEFAULT_OUTPUT_PATH = "."

# This seems unlikely to change in the near future
FILE_COUNT = 3


def do_download(playwright, input_file, output_path, force):

    try:
        with open(input_file) as input_file:
            queue = json.load(input_file)
    except FileNotFoundError:
        print(f"{input_file} not found")
        return

    browser = playwright.chromium.launch(headless=True)
    context = browser.newContext(acceptDownloads=True)

    for item in filter(lambda v: not "downloaded" in v or not v["downloaded"], queue):
        print(f"Downloading files for \"{item['name']}\":")

        if not force:
            existing_downloads = glob.glob(
                f"{os.path.join(output_path, item['name'])}*"
            )
            if existing_downloads:
                print(
                    f"Found downloads for {item['name']}: {', '.join(existing_downloads)}, use -f to overwrite"
                )
                continue

        page = context.newPage()
        page.goto(item["url"])

        page.fill('input[name="password"]', item["password"])
        page.mouse

        with page.expect_navigation():
            page.click("text=/.*Access Recording.*/")

        page.click(".download-btn")

        downloads = []

        for _ in range(3):
            with page.expect_download() as download_info:
                downloads.append(download_info.value)

        for download in downloads:
            filename = f"{item['name']}.{download.suggestedFilename.split('.')[-1]}"
            print(f"\t{filename}")
            download.saveAs(os.path.join(output_path, filename))

        page.close()

    context.close()
    browser.close()

    print("Done")


def download(input_file, output_path, force=False):
    with sync_playwright() as playwright:
        do_download(playwright, input_file, output_path, force)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download Zoom recording")
    parser.add_argument(
        "input",
        help="input JSON download queue file",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        nargs="?",
        default=DEFAULT_OUTPUT_PATH,
        help="output directory",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="overwrite existing downloads",
    )

    args = parser.parse_args()

    download(args.input, args.output, args.force)
