from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pytesseract
from PIL import Image
from io import BytesIO
import time

# Function to perform OCR on an image
def ocr_image(image_url):
    try:
        driver.get(image_url)
        image_element = driver.find_element(By.CSS_SELECTOR, 'img')
        image_src = image_element.get_attribute('src')
        image_response = requests.get(image_src)
        if image_response.status_code == 200:
            image = Image.open(BytesIO(image_response.content))
            text = pytesseract.image_to_string(image)
            return text.strip()
        else:
            print("Failed to fetch image:", image_url)
            return ""
    except Exception as e:
        print("Error occurred during OCR:", e)
        return ""

def scrape_page(driver, total_jobs):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.job-list-table")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        job_elements = soup.select("table.job-list-table tr")

        for job_element in job_elements:
            try:
                position_element = job_element.select_one("h2 span")
                employer_element = job_element.select_one("h1")
                opening_date_element = job_element.select_one("td:nth-of-type(5)")
                closing_date_element = job_element.select_one("td:nth-of-type(6)")

                if position_element and employer_element and opening_date_element and closing_date_element:
                    position = position_element.get_text(strip=True)
                    employer = employer_element.get_text(strip=True)
                    opening_date = opening_date_element.get_text(strip=True)
                    closing_date = closing_date_element.get_text(strip=True)

                    print(f"Position: {position} | Employer: {employer} | Opening Date: {opening_date} | Closing Date: {closing_date}")

                    total_jobs.append({
                        "Position": position,
                        "Employer": employer,
                        "Opening Date": opening_date,
                        "Closing Date": closing_date
                    })
                else:
                    print("One or more elements not found for job:", job_element)

            except Exception as e:
                print("An error occurred while extracting job details:", e)

    except Exception as e:
        print("Error occurred while scraping:", e)

    return total_jobs

def scrape_all_pages():
    base_url = "https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=AV&pageNo="
    num_pages = 5
    total_jobs = []

    for page in range(1, num_pages + 1):
        print(f"\n\n\n....................................................................................Scraping page {page}...............................................\n\n\n")  # Print page number just before scraping
        url = f"{base_url}{page}"
        driver.get(url)
        total_jobs = scrape_page(driver, total_jobs)

    print("Total scraped jobs:", len(total_jobs))
    return total_jobs

# Set up Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode, without opening a browser window
service = Service('/usr/local/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

# Initialize PyTesseract
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Call the scraping function
scrape_all_pages()

# Quit the WebDriver
driver.quit()
