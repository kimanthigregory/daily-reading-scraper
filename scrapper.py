import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# File path for storing readings
JSON_FILE = "readings.json"

# Email settings
EMAIL_SENDER = "gregteckie@gmail.com"  # Change to your email
EMAIL_PASSWORD = "yvrq kalu lmdd uade"  # Use an App Password if using Gmail
EMAIL_RECEIVER = "jcomputercollege@gmail.com"  # Change to where you want alerts sent

# Function to send an email alert
def send_email(subject, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        print("📧 Alert sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email alert: {e}")

# Set up Selenium WebDriver
options = Options()
options.add_argument("--headless")  # Run in the background
driver = webdriver.Chrome(options=options)

# URL of the daily readings page
url = "https://dailygospel.org/AM/gospel"
driver.get(url)
driver.implicitly_wait(5)

# Parse with BeautifulSoup
soup = BeautifulSoup(driver.page_source, "html.parser")

# Close Selenium after fetching the page
driver.quit()

# Extract readings
readings = {}
categories = ["First_Reading", "Psalm", "Second_Reading", "Gospel"]
reading_sections = soup.select("div.GospelReading")

# Assign readings to categories
category_index = 0
for section in reading_sections:
    if category_index >= len(categories):
        break

    title_tag = section.select_one("h2.GospelReading-title span")
    book_reference = title_tag.get_text(strip=True) if title_tag else "Unknown Reference"

    reading_text = [verse.get_text(strip=True) for verse in section.select("div.GospelReading-text span.verse__content")]
    reading_content = "\n".join(reading_text)

    readings[categories[category_index]] = {
        "title": book_reference,
        "reading": reading_content
    }
    category_index += 1

# Get today's date
today = datetime.today().strftime("%Y-%m-%d")

# Load existing data if available
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r", encoding="utf-8") as file:
        try:
            existing_data = json.load(file)
        except json.JSONDecodeError:
            existing_data = {}
else:
    existing_data = {}

# Handle scraper failure
if readings:
    existing_data[today] = readings
    message = f"✅ Readings for {today} saved successfully!"
else:
    if existing_data:
        latest_date = max(existing_data.keys())
        existing_data[today] = existing_data[latest_date]
        message = f"⚠️ Scraper failed! Using readings from {latest_date} instead."
        send_email("⚠️ Scraper Failure - Using Old Readings", f"The scraper failed today ({today}). Using readings from {latest_date} instead.")
    else:
        message = "❌ Scraper failed and no past readings are available!"
        send_email("❌ Scraper Failed - No Readings", f"The scraper failed today ({today}) and no past readings are available. Please check!")

# Save updated JSON
with open(JSON_FILE, "w", encoding="utf-8") as file:
    json.dump(existing_data, file, indent=4, ensure_ascii=False)

print(message)
