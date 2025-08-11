"""
fetch_vahan_selenium.py
Robust Selenium downloader for Vahan dashboard (reportview.xhtml).

Usage:
  python fetch_vahan_selenium.py     # runs visible browser by default (recommended)
  python fetch_vahan_selenium.py --headless   # run headless once tested

Outputs:
  data/raw/  -> downloaded XLS/XLSX files (if export works)
  data/raw/snapshots/ -> screenshots & page source on failures for debugging
"""

import os
import time
import argparse
import glob
from pathlib import Path
from datetime import datetime
import shutil
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# CONFIG
URL = "https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml"
DOWNLOAD_DIR = Path.cwd() / "data" / "raw"
SNAP_DIR = DOWNLOAD_DIR / "snapshots"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
SNAP_DIR.mkdir(parents=True, exist_ok=True)

# Candidate selectors / labels we will try (site changes often)
YAXIS_LABEL_CANDIDATES = [
    ("id", "yaxisVar_label"),            # older id
    ("xpath", "//label[contains(@id,'yaxis') or contains(@for,'yaxis')]"),
    ("xpath", "//span[contains(text(), 'Y Axis') or contains(., 'Y Axis')]"),
]
# Li items will be located by their visible text, examples:
YAXIS_OPTIONS = ["Maker", "Vehicle Category", "Vehicle Type", "Maker Name", "Category"]

REFRESH_CANDIDATES = [
    ("id", "j_idt61"),  # earlier example
    ("xpath", "//button[contains(., 'Refresh') or contains(@title,'Refresh')]"),
    ("xpath", "//a[contains(., 'Refresh') or contains(@title,'Refresh')]"),
    ("css", "button.ui-button"),  # generic fallback
]

DOWNLOAD_CANDIDATES = [
    ("id", "vchgroupTable:xls"),
    ("xpath", "//a[contains(@id,'xls') or contains(@href,'.xls') or contains(.,'Export') or contains(.,'Excel')]"),
    ("xpath", "//button[contains(.,'Excel') or contains(.,'Export')]"),
    ("css", "a[download], a[href*='.xls'], a[href*='.xlsx']"),
]

