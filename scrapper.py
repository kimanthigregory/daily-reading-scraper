from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

JSON_FILE = "readings.json"

EMAIL_SENDER = "gregteckie@gmail.com"
EMAIL_PASSWORD = "yvrq kalu lmdd uade"
EMAIL_RECEIVER = "jcomputercollege@gmail.com"

def send_email(subject, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        print("📧 Email alert sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email alert: {e}")

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

url = "https://dailygospel.org/AM/gospel"
driver.get(url)
driver.implicitly_wait(5)

soup = BeautifulSoup(driver.page_source, "html.parser")

# Extract liturgical week
week_element = soup.select_one("div.ng-star-inserted")
liturgical_week = week_element.get_text(strip=True) if week_element else "Unknown Week"

# Extract readings
readings = {}
reading_sections = soup.select("div.GospelReading")
num_sections = len(reading_sections)

# Map reading positions to categories
if num_sections == 4:
    category_order = ["First_Reading", "Psalm", "Second_Reading", "Gospel"]
elif num_sections == 3:
    category_order = ["First_Reading", "Psalm", "Gospel"]
else:
    category_order = [f"Reading_{i+1}" for i in range(num_sections)]

for idx, section in enumerate(reading_sections):
    title_tag = section.select_one("h2.GospelReading-title span")
    book_reference = title_tag.get_text(strip=True) if title_tag else "Unknown Reference"

    reading_text = [verse.get_text(strip=True) for verse in section.select("div.GospelReading-text span.verse__content")]
    reading_content = "\n".join(reading_text)

    category = category_order[idx] if idx < len(category_order) else f"Reading_{idx+1}"

    readings[category] = {
        "title": book_reference,
        "reading": reading_content
    }

# Get Saint of the Day
saint_data = {}
saint_link_element = soup.select_one("a.MoreGospelSaint-link")

if saint_link_element:
    saint_page_url = "https://dailygospel.org" + saint_link_element["href"]
    driver.get(saint_page_url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Saint-link"))
        )
        saint_soup = BeautifulSoup(driver.page_source, "html.parser")
        saint_element = saint_soup.select_one("a.Saint-link.saint-link")
        if saint_element:
            saint_name = saint_element.select_one("span.Saint-title").get_text(strip=True)
            saint_subtitle = saint_element.select_one("span.Saint-subtitle").get_text(strip=True)
            saint_profile_link = "https://dailygospel.org" + saint_element["href"]

            saint_data = {
                "name": saint_name,
                "title": saint_subtitle,
                "profile_link": saint_profile_link
            }
    except Exception as e:
        print(f"⚠️ Failed to load Saint of the Day: {e}")

driver.quit()

today = datetime.today().strftime("%Y-%m-%d")

# Load previous data
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r", encoding="utf-8") as file:
        try:
            existing_data = json.load(file)
        except json.JSONDecodeError:
            existing_data = {}
else:
    existing_data = {}

# Save new data or fallback
if readings or saint_data:
    existing_data[today] = {
        "liturgical_week": liturgical_week,
        "readings": readings,
        "saint_of_the_day": saint_data
    }
    message = f"✅ Readings and Saint of the Day for {today} saved successfully!"
else:
    if existing_data:
        latest_date = max(existing_data.keys())
        existing_data[today] = existing_data[latest_date]
        message = f"⚠️ Scraper failed! Using readings from {latest_date} instead."
        send_email("⚠️ Scraper Failure - Using Old Readings", f"The scraper failed today ({today}). Using readings from {latest_date} instead.")
    else:
        message = "❌ Scraper failed and no past data is available!"
        send_email("❌ Scraper Failed - No Readings", f"The scraper failed today ({today}) and no past readings are available. Please check!")

with open(JSON_FILE, "w", encoding="utf-8") as file:
    json.dump(existing_data, file, indent=4, ensure_ascii=False)

print(message)
