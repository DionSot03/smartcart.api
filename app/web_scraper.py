from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd

def scrape_bakalmarket_selenium(return_df=False, save_json=True):
    url = "https://www.bakalmarket.gr/product-category/pantopoleio/"
    driver = webdriver.Chrome()
    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.product"))
        )
    except Exception as e:
        print("Timeout waiting for products:", e)
        driver.quit()
        if save_json:
            import json
            with open("bakalmarket_products.json", "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        return pd.DataFrame()

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    products = soup.find_all("li", class_="product")
    print(f"Βρέθηκαν {len(products)} προϊόντα.")

    data = []
    for p in products:
        try:
            name_el = p.select_one("h2.woocommerce-loop-product__title")
            if not name_el:
                name_el = p.select_one("h3.product-name")
            if not name_el:
                name_el = p.find("h2")
            if not name_el:
                name_el = p.find("h3")
            price_el = p.select_one("span.woocommerce-Price-amount")
            img_el = p.select_one("img.attachment-woocommerce_thumbnail")
            link_el = p.select_one("a.woocommerce-LoopProduct-link")
            name = name_el.get_text(strip=True) if name_el else None
            price_text = price_el.get_text(strip=True) if price_el else None
            # Extract float from price string (e.g., "2,80€" -> 2.80)
            price = None
            if price_text:
                import re
                match = re.search(r"(\d+,\d+|\d+\.\d+|\d+)", price_text)
                if match:
                    price = float(match.group(1).replace(",", "."))
            image_url = img_el["src"] if img_el and img_el.has_attr("src") else None
            
            description = None

            print(f"Extracted: name={name}, price={price}, image_url={image_url}")

            if not name or price is None:
                continue

            data.append({
                "name": name,
                "description": description,
                "image_url": image_url,
                "price": price
            })
        except Exception as e:
            print("Σφάλμα σε προϊόν:", e)
            continue

    df = pd.DataFrame(data)
    # Save as JSON instead of HTML or CSV
    with open("bakalmarket_products.json", "w", encoding="utf-8") as f:
        import json
        json.dump(data, f, ensure_ascii=False, indent=2)

    if return_df:
        return df

    print(df.head())
