from botasaurus import *
@browser
def scrape_heading_task(driver: AntiDetectDriver, data):
    driver.get("https://www.omkar.cloud/")
    heading = driver.text("h1")
    return {
        "heading": heading
    }
    if __name__ == "__main__":
        scrape_heading_task()
