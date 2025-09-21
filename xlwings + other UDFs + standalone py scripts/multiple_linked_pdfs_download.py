# %% Imports and Setup
import requests
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urljoin
import re
from concurrent.futures import ThreadPoolExecutor
import threading
# Configuration
MAIN_URL = "https://www.omkarmyog.in/2022/10/pdf.html"
DOWNLOAD_DIR = "downloaded_pdfs"
WAIT_TIME = 20  # seconds to wait for JavaScript redirects

# %% Helper Functions - Link Extraction
def extract_links_from_main_page(url):
    """Extract all chapter links from the main page"""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links that contain 'adhyay' or similar patterns
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'adhyay' in href.lower() or 'chapter' in href.lower():
                full_url = urljoin(url, href)
                links.append(full_url)
        
        return links
    except Exception as e:
        print(f"Error extracting links: {e}")
        return []

# %% Helper Functions - URL Processing
def get_final_google_drive_url(intermediate_url, wait_time=20):
    """
    Get the final Google Drive URL by following redirects
    Note: This might not work due to JavaScript-based redirections
    """
    try:
        # Add headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        # First request to get the intermediate page
        response = session.get(intermediate_url, allow_redirects=True)
        
        # Look for Google Drive URLs in the page content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for JavaScript redirects or meta refresh
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for Google Drive URLs in JavaScript
                drive_urls = re.findall(r'https://drive\.google\.com/[^"\']*', script.string)
                if drive_urls:
                    return drive_urls[0]
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'drive.google.com' in href or 'docs.google.com' in href:
                return href
        
        # Check for meta refresh
        meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
        if meta_refresh:
            content = meta_refresh.get('content', '')
            url_match = re.search(r'url=(.+)', content)
            if url_match:
                return url_match.group(1)
        
        return None
        
    except Exception as e:
        print(f"Error getting final URL from {intermediate_url}: {e}")
        return None
