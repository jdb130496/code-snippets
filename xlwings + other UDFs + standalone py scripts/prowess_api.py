import requests
import time
import zipfile
import os
import json
import csv
import pandas as pd

class ProwessAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.sendbatch_url = 'https://prowess.cmie.com/api/sendbatch'
        self.getbatch_url = 'https://prowess.cmie.com/api/getbatch'
    
    def send_batch(self, batch_file_path, output_format='json'):
        """
        Send a batch file for processing
        
        Args:
            batch_file_path (str): Path to the batch file downloaded from Prowess
            output_format (str): 'json' or 'txt' (default: 'json')
        
        Returns:
            dict: Response containing token and status
        """
        try:
            # Exact format as per documentation
            mydata = {
                'apikey': self.api_key,
                'format': output_format
            }
            
            # Debug: Print what we're sending (hide API key)
            debug_data = mydata.copy()
            debug_data['apikey'] = f"{self.api_key[:8]}..." if len(self.api_key) > 8 else "***"
            print(f"Sending data: {debug_data}")
            print(f"Batch file: {batch_file_path}")
            print(f"File exists: {os.path.exists(batch_file_path)}")
            
            # Exact format as per documentation
            with open(batch_file_path, 'rb') as batch_file:
                myfile = {'batchfile': batch_file}
                response = requests.post(self.sendbatch_url, data=mydata, files=myfile)
            
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text: {response.text}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {'error': f'Invalid JSON response: {response.text}'}
            else:
                return {'error': f'HTTP {response.status_code}: {response.text}'}
                
        except FileNotFoundError:
            return {'error': f'Batch file not found: {batch_file_path}'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_batch_status(self, token):
        """
        Check the status of a batch processing job
        
        Args:
            token (str): Token received from send_batch
        
        Returns:
            dict or bytes: Status JSON or ZIP file content if ready
        """
        try:
            mydata = {
                'apikey': self.api_key,
                'token': token
            }
            
            response = requests.post(self.getbatch_url, data=mydata)
            
            if response.status_code == 200:
                # Check if response is JSON (status) or ZIP file (data ready)
                content_type = response.headers.get("Content-Type", "").lower()
                if "application/json" in content_type:
                    return response.json()
                else:
                    # Return ZIP file content
                    return response.content
            else:
                return {'error': f'HTTP {response.status_code}: {response.text}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def download_data_dump(self, batch_file_path, output_dir='./downloads', 
                          output_format='json', polling_interval=30, max_wait_time=3600,
                          convert_to_csv=True, create_excel=True):
        """
        Complete workflow to download data dump
        
        Args:
            batch_file_path (str): Path to the batch file
            output_dir (str): Directory to save downloaded files
            output_format (str): 'json' or 'txt'
            polling_interval (int): Seconds between status checks
            max_wait_time (int): Maximum time to wait in seconds
            convert_to_csv (bool): Convert files to CSV format
            create_excel (bool): Create Excel workbook from CSV files
        
        Returns:
            str: Path to downloaded ZIP file or error message
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Sending batch file: {batch_file_path}")
        
        # Step 1: Send batch for processing
        send_response = self.send_batch(batch_file_path, output_format)
        
        if 'error' in send_response:
            return f"Error sending batch: {send_response['error']}"
        
        if send_response.get('status') != '200':
            return f"Batch submission failed: {send_response.get('errdesc', 'Unknown error')}"
        
        token = send_response['token']
        print(f"Batch submitted successfully. Token: {token}")
        
        # Step 2: Poll for completion
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            print(f"Checking status for token: {token}")
            
            batch_result = self.get_batch_status(token)
            
            if isinstance(batch_result, dict):
                # Still processing - check status
                if 'error' in batch_result:
                    return f"Error checking status: {batch_result['error']}"
                
                message = batch_result.get('message', 'Unknown')
                print(f"Status: {message}")
                
                if message in ['IN_QUEUE', 'PROCESSING', 'ZIP WAITING TO BE QUEUED', 
                              'ZIP INQUEUE', 'ZIP PROCESSING']:
                    print(f"Waiting {polling_interval} seconds before next check...")
                    time.sleep(polling_interval)
                    continue
                else:
                    return f"Unexpected status: {message}"
            
            elif isinstance(batch_result, bytes):
                # ZIP file is ready - save it
                zip_filename = f"{token}.zip"
                zip_path = os.path.join(output_dir, zip_filename)
                
                with open(zip_path, 'wb') as zip_file:
                    zip_file.write(batch_result)
                
                print(f"Data dump downloaded successfully: {zip_path}")
                
                # Extract and list contents
                extract_path = os.path.join(output_dir, 'extracted')
                self._extract_and_list_contents(zip_path, output_dir)
                
                # Convert to CSV if requested
                if convert_to_csv:
                    self.convert_to_csv(extract_path, output_format)
                    
                    # Create Excel workbook if requested
                    if create_excel:
                        csv_dir = os.path.join(output_dir, 'csv_files')
                        self.create_excel_workbook(csv_dir)
                
                return zip_path
        
        return f"Timeout: Data not ready after {max_wait_time} seconds"
    
    def _extract_and_list_contents(self, zip_path, extract_dir):
        """Extract ZIP file and list contents"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extract_path = os.path.join(extract_dir, 'extracted')
                zip_ref.extractall(extract_path)
                
                print(f"\nExtracted files to: {extract_path}")
                print("Contents:")
                for file in zip_ref.namelist():
                    print(f"  - {file}")
                    
        except Exception as e:
            print(f"Error extracting ZIP: {e}")
    
    def convert_to_csv(self, extracted_dir, output_format='json'):
        """
        Convert extracted files to CSV format
        
        Args:
            extracted_dir (str): Directory containing extracted files
            output_format (str): Original format ('json' or 'txt')
        """
        csv_dir = os.path.join(os.path.dirname(extracted_dir), 'csv_files')
        os.makedirs(csv_dir, exist_ok=True)
        
        print(f"\nConverting files to CSV format...")
        
        if output_format == 'json':
            self._convert_json_to_csv(extracted_dir, csv_dir)
        else:
            self._convert_pipe_to_csv(extracted_dir, csv_dir)
    
    def _convert_json_to_csv(self, extracted_dir, csv_dir):
        """Convert JSON files to CSV"""
        json_files = [f for f in os.listdir(extracted_dir) if f.endswith('.json')]
        
        for json_file in json_files:
            try:
                json_path = os.path.join(extracted_dir, json_file)
                csv_file = json_file.replace('.json', '.csv')
                csv_path = os.path.join(csv_dir, csv_file)
                
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract headers and data from JSON structure
                headers = data.get('head', [])
                rows = data.get('data', [])
                
                # Write to CSV
                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
                    writer.writerows(rows)
                
                print(f"  Converted {json_file} -> {csv_file}")
                print(f"    Rows: {len(rows)}, Columns: {len(headers)}")
                
            except Exception as e:
                print(f"  Error converting {json_file}: {e}")
    
    def _convert_pipe_to_csv(self, extracted_dir, csv_dir):
        """Convert pipe-delimited files to CSV"""
        txt_files = [f for f in os.listdir(extracted_dir) 
                    if f.endswith('.txt') and not f.endswith('.lst')]
        
        for txt_file in txt_files:
            try:
                txt_path = os.path.join(extracted_dir, txt_file)
                csv_file = txt_file.replace('.txt', '.csv')
                csv_path = os.path.join(csv_dir, csv_file)
                
                # Read pipe-delimited file and convert to CSV
                with open(txt_path, 'r', encoding='utf-8') as infile:
                    reader = csv.reader(infile, delimiter='|')
                    
                    with open(csv_path, 'w', newline='', encoding='utf-8') as outfile:
                        writer = csv.writer(outfile)
                        row_count = 0
                        for row in reader:
                            writer.writerow(row)
                            row_count += 1
                
                print(f"  Converted {txt_file} -> {csv_file}")
                print(f"    Rows: {row_count}")
                
            except Exception as e:
                print(f"  Error converting {txt_file}: {e}")
    
    def create_excel_workbook(self, csv_dir):
        """
        Create a single Excel workbook with multiple sheets from CSV files
        
        Args:
            csv_dir (str): Directory containing CSV files
        """
        try:
            csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
            
            if not csv_files:
                print("No CSV files found to create Excel workbook")
                return
            
            excel_path = os.path.join(os.path.dirname(csv_dir), 'prowess_data.xlsx')
            
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                for csv_file in csv_files:
                    csv_path = os.path.join(csv_dir, csv_file)
                    sheet_name = csv_file.replace('.csv', '')
                    
                    # Read CSV and write to Excel sheet
                    df = pd.read_csv(csv_path)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    print(f"  Added sheet '{sheet_name}' with {len(df)} rows")
            
            print(f"\nExcel workbook created: {excel_path}")
            return excel_path
            
        except Exception as e:
            print(f"Error creating Excel workbook: {e}")
            return None


# Example usage
def main():
    # Replace with your actual API key
    API_KEY = "0be95582cf2a260c6be0b3ea5ebb7c32"
    
    # Replace with the path to your batch file downloaded from Prowess
    BATCH_FILE_PATH = r"D:\Downloads\52_week.bt"
    
    # Initialize API client (exactly as per documentation)
    api = ProwessAPI(API_KEY)
    
    print("=== Testing Simple Send Batch (as per documentation) ===")
    
    # Test the exact format from documentation first
    send_response = api.send_batch(BATCH_FILE_PATH, 'json')
    print(f"Send batch response: {send_response}")
    
    if 'error' not in send_response and send_response.get('status') == '200':
        print("✓ Batch submitted successfully!")
        token = send_response['token']
        print(f"Token: {token}")
        
        # Now proceed with full download
        result = api.download_data_dump(
            batch_file_path=BATCH_FILE_PATH,
            output_dir=r'D:\Downloads\prowess_output',
            output_format='json',
            polling_interval=30,
            max_wait_time=1800,
            convert_to_csv=True,
            create_excel=True
        )
        print(f"\nFinal result: {result}")
    else:
        print("❌ Batch submission failed!")
        print("Possible issues:")
        print("1. Invalid API key")
        print("2. API access not enabled for your subscription")
        print("3. Batch file format issue")
        print("4. Network/firewall restrictions")
        print("5. IP address not whitelisted (if applicable)")


def test_simple_request():
    """Simple test exactly matching documentation"""
    import requests
    
    API_KEY = ""  # Replace with your actual API key
    BATCH_FILE_PATH = r"D:\Downloads\52_week.bt"
    
    url = 'https://prowess.cmie.com/api/sendbatch'
    mydata = {'apikey': API_KEY, 'format': 'json'}
    
    try:
        with open(BATCH_FILE_PATH, 'rb') as f:
            myfile = {'batchfile': f}
            response = requests.post(url, data=mydata, files=myfile)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")


# Uncomment to run simple test first
# test_simple_request()


if __name__ == "__main__":
    main()
