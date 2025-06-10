import json
import httpx
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytesseract
from PIL import Image
from io import BytesIO

# Path to the Tesseract executable (update this according to your installation)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Set up Selenium options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
chrome_options.add_argument("--no-sandbox")  # Avoid issues in some environments
chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent crashes in Docker/WSL
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("disable-infobars")
chrome_options.add_argument("--disable-extensions")

# Set User-Agent header
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}

# JSON file for real-time updates
JSON_FILE = "scraped_data.json"


def save_to_json(job_data):
    """Appends job data to the JSON file in real time."""
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(job_data)

    with open(JSON_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    print(f"Job saved: {job_data['Position']}")


def extract_image_text(image_url):
    """Extracts text from an image using OCR."""
    try:
        image_response = httpx.get(image_url)
        image = Image.open(BytesIO(image_response.content))
        extracted_text = pytesseract.image_to_string(image).replace("\n", " ")
        return extracted_text.strip() if extracted_text else "N/A"
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return "N/A"


def scrape_page(url, page_number):
    """Scrapes a single page for job listings."""
    with httpx.Client() as client:
        response = client.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Failed to load page {page_number}: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    job_listings = soup.find_all("tr", id=lambda x: x and x.startswith("tr"))

    if not job_listings:
        print(f"No job listings found on page {page_number}.")
        return

    # Initialize Selenium WebDriver (Headless Mode)
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)

    for job in job_listings:
        try:
            job_ref_element = job.find("td", width="5%", align="center")
            job_ref = job_ref_element.text.strip() if job_ref_element else "N/A"

            position_element = job.find("span", id="hdnJC1")
            position = position_element.text.strip() if position_element else "N/A"

            if position == "N/A":
                job_desc_element = job.find("td", width="28%")
                job_desc_parts = [
                    part.strip()
                    for part in job_desc_element.stripped_strings
                    if part != "DEFZZZ" and not part.startswith("000")
                ]
                for part in job_desc_parts:
                    if part.lower() != "company name withheld":
                        position = part
                        break

            employer_element = job.find("h1")
            employer = employer_element.text.strip() if employer_element else "N/A"

            opening_date_elements = job.find_all("td", nowrap=True)
            if len(opening_date_elements) >= 2:
                opening_date = opening_date_elements[1].text.strip()
                closing_date = opening_date_elements[2].text.strip()
            else:
                opening_date = "N/A"
                closing_date = "N/A"

            # Click Job Element in Selenium
            job_element = driver.find_element(By.ID, job["id"])
            job_element.click()

            # Wait for the new tab to open
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

            # Switch to new tab
            driver.switch_to.window(driver.window_handles[1])

            # Extract SEO tags
            seo_title = driver.title
            meta_tags = driver.find_elements(By.CSS_SELECTOR, "meta")
            meta_data = {
                tag.get_attribute("name"): tag.get_attribute("content")
                for tag in meta_tags
                if tag.get_attribute("name")
            }

            # Extract text from an image if present
            try:
                image_element = driver.find_element(By.CSS_SELECTOR, "#remark img")
                image_src = image_element.get_attribute("src")
                extracted_text = extract_image_text(image_src)
            except Exception:
                extracted_text = "N/A"

            # Close job tab and switch back
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            # Prepare job data
            job_data = {
                "Job Reference Number": job_ref,
                "Position": position,
                "Employer": employer,
                "Opening Date": opening_date,
                "Closing Date": closing_date,
                "SEO Title": seo_title,
                "Meta Tags": meta_data,
                "Extracted Text": extracted_text,
            }

            # Save job data in real time
            save_to_json(job_data)

        except Exception as e:
            print(f"Error extracting job details: {e}")

    # Close the browser
    driver.quit()


def scrape_all_pages():
    """Scrapes multiple pages and updates the JSON file in real time."""
    base_url = "https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=AV&pageNo="
    num_pages = 5  # Adjust as needed

    for page in range(1, num_pages + 1):
        print(f"\nScraping page {page}...\n")
        scrape_page(f"{base_url}{page}", page)

    print("\nScraping completed. Data saved in real-time to 'scraped_data.json'.")


# Start the scraping process
scrape_all_pages()
