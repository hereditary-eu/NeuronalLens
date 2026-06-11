#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pypdf",
#   "selenium",
#   "Pillow",
# ]
# ///
import base64
import io
import time
import traceback

import pypdf
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

DPI = 96
PT_PER_INCH = 72
PX_TO_PT = PT_PER_INCH / DPI

SCREEN_WIDTH = 1728  # 18 inches * 96 DPI
SCREEN_HEIGHT = 1094  # 11.4 inches * 96 DPI

chrome_options = Options()
chrome_options.binary_location = "/usr/bin/brave-browser"

chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-popup-blocking")

chrome_options.add_argument("--headless=new")
chrome_options.add_argument(f"--window-size={SCREEN_WIDTH},{SCREEN_HEIGHT}")
chrome_options.add_argument("--enable-webgl")
chrome_options.add_argument("--use-gl=swiftshader")
chrome_options.add_argument("--ignore-gpu-blocklist")
chrome_options.add_argument("--enable-gpu-rasterization")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

chrome_options.add_experimental_option("useAutomationExtension", value=False)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(options=chrome_options)
# note that in landscape mode, dimensions are inverted
PDF_PARAMS = {
    "landscape": True,
    "paperWidth": SCREEN_HEIGHT / DPI,
    "paperHeight": SCREEN_WIDTH / DPI,
    "printBackground": True,
    "marginTop": 0,
    "marginBottom": 0,
    "marginLeft": 0,
    "marginRight": 0,
    "pageRanges": "1",
}


def save_screenshot_pdf(filename: str) -> None:
    """Capture full page as PDF (good for DOM/SVG content, not WebGL canvas)."""
    try:
        time.sleep(5)
        data = driver.execute_cdp_cmd("Page.printToPDF", PDF_PARAMS)
        with open(f"paper/figures/generated/{filename}", "wb") as file:
            file.write(base64.b64decode(data["data"]))
        print(f"Saved {filename}")
    except TimeoutException as error:
        print("something went wrong")
        print("".join(traceback.format_tb(error.__traceback__)))


def save_screenshot_png(filename: str) -> None:
    """Capture full page as PNG (captures WebGL canvas pixels)."""
    try:
        time.sleep(5)
        png = driver.get_screenshot_as_png()
        with open(f"paper/figures/generated/{filename}", "wb") as file:
            file.write(png)
        print(f"Saved {filename}")
    except Exception as error:
        print(f"something went wrong: {error}")


def screenshot_element_png(css_selector: str, filename: str) -> None:
    """Crop a PNG screenshot to the bounding rect of a DOM element."""
    try:
        time.sleep(4)
        png = driver.get_screenshot_as_png()
        element = driver.find_element(By.CSS_SELECTOR, css_selector)
        rect = driver.execute_script(
            "const r = arguments[0].getBoundingClientRect();"
            "const scrollX = window.scrollX || 0, scrollY = window.scrollY || 0;"
            "return {left: r.left + scrollX, top: r.top + scrollY, width: r.width, height: r.height};",
            element,
        )
        img = Image.open(io.BytesIO(png))
        dpr = driver.execute_script("return window.devicePixelRatio || 1;")
        x0 = int(rect["left"] * dpr)
        y0 = int(rect["top"] * dpr)
        x1 = int((rect["left"] + rect["width"]) * dpr)
        y1 = int((rect["top"] + rect["height"]) * dpr)
        cropped = img.crop((x0, y0, x1, y1))
        cropped.save(f"paper/figures/generated/{filename}")
        print(f"Saved {filename}")
    except Exception as error:
        print(f"something went wrong: {error}")


def screenshot_element_pdf(css_selector: str, filename: str) -> None:
    """Crop a PDF to the bounding rect of a DOM element (DOM/SVG content only)."""
    try:
        time.sleep(4)
        data = driver.execute_cdp_cmd("Page.printToPDF", PDF_PARAMS)
        pdf_bytes = base64.b64decode(data["data"])

        element = driver.find_element(By.CSS_SELECTOR, css_selector)
        rect = driver.execute_script(
            "const r = arguments[0].getBoundingClientRect();"
            "const scrollX = window.scrollX || 0, scrollY = window.scrollY || 0;"
            "return {left: r.left + scrollX, top: r.top + scrollY, width: r.width, height: r.height};",
            element,
        )

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        writer = pypdf.PdfWriter()
        page = reader.pages[0]

        page_height_pt = float(page.mediabox.height)
        x0 = (rect["left"] - 4.0) * PX_TO_PT
        y0 = (rect["top"] - 4.0) * PX_TO_PT
        x1 = (rect["left"] + rect["width"]) * PX_TO_PT
        y1 = (rect["top"] + rect["height"]) * PX_TO_PT

        page.mediabox.lower_left = (x0, page_height_pt - y1)
        page.mediabox.upper_right = (x1, page_height_pt - y0)
        page.cropbox = page.mediabox
        writer.add_page(page)

        with open(f"paper/figures/generated/{filename}", "wb") as file:
            writer.write(file)
        print(f"Saved {filename}")
    except TimeoutException as error:
        print("something went wrong")
        print("".join(traceback.format_tb(error.__traceback__)))


# Verify WebGL is available
driver.get("about:blank")
webgl_ok = driver.execute_script(
    "var c=document.createElement('canvas');"
    "var gl=c.getContext('webgl')||c.getContext('experimental-webgl');"
    "return !!gl;"
)
print(f"WebGL available: {webgl_ok}")

# ── Graph view (PDF — pure DOM/SVG) ──────────────────────────────────────────
driver.get("http://localhost:4321")
time.sleep(1)

driver.find_element(By.CSS_SELECTOR, "#show-graph").click()
time.sleep(2)

save_screenshot_pdf("graph-view.pdf")

# ── Perspective view (PNG — WebGL canvas) ────────────────────────────────────
driver.find_element(By.CSS_SELECTOR, "#show-perspective").click()
time.sleep(4)  # let positions load + Three.js render + auto-rotate settle

save_screenshot_pdf("perspective-overview.pdf")
screenshot_element_pdf("#three-d-view", "perspective-3d.pdf")
screenshot_element_pdf("#three-controls", "perspective-controls.pdf")

driver.close()
driver.quit()
