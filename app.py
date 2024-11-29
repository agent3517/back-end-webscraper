from flask import Flask, request, jsonify, send_file, render_template
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import os


# Initialize Flask app
app = Flask(__name__, template_folder='templates')

# Global variable for storing results
scraped_results = []

def initialize_driver():
    options = Options()
    options.add_argument('--headless')  # Run headlessly in the background
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # Changing user agent to mimic real browsing
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.90 Safari/537.36")
    
    # Set capabilities within options
    caps = options.to_capabilities()
    caps["goog:loggingPrefs"] = {"performance": "ALL"}
    caps["pageLoadStrategy"] = "normal"
    
    # Create service object for the ChromeDriver
    service = ChromeService()

    driver = webdriver.Chrome(service=service, options=options)
    return driver


# Function to scrape Google search results
def google_scrape(keyword):
    global scraped_results
    scraped_results = []  # Clear previous results
    
    driver = initialize_driver()
    url = f'https://www.google.com/search?q={keyword}&num=10'
    driver.get(url)

    # Wait and accept the cookies consent if any
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[text()="Přijmout vše"]'))
        )
        accept_button.click()
    except Exception as e:
        print("Cookies dialog was not found or could not be clicked:", e)

    # Wait for search results to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tF2Cxc'))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        for g in soup.find_all('div', class_='tF2Cxc'):
            title = g.find('h3').text if g.find('h3') else 'No title'
            link = g.find('a')['href'] if g.find('a') else 'No link'
            snippet = g.find('span', class_='aCOpRe').text if g.find('span', class_='aCOpRe') else 'No snippet'
            scraped_results.append({'title': title, 'link': link, 'snippet': snippet})

    except Exception as e:
        print(f"An error occurred while scraping: {e}")
    
    driver.quit()

# Route for performing the search
@app.route('/search', methods=['POST'])
def search_route():
    global scraped_results
    # Get the keyword from the request body
    data = request.get_json()
    keyword = data.get('keyword', '')

    # Perform the search
    google_scrape(keyword)

    # Return the search results as JSON
    return jsonify({"results": scraped_results})

# Route for exporting results to CSV
@app.route('/export', methods=['GET'])
def export():
@app.route('/export', methods=['GET'])
def export():
    global scraped_results

    # Create a CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Link', 'Snippet'])  # Write headers

    for result in scraped_results:
        writer.writerow([result['title'], result['link'], result['snippet']])

    # Move the cursor to the beginning of the file
    output.seek(0)

    # Return the file as an attachment
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='results.csv'
    )
    
@app.route('/')
def index():
    print("Serving index.html")  # Debug log
    return render_template('index.html')  # Your front-end HTML file

if __name__ == '__main__':
    app.run(debug=True)
