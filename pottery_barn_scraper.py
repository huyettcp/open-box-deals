
import json
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)

def dismiss_modals(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal_component"))
        )
        close_selectors = [".btnClose", ".stickyOverlayMinimizeButton"]
        for selector in close_selectors:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for button in buttons:
                if button.is_displayed():
                    logging.info(f"Closing modal using selector: {selector}")
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
    except Exception as e:
        logging.info("No modal appeared or error during dismissal: %s", e)

def scroll_page(driver):
    logging.info("Beginning incremental scroll...")
    last_count = 0
    attempts = 0

    while True:
        products = driver.find_elements(By.CLASS_NAME, "grid-item")
        current_count = len(products)
        logging.info(f"Scrolled to {current_count} products")

        try:
            show_more = driver.find_element(By.XPATH, "//div[contains(@class, 'show-me-more')]/button")
            if show_more.is_displayed():
                logging.info("Clicking 'Show Me More' button")
                driver.execute_script("arguments[0].click();", show_more)
                time.sleep(random.uniform(2.0, 3.0))
        except Exception as e:
            logging.debug("No 'Show Me More' button found: %s", e)

        if current_count > last_count:
            last_count = current_count
            attempts = 0
        else:
            attempts += 1

        if attempts > 6:
            logging.info("No new items loaded after multiple scrolls. Stopping.")
            break

        ActionChains(driver).scroll_by_amount(0, 1000).perform()
        time.sleep(random.uniform(1.2, 1.8))

def scrape_products(driver):
    data = []
    skipped = []
    blocks = driver.find_elements(By.CLASS_NAME, "grid-item")
    logging.info(f"Extracting {len(blocks)} products...")

    for i, block in enumerate(blocks):
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", block)
            time.sleep(0.1)

            try:
                title_el = block.find_element(By.CSS_SELECTOR, ".product-name a span")
            except:
                title_el = block.find_element(By.CLASS_NAME, "product-name")
            title = title_el.text.strip()

            url_el = block.find_element(By.CSS_SELECTOR, "a.product-image-link")
            full_url = url_el.get_attribute("href")

            try:
                image_el = block.find_element(By.CSS_SELECTOR, "img.product-image")
            except:
                image_el = block.find_element(By.CSS_SELECTOR, "img[data-test-id='alt-image']")
            image_url = image_el.get_attribute("src")

            price_block = block.find_element(By.CLASS_NAME, "product-pricing")
            amounts = price_block.find_elements(By.CSS_SELECTOR, "span.amount")

            sale_price = f"${amounts[0].text.strip()}" if len(amounts) > 0 else None
            orig_price = f"${amounts[-1].text.strip()}" if len(amounts) > 1 else None

            data.append({
                "Product Name": title,
                "Original Price": orig_price,
                "Sale Price": sale_price,
                "Image URL": image_url,
                "Product Display Page URL": full_url,
                "Store": "Pottery Barn"
            })
        except Exception as e:
            logging.warning(f"[Block {i}] Skipping product due to error: {e}")
            try:
                skipped.append({
                    "index": i,
                    "error": str(e),
                    "html": block.get_attribute("outerHTML")
                })
            except:
                pass

    return data, skipped

def main():
    options = Options()
    options.add_experimental_option("detach", True)
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.potterybarn.com/shop/sale/open-box-deals/")

    dismiss_modals(driver)
    scroll_page(driver)
    products, skipped = scrape_products(driver)

    with open("pottery_barn_open_box.json", "w") as f:
        json.dump(products, f, indent=2)
    logging.info(f"Saved {len(products)} items to pottery_barn_open_box.json")

    with open("pottery_barn_skipped_blocks.json", "w") as f:
        json.dump(skipped, f, indent=2)
    logging.info(f"Saved {len(skipped)} skipped blocks to pottery_barn_skipped_blocks.json")

    driver.quit()

if __name__ == "__main__":
    main()
