from config import DB_CONFIG
import requests
from bs4 import BeautifulSoup
import re
import psycopg2

# Define constants
URL = 'https://999.md/ro/list/real-estate/apartments-and-rooms'
TABLE_NAME = "apartamente"
DB_NAME = "postgres"

def create_database():
    # Connect to PostgreSQL without specifying a database
    initial_connection_params = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    db = psycopg2.connect(**initial_connection_params)

    try:
        # Use a cursor to execute commands
        with db.cursor() as cursor:
            # Check if the database exists
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
            exists = cursor.fetchone()

            # If the database doesn't exist, create it
            if not exists:
                cursor.execute(f"CREATE DATABASE {DB_NAME}")

    finally:
        # Close the initial connection after creating the database
        db.close()



# Function to get unique links
def get_unique_links(url):
    response = requests.get(url)
    html_content = response.text
    pattern = r"/ro/\d{8}"
    links = re.findall(pattern, html_content)
    return set(f"https://999.md{link}" for link in links)

# Function to scrape and insert data
# Function to scrape and insert data
def scrape_and_insert_data(url, table_name):
    db = psycopg2.connect(**DB_CONFIG)
    with db:
        cursor = db.cursor()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (url VARCHAR(255), name VARCHAR(255), price VARCHAR(255), currency VARCHAR(255), surface VARCHAR(255), Phone VARCHAR(255))")
        final_links = get_unique_links(url)

        for link in final_links:
            print(link)  # Keep the print statement to indicate scraping
            response = requests.get(link)
            soup = BeautifulSoup(response.content, 'html.parser')

            deleted = soup.find(class_='adPage__archive-alert')
            if deleted is None:
                name = soup.find(class_='adPage__header')
                price = soup.find(class_='adPage__content__price-feature__prices__price__value')
                currency = soup.find(class_='adPage__content__price-feature__prices__price__currency')
                phone = soup.find(class_='js-phone-number-format number-format')

                content = {
                    'url': link,
                    'name': name.get_text().strip(),
                    'price': price.get_text().replace(" ", '').strip() if price else '0',
                    'currency': currency.get_text().replace(" ", '').strip() if currency else '0',
                    'surface': next((text.replace("m²", "").strip() for text in soup.select('.adPage__content__features__value') if "m²" in text), '0'),
                    'phone': phone.get_text().strip() if phone else '0',
                }

                cursor.execute(f"SELECT url FROM {table_name} WHERE url = %s", (content['url'],))
                existing_record = cursor.fetchone()

                if existing_record:
                    query = f"UPDATE {table_name} SET name = %s, price = %s, currency = %s, surface = %s, phone = %s WHERE url = %s"
                else:
                    query = f"INSERT INTO {table_name} (url, name, price, currency, surface, phone) VALUES (%s, %s, %s, %s, %s, %s)"

                values = (content['url'], content['name'], content['price'], content['currency'], content['surface'], content['phone'])
                cursor.execute(query, values)


# Main function
def main():
    create_database()
    scrape_and_insert_data(URL, TABLE_NAME)

if __name__ == "__main__":
    main()
