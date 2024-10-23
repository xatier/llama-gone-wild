import random

from playwright.sync_api import sync_playwright

PROXY = ""
HAR_FILE = ""
HAR_RECORD_URL = ""
PAGE_URL = ""
ITERATIONS = 100

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="msedge-dev",
        headless=False,
        proxy={"server": PROXY},
    )

    page = browser.new_page()

    # record the responses into the HAR file
    page.route_from_har(
        HAR_FILE,
        url=HAR_RECORD_URL,
        update=True,
        update_content="embed",
    )

    # go to the page
    page.goto(PAGE_URL)
    page.screenshot(path="1.png", full_page=True)

    # click through the pop-ups
    page.get_by_text("Okay").click(button="left")
    page.screenshot(path="2.png", full_page=True)
    page.get_by_text("I'm 18 or older").click(button="left")
    page.screenshot(path="3.png", full_page=True)

    page.wait_for_timeout(2000)

    for i in range(ITERATIONS):
        print(f"iteration {i=}")

        # scroll down some randomized pixels
        a, b = random.randint(0, 10), random.randint(0, 1000)
        print(f"scrolling {1000 * a + b}px (1000*{a}+{b})")
        page.mouse.wheel(0, 10000 * a + b)

        # zzz randomly
        c, d = random.randint(0, 5), random.randint(0, 15000)
        print(f"sleeping {500 * c + d}ms (500*{c}+{d})")
        page.wait_for_timeout(500 * c + d)

        page.screenshot(path=f"{i + 4}.png", full_page=True)

    # save the HAR file into disk
    page.close()

    browser.close()