# %% Helper Functions - PDF Download
def download_pdf(pdf_url, filename):
    """Download PDF from Google Drive URL"""
    try:
        # Convert Google Drive view URL to download URL
        if 'drive.google.com' in pdf_url:
            # Extract file ID more reliably
            file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', pdf_url)
            if file_id_match:
                file_id = file_id_match.group(1)
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            else:
                print(f"Could not extract file ID from: {pdf_url}")
                return False
        else:
            download_url = pdf_url
        
        print(f"Attempting download from: {download_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        session = requests.Session()
        response = session.get(download_url, headers=headers, stream=True, timeout=30)
        
        if response.status_code == 200:
            # Check if we got HTML instead of PDF (Google's download warning page)
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type:
                print(f"Got HTML page instead of PDF for {filename} - trying alternative method")
                # Try with confirm parameter for large files
                download_url_with_confirm = f"{download_url}&confirm=t"
                response = session.get(download_url_with_confirm, headers=headers, stream=True, timeout=30)
            
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Check if file is actually a PDF
            file_size = os.path.getsize(filepath)
            if file_size > 1000:  # At least 1KB
                print(f"Downloaded: {filename} ({file_size} bytes)")
                return True
            else:
                print(f"Downloaded file too small, might be an error page: {filename}")
                return False
            
        else:
            print(f"Failed to download {filename}: Status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"Timeout downloading {filename}")
        return False
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return False
# %% Test Link Extraction
# Run this cell to test link extraction without downloading
if __name__ == "__main__":
    print("Testing link extraction...")
    chapter_links = extract_links_from_main_page(MAIN_URL)
    
    if chapter_links:
        print(f"Found {len(chapter_links)} chapter links:")
        for i, link in enumerate(chapter_links, 1):
            print(f"{i}. {link}")
    else:
        print("No chapter links found!")
        
    # Store for use in other cells
    globals()['chapter_links'] = chapter_links

# %% Test Single URL Processing
# Run this cell to test URL processing for one link
def test_single_url(link_index=0):
    """Test processing a single URL"""
    if 'chapter_links' not in globals():
        print("Run the link extraction cell first!")
        return
    
    if link_index >= len(chapter_links):
        print(f"Invalid index. Available links: 0-{len(chapter_links)-1}")
        return
        
    test_link = chapter_links[link_index]
    print(f"Testing link {link_index + 1}: {test_link}")
    
    final_url = get_final_google_drive_url(test_link, WAIT_TIME)
    
    if final_url:
        print(f"Found final URL: {final_url}")
        return final_url
    else:
        print("Could not get final URL")
        return None

# Uncomment to test a specific link (change index as needed)
# test_url = test_single_url(0)

# %% Test Single Download
# Run this cell to test downloading one PDF
def test_single_download(google_drive_url, filename="test_chapter.pdf"):
    """Test downloading a single PDF"""
    if google_drive_url:
        success = download_pdf(google_drive_url, filename)
        if success:
            print(f"Test download successful: {filename}")
        else:
            print("Test download failed")
    else:
        print("No URL provided for testing")

# Uncomment to test download (provide a valid Google Drive URL)
# test_single_download("YOUR_GOOGLE_DRIVE_URL_HERE", "test_file.pdf")

# %% Debug Cell - Inspect Variables
def debug_info():
    """Print debug information about current variables"""
    print("=== DEBUG INFORMATION ===")
    
    if 'chapter_links' in globals():
        print(f"Chapter links found: {len(chapter_links)}")
        print(f"First few links: {chapter_links[:3] if chapter_links else 'None'}")
    else:
        print("Chapter links not extracted yet")
    
    print(f"Download directory: {DOWNLOAD_DIR}")
    print(f"Main URL: {MAIN_URL}")
    print(f"Wait time: {WAIT_TIME} seconds")
    
    # Check if download directory exists and list contents
    if os.path.exists(DOWNLOAD_DIR):
        files = os.listdir(DOWNLOAD_DIR)
        print(f"Files in download directory: {len(files)}")
        if files:
            print("Downloaded files:", files[:5])  # Show first 5 files
    else:
        print("Download directory doesn't exist yet")

# Uncomment to run debug info
# debug_info()

# %% Main Download Process
#def main():
    """Main function to download all PDFs"""
def main():
    """Main function to download all PDFs"""
    print("Starting PDF download process...")
    
    print("Extracting chapter links...")
    chapter_links = extract_links_from_main_page(MAIN_URL)
    
    if not chapter_links:
        print("No chapter links found!")
        return
    
    print(f"Found {len(chapter_links)} chapter links:")
    for i, link in enumerate(chapter_links, 1):
        print(f"{i}. {link}")
    
    print("\nAttempting to get final PDF URLs...")
    
    successful_downloads = 0
    failed_downloads = 0
    
    for i, link in enumerate(chapter_links, 1):
        print(f"\nProcessing link {i}/{len(chapter_links)}: {link}")
        
        final_url = get_final_google_drive_url(link)
        
        if final_url:
            print(f"Found final URL: {final_url}")
            filename = f"chapter_{i:02d}.pdf"
            
            if download_pdf(final_url, filename):
                successful_downloads += 1
            else:
                failed_downloads += 1
        else:
            print(f"Could not get final URL for chapter {i}")
            failed_downloads += 1
        
        # Add delay between requests to be respectful
        time.sleep(2)
    
    # Print summary
    print(f"\n=== DOWNLOAD SUMMARY ===")
    print(f"Total chapters: {len(chapter_links)}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Success rate: {(successful_downloads/len(chapter_links)*100):.1f}%")

# %% Parallel Download - Speedier Option
def download_single_chapter(args):
    """Download a single chapter - for use with threading"""
    i, link = args
    print(f"Processing link {i}/{len(chapter_links)}: {link}")
    
    final_url = get_final_google_drive_url(link)
    
    if final_url:
        print(f"Found final URL: {final_url}")
        filename = f"chapter_{i:02d}.pdf"
        
        if download_pdf(final_url, filename):
            return (i, True)
        else:
            return (i, False)
    else:
        print(f"Could not get final URL for chapter {i}")
        return (i, False)

def main():
    """Main function with concurrent downloads"""
    print("Starting PDF download process...")
    
    chapter_links = extract_links_from_main_page(MAIN_URL)
    
    if not chapter_links:
        print("No chapter links found!")
        return
    
    # Create list of (index, link) tuples
    download_tasks = [(i+1, link) for i, link in enumerate(chapter_links)]
    
    successful_downloads = 0
    failed_downloads = 0
    
    # Use ThreadPoolExecutor for concurrent downloads
    with ThreadPoolExecutor(max_workers=5) as executor:  # 5 concurrent downloads
        results = executor.map(download_single_chapter, download_tasks)
        
        for chapter_num, success in results:
            if success:
                successful_downloads += 1
            else:
                failed_downloads += 1
    
    # Print summary
    print(f"\n=== DOWNLOAD SUMMARY ===")
    print(f"Total chapters: {len(chapter_links)}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Success rate: {(successful_downloads/len(chapter_links)*100):.1f}%")

