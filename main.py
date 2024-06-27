import httpx
from bs4 import BeautifulSoup
import asyncio

async def scrape_topjobs():
    url = "https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=AV"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        job_listings = soup.find_all('tr', id=lambda x: x and x.startswith('tr'))
        
        for job in job_listings:
            try:
                job_ref = job.find('td', width="5%", align="center").text.strip()
                position = job.find('span', id='hdnJC1').text.strip()
                employer = job.find('h1').text.strip()
                job_desc = job.find('td', width="28%").text.strip()
                opening_date = job.find_all('td', nowrap=True)[0].text.strip()
                closing_date = job.find_all('td', nowrap=True)[1].text.strip()
                
                # Extracting hidden span parameters
                job_code = job.find('span', id='hdnAC1').text.strip()
                employer_code = job.find('span', id='hdnEC1').text.strip()
                
                print("Job Reference Number:", job_ref)
                print("Position:", position)
                print("Employer:", employer)
                print("Job Description:", job_desc)
                print("Opening Date:", opening_date)
                print("Closing Date:", closing_date)
                print("Job Code:", job_code)
                print("Employer Code:", employer_code)
                print("-------------------------")
            except AttributeError as e:
                print("An error occurred while extracting job details:", e)
                print("HTML Content of the job variable:", job.prettify())  # Print HTML content for debugging

asyncio.run(scrape_topjobs())
