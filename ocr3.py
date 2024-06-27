import random
import pytesseract
from PIL import Image
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import time

# List of proxy configurations with authentication
PROXY_CONFIGS = [
    'http://pM7vqB:GyxrBZ@45.93.214.101:8000',
    'http://uJ0h5E:c8xGJG@45.89.75.43:8000',
    'http://3oqaU8:Z3oGEq@79.143.19.130:8000',
    'http://jMzHjR:PB2NAe@81.161.63.54:8000',
    'http://DzgEve:51Q4pd@81.161.63.176:8000',
    'http://r3Vrv8:3nUgLu@84.21.160.187:8000',
    'http://qxyVj8:V5EL8o@45.130.70.43:8000',
    'http://6wa2tK:e4TjKq@185.59.235.82:8000',
    'http://P7f00A:s5p8ys@185.59.232.78:8000',
    'http://4adwq0:6DBTA2@45.141.179.179:8000',
    'http://6SfTz2:sFmpZg@92.240.200.192:8000',
    'http://LPkt7x:ZbpYar@92.240.200.201:8000',
    'http://EFzAV3:94vM3d@38.148.143.98:8000',
    'http://Rb3psg:0817mM@38.148.141.9:8000',
    'http://LEoK4Q:7T1QYC@185.242.247.183:8000',
    'http://vpojQt:HMwNwn@168.81.251.109:8000',
]

def get_random_proxy():
    return random.choice(PROXY_CONFIGS)

# Function to perform OCR on an image
def ocr_image(image_url):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            text = pytesseract.image_to_string(image)
            return text.strip()
        else:
            print("Failed to fetch image:", image_url)
            return ""
    except Exception as e:
        print("Error occurred during OCR:", e)
        return ""

def scrape_page(url, total_jobs):
    proxy = get_random_proxy()  # Get a random proxy with authentication

    try:
        response = requests.get(url, proxies={"http": proxy}, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_elements = soup.select("tr[id^='tr']")

            for job_element in job_elements:
                try:
                    position_element = job_element.select_one("h2 span")
                    employer_element = job_element.select_one("h1")
                    opening_date_element = job_element.select_one("td:nth-of-type(5)")  # Adjusted this line to select the correct opening date element
                    closing_date_element = job_element.select_one("td:nth-of-type(6)")  # Adjusted this line to select the correct closing date element

                    if position_element and employer_element and opening_date_element and closing_date_element:
                        position = position_element.get_text(strip=True)
                        employer = employer_element.get_text(strip=True)
                        opening_date = opening_date_element.get_text(strip=True)  # Adjusted this line to correctly extract opening date
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
        total_jobs = scrape_page(url, total_jobs)

    print("Total scraped jobs:", len(total_jobs))
    return total_jobs

scrape_all_pages()