# Utility helpers
def save_debug_snapshot(driver, name_prefix="error"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    png = SNAP_DIR / f"{name_prefix}_{ts}.png"
    html = SNAP_DIR / f"{name_prefix}_{ts}.html"
    try:
        driver.save_screenshot(str(png))
        with open(html, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"[DEBUG] Saved screenshot and page source: {png}, {html}")
    except Exception as e:
        print("[DEBUG] Failed saving snapshot:", e)

def try_find_click(driver, wait, selector, by_type, timeout=10):
    """
    Try to find element using selector & click it. Returns True if clicked.
    by_type: 'id' | 'xpath' | 'css'
    """
    try:
        if by_type == "id":
            el = wait.until(EC.element_to_be_clickable((By.ID, selector)))
        elif by_type == "xpath":
            el = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
        elif by_type == "css":
            el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        else:
            return False
        # scroll into view & click via JS if normal click fails
        try:
            el.click()
        except (ElementClickInterceptedException, Exception):
            driver.execute_script("arguments[0].scrollIntoView(true);", el)
            time.sleep(0.3)
            try:
                el.click()
            except Exception:
                driver.execute_script("arguments[0].click();", el)
        return True
    except TimeoutException:
        return False

def find_list_item_and_click(driver, wait, option_text):
    """
    Find dropdown list item by visible text (option_text) and click it.
    """
    # Many dashboards render list items as <li data-label="Maker"> or <li role="option">Maker</li>
    # Try several XPath patterns
    patterns = [
        f"//li[@data-label='{option_text}']",
        f"//li[normalize-space()='{option_text}']",
        f"//a[normalize-space()='{option_text}']",
        f"//span[normalize-space()='{option_text}']",
        f"//div[contains(@class,'ui-select')]//li[contains(.,'{option_text}')]",
    ]
    for p in patterns:
        try:
            el = wait.until(EC.element_to_be_clickable((By.XPATH, p)))
            driver.execute_script("arguments[0].scrollIntoView(true);", el)
            time.sleep(0.2)
            el.click()
            return True
        except TimeoutException:
            continue
    return False

def wait_for_download_completion(dldir: Path, timeout=30):
    """
    Wait until a new .xls/.xlsx appears in the folder.
    """
    start = time.time()
    before = set(dldir.glob("*"))
    while time.time() - start < timeout:
        after = set(dldir.glob("*"))
        new = after - before
        # consider partial temporary files (Chrome uses .crdownload)
        for f in new:
            if f.suffix.lower() in [".xls", ".xlsx", ".csv"]:
                # ensure file size stabilized
                prev_size = -1
                stable_count = 0
                while stable_count < 3 and time.time() - start < timeout:
                    size = f.stat().st_size
                    if size == prev_size:
                        stable_count += 1
                    else:
                        stable_count = 0
                    prev_size = size
                    time.sleep(0.5)
                return f
        time.sleep(0.5)
    return None

def perform_download_cycle(driver, wait, option_label, verbose=True):
    """
    Open page, select Y-axis option, refresh, click export/download.
    Returns downloaded file path or None.
    """
    # go to page fresh each time (avoids stale elements)
    driver.get(URL)
    if verbose:
        print(f"[INFO] Page loaded for option: {option_label}")
    time.sleep(2)  # let page start loading

    # 1) open Y-axis dropdown
    opened = False
    for by_type, sel in YAXIS_LABEL_CANDIDATES:
        if try_find_click(driver, wait, sel, by_type, timeout=8):
            opened = True
            break
    if not opened:
        print("[WARN] Could not open Y-axis control with candidate selectors. Trying fallback by clicking js.")
        # fallback: try generic dropdown click via JS searching for elements with 'yaxis' in id/for attributes
        try:
            el = driver.find_element(By.XPATH, "//*[contains(@id,'yaxis') or contains(@for,'yaxis') or contains(.,'Y Axis')]")
            driver.execute_script("arguments[0].click();", el)
            opened = True
        except Exception:
            pass

    if not opened:
        print("[ERROR] Failed to open Y-axis dropdown. Saving snapshot and returning.")
        save_debug_snapshot(driver, "no_yaxis")
        return None

    time.sleep(0.5)

    # 2) choose the option
    chosen = find_list_item_and_click(driver, wait, option_label)
    if not chosen:
        print(f"[WARN] Could not find list item by exact label '{option_label}'. Trying fuzzy matches.")
        # try fuzzy - look for partial match among candidate option texts
        for candidate in YAXIS_OPTIONS:
            if option_label.lower() in candidate.lower():
                if find_list_item_and_click(driver, wait, candidate):
                    chosen = True
                    break
    if not chosen:
        print(f"[ERROR] Could not click option '{option_label}'. Saving snapshot.")
        save_debug_snapshot(driver, f"no_option_{option_label}")
        return None

    time.sleep(1)

    # 3) Click refresh (try multiple candidate selectors)
    refreshed = False
    for by_type, sel in REFRESH_CANDIDATES:
        if try_find_click(driver, wait, sel, by_type, timeout=10):
            refreshed = True
            break
    if not refreshed:
        print("[WARN] Refresh button not found by id/xpath. Trying to execute dashboard refresh JS (if available).")
        # common dashboards expose a method to refresh; we attempt generic approach
        try:
            driver.execute_script("if(window.PF && PF('dashboard') ) { /* no-op */ }")
        except Exception:
            pass

    # Allow time for charts/data to update
    time.sleep(3)

    # 4) Click download/export
    dl_candidate_clicked = False
    before_files = set(DOWNLOAD_DIR.glob("*"))
    for by_type, sel in DOWNLOAD_CANDIDATES:
        if try_find_click(driver, wait, sel, by_type, timeout=8):
            dl_candidate_clicked = True
            break

    if not dl_candidate_clicked:
        # as a last resort, try to search for links to xls/xlsx in page
        try:
            links = driver.find_elements(By.XPATH, "//a[contains(@href,'.xls') or contains(@href,'.xlsx') or contains(.,'Download') or contains(.,'Export')]")
            for l in links:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", l)
                    time.sleep(0.2)
                    l.click()
                    dl_candidate_clicked = True
                    break
                except Exception:
                    continue
        except Exception:
            pass

    if not dl_candidate_clicked:
        print("[ERROR] Could not trigger download/export. Saving snapshot.")
        save_debug_snapshot(driver, f"no_download_{option_label}")
        return None

    # 5) Wait for download to complete
    downloaded = wait_for_download_completion(DOWNLOAD_DIR, timeout=25)
    if downloaded:
        print(f"[OK] Downloaded: {downloaded.name}")
        return downloaded
    else:
        print("[WARN] No new download found after clicking export. Check browser download settings.")
        # save snapshot for debug
        save_debug_snapshot(driver, f"no_file_{option_label}")
        return None

def cleanup_old_downloads():
    # optional: remove old xls/xlsx files to make detection of new downloads easier
    for ext in ("*.xls", "*.xlsx", "*.csv"):
        for f in DOWNLOAD_DIR.glob(ext):
            try:
                f.unlink()
            except Exception:
                pass

def main(headless=False):
    # Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1600,1000")

    # download preferences
    prefs = {
        "download.default_directory": str(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # create driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        # list of options to fetch
        options_to_fetch = ["Maker", "Vehicle Category"]

        cleanup_old_downloads()

        downloaded_files = []
        for opt in options_to_fetch:
            print(f"\n=== Starting cycle for: {opt} ===")
            for attempt in range(1, 4):  # retry up to 3 times
                try:
                    result = perform_download_cycle(driver, wait, opt, verbose=True)
                    if result:
                        downloaded_files.append(result)
                        break
                    else:
                        print(f"[INFO] Attempt {attempt} for '{opt}' failed — retrying...")
                        time.sleep(2)
                except Exception as e:
                    print(f"[ERROR] Unexpected exception during attempt {attempt} for '{opt}': {e}")
                    save_debug_snapshot(driver, f"exception_{opt}")
                    time.sleep(2)
            else:
                print(f"[FAILED] All attempts failed for option: {opt}")

        print("\n--- Summary ---")
        if downloaded_files:
            for f in downloaded_files:
                print("Downloaded:", f.name)
        else:
            print("No files downloaded. Check snapshots in", SNAP_DIR)
    finally:
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="Run Chrome headless")
    args = parser.parse_args()
    main(headless=args.headless)
