from bs4 import BeautifulSoup
import pandas as pd

# StaticShop1
with open("StaticShop1.html", "r", encoding="utf-8") as f1:
    soup1 = BeautifulSoup(f1, "html.parser")

products1 = []

for div in soup1.find_all("div", class_="product"):
    name = div.find("h2", class_="name").text.strip()
    price = float(div.find("span", class_="price").text.strip())
    description = div.find("p", class_="description").text.strip()
    image_url = div.find("img", class_="image")["src"]
    products1.append([name, price, description, image_url])

df1 = pd.DataFrame(products1, columns=["name", "price", "description", "image_url"])
df1["store"] = "StaticShop1"


# StaticShop2
with open("StaticShop2.html", "r", encoding="utf-8") as f2:
    soup2 = BeautifulSoup(f2, "html.parser")

products2 = []

for div in soup2.find_all("div", class_="product"):
    name = div.find("h2", class_="name").text.strip()
    price = float(div.find("span", class_="price").text.strip())
    description = div.find("p", class_="description").text.strip()
    image_url = div.find("img", class_="image")["src"]
    products2.append([name, price, description, image_url])

df2 = pd.DataFrame(products2, columns=["name", "price", "description", "image_url"])
df2["store"] = "StaticShop2"


# Συγχώνευση αποτελεσμάτων
all_products = pd.concat([df1, df2], ignore_index=True)

# Αποθήκευση σε αρχείο CSV (προαιρετικό)
all_products.to_csv("scraped_static_shops.csv", index=False, encoding="utf-8")

#  Προβολή πρώτων γραμμών
print(all_products.head())



