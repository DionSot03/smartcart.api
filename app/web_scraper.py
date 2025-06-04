from bs4 import BeautifulSoup

def scrape_from_html(html_file, target_name, store_name):
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
    except FileNotFoundError:
        return {"store": store_name, "error": "Το αρχείο HTML δεν βρέθηκε"}

    for div in soup.find_all("div", class_="product"):
        name = div.find("h2", class_="name").text.strip()
        if target_name.lower() in name.lower():
            try:
                price = float(div.find("span", class_="price").text.strip())
                description = div.find("p", class_="description").text.strip()
                image_url = div.find("img", class_="image")["src"]
            except Exception as e:
                return {"store": store_name, "error": f"Σφάλμα ανάγνωσης: {e}"}

            return {
                "store": store_name,
                "name": name,
                "price": price,
                "description": description,
                "image_url": image_url
            }

    return {"store": store_name, "error": "Το προϊόν δεν βρέθηκε"}


