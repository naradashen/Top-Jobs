import httpx
from bs4 import BeautifulSoup
import random
import pytesseract
from PIL import Image

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
        with httpx.Client() as client:
            response = client.get(image_url)
            if response.status_code == 200:
                text = pytesseract.image_to_string(Image.open(BytesIO(response.content)))
                return text.strip()
            else:
                print("Failed to fetch image:", image_url)
                return ""
    except Exception as e:
        print("Error occurred during OCR:", e)
        return ""

def scrape_page(url, page_number, total_jobs):
    proxy = get_random_proxy()  # Get a random proxy with authentication
    
    try:
        with httpx.Client(proxies={"http://": proxy}, verify=False) as client:  # Disabling SSL verification
            response = client.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_listings = soup.find_all('tr', id=lambda x: x and x.startswith('tr'))
            
            page_jobs = []
            
            for job in job_listings:
                try:
                    # Assuming the job description is presented as an image
                    job_desc_element = job.find('td', width="28%")
                    if job_desc_element and job_desc_element.find('img'):
                        image_src = job_desc_element.find('img')['src']
                        image_url = f"{url}/{image_src}"  # Assuming the image source is relative
                        position = ocr_image(image_url)
                    else:
                        position = "N/A"
                    
                    employer_element = job.find('h1')
                    if employer_element:
                        employer = employer_element.text.strip()
                    else:
                        employer = "N/A"
                    
                    opening_date_elements = job.find_all('td', nowrap=True)
                    if opening_date_elements and len(opening_date_elements) >= 2:
                        opening_date = opening_date_elements[1].text.strip()
                        closing_date = opening_date_elements[2].text.strip()
                    else:
                        opening_date = "N/A"
                        closing_date = "N/A"
                    
                    # Output in piped format
                    print(" | ".join([f"Position: {position}", f"Employer: {employer}", f"Opening Date: {opening_date}", f"Closing Date: {closing_date}"]))
                    print("\n")
                    
                    page_jobs.append({
                        "Position": position,
                        "Employer": employer,
                        "Opening Date": opening_date,
                        "Closing Date": closing_date
                    })
                    
                except AttributeError as e:
                    print("An error occurred while extracting job details:", e)
            
            total_jobs.extend(page_jobs)
    except httpx.HTTPError:
        print("Error occurred while making request with proxy:", proxy)
        # Retry with another proxy
        scrape_page(url, page_number, total_jobs)

def scrape_all_pages():
    base_url = "https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=AV&pageNo="
    num_pages = 5
    total_jobs = []
    
    for page in range(1, num_pages + 1):
        print(f"\n\n\n....................................................................................Scraping page {page}...............................................\n\n\n")  # Print page number just before scraping
        url = f"{base_url}{page}"
        scrape_page(url, page, total_jobs)
    
    print("Total scraped jobs:", len(total_jobs))
    return total_jobs

scrape_all_pages()
