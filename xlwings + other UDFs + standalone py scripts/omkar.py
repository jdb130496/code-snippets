from botasaurus import *

@request
def scrape_heading_task(request: AntiDetectRequests, data):
    # Navigate to the Omkar Cloud website
    soup = request.bs4("https://www.omkar.cloud/")
    
    # Retrieve the heading element's text
    heading = soup.find('h1').get_text()

    # Save the data as a JSON file in output/scrape_heading_task.json
    return {
        "heading": heading
    }
     
if __name__ == "__main__":
    # Initiate the web scraping task
    scrape_heading_task()
