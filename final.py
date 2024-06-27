import httpx
from bs4 import BeautifulSoup

def scrape_page(url, page_number, total_jobs):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        job_listings = soup.find_all('tr', id=lambda x: x and x.startswith('tr'))
        
        page_jobs = []
        
        for job in job_listings:
            try:
                job_ref_element = job.find('td', width="5%", align="center")
                if job_ref_element:
                    job_ref = job_ref_element.text.strip()
                else:
                    job_ref = "N/A"
                
                position_element = job.find('span', id='hdnJC1')
                if position_element:
                    position = position_element.text.strip()
                else:
                    position = "N/A"
                
                if position == "N/A":  # If position is not found in designated element, try to extract from job description
                    job_desc_element = job.find('td', width="28%")
                    if job_desc_element:
                        job_desc_parts = [part.strip() for part in job_desc_element.stripped_strings if part != "DEFZZZ" and not part.startswith("000")]
                        for part in job_desc_parts:
                            if part.lower() != "company name withheld":
                                position = part
                                break
                
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
                print("|".join([f"Job Reference Number: {job_ref}", f"Position: {position}", f"Employer: {employer}", f"Opening Date: {opening_date}", f"Closing Date: {closing_date}"]))
                print("\n")
                
                page_jobs.append({
                    "Job Reference Number": job_ref,
                    "Position": position,
                    "Employer": employer,
                    "Opening Date": opening_date,
                    "Closing Date": closing_date
                })
                
            except AttributeError as e:
                print("An error occurred while extracting job details:", e)
        
        total_jobs.extend(page_jobs)

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
