import requests
import pytesseract
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup

# Example HTML image tag
html_image_tag = '<img alt="" src="/logo/DEFZZZ/4621cacorn.png" style="border-style:solid; border-width:3px; height:1414px; width:1000px">'

# Parse HTML to extract image source
soup = BeautifulSoup(html_image_tag, 'html.parser')
image_src = soup.find('img')['src']

# Construct full image URL
base_url = 'https://www.topjobs.lk'
full_image_url = base_url + image_src

# Download the image
response = requests.get(full_image_url)

if response.status_code == 200:
    # Process the image using Tesseract
    image = Image.open(BytesIO(response.content))
    extracted_text = pytesseract.image_to_string(image)
    
    print("Extracted Text:")
    print(extracted_text.strip())
else:
    print("Failed to download the image:", full_image_url)
