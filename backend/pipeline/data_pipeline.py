
import requests
import csv
import json
import time
import os
from datetime import datetime
import math

# Configuration from the user's JSON input
PIPELINE_CONFIG = {
  "input": {
    "endpoints": [
      {
        "name": "data_source_1",
        "url": "https://localhost:8000/fitnesss_certificates",
        "method": "GET",
        "headers": {
          "Accept": "text/csv"
        }
      },
      {
        "name": "data_source_2",
        "url": "https://localhost:8000/joboards",
        "method": "GET",
        "headers": {
          "Accept": "text/csv"
        }
      },
      {
        "name": "data_source_3",
        "url": "https://localhost:8000/branding",
        "method": "GET",
        "headers": {
          "Accept": "text/csv"
        }
      },
      {
        "name": "data_source_4",
        "url": "https://localhost:8000/mileage",
        "method": "GET",
        "headers": {
          "Accept": "text/csv"
        }
      }
    ]
  },
  "output": {
    "destination_api": {
      "url": "https://localhost:8000/postmodeldata",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      }
    }
  },
  "error_handling": {
    "retry_attempts": 3,
    "retry_delay_seconds": 5,
    "log_errors": True,
    "fallback": "Store data locally if API call fails."
  }
}

def fetch_csv_data(endpoint):
    """Fetches CSV data from a single API endpoint with retries."""
    url = endpoint["url"]
    headers = endpoint["headers"]
    method = endpoint["method"]
    attempts = PIPELINE_CONFIG["error_handling"]["retry_attempts"]
    delay = PIPELINE_CONFIG["error_handling"]["retry_delay_seconds"]

    for attempt in range(attempts):
        try:
            response = requests.request(method, url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.text
        except requests.exceptions.RequestException as e:
            if PIPELINE_CONFIG["error_handling"]["log_errors"]:
                print(f"Error fetching data from {url} (attempt {attempt + 1}/{attempts}): {e}")
            if attempt < attempts - 1:
                time.sleep(delay)
            else:
                print(f"Failed to fetch data from {url} after {attempts} attempts.")
                return None

def parse_csv(csv_data):
    """Parses CSV data from a string into a list of dictionaries."""
    if not csv_data:
        return []
    try:
        reader = csv.DictReader(csv_data.strip().splitlines())
        return [row for row in reader]
    except csv.Error as e:
        if PIPELINE_CONFIG["error_handling"]["log_errors"]:
            print(f"Error parsing CSV data: {e}")
        return []

def process_data(all_data):
    """
    Processes the collected data based on specific rules for each data type.
    """
    processed_output = {
        "fitness_certificates": [],
        "job_card_status": [],
        "branding_priorities": [],
        "mileage": []
    }
    today = datetime.now().date()

    # NOTE: This assumes the fetched data keys match these names.
    # The names come from the user's description of the data.
    # e.g., all_data['fitness_certificates'] contains the fitness data.

    # 1. Process Fitness Certificates
    fitness_data = all_data.get('fitness_certificates', [])
    for cert in fitness_data:
        status = True
        try:
            # Check validity date
            validity_date = datetime.strptime(cert['validity'], '%Y-%m-%d').date()
            if validity_date < today:
                status = False
            
            # Check boolean fields if validity is ok
            if status:
                if not (cert['braking'].lower() == 'true' and \
                        cert['signaling'].lower() == 'true' and \
                        cert['structural'].lower() == 'true'):
                    status = False
        except (ValueError, KeyError) as e:
            print(f"Skipping fitness record due to error: {e} - Record: {cert}")
            continue

        processed_output["fitness_certificates"].append({
            "train_id": cert.get("train_id"),
            "status": status
        })

    # 2. Process Job Card Status
    job_card_data = all_data.get('job_card_status', [])
    for job in job_card_data:
        processed_output["job_card_status"].append({
            "train_id": job.get("train_id"),
            "status": job.get("status")
        })

    # 3. Process Branding Priorities
    branding_data = all_data.get('branding_priorities', [])
    for brand in branding_data:
        try:
            start_date = datetime.strptime(brand['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(brand['end_date'], '%Y-%m-%d').date()

            if start_date <= today <= end_date:
                revenue = float(brand.get('perday_revenue', 0))
                impression = float(brand.get('impression', 0))

                # Scoring logic:
                # A simple weighted score. Assumes max revenue of 10000 and max impression of 100000 for normalization.
                # Revenue is weighted 70%, Impression 30%.
                # The final score is scaled to be between 1 and 5.
                norm_revenue = min(revenue / 10000, 1.0)
                norm_impression = min(impression / 100000, 1.0)
                
                combined_score = (0.7 * norm_revenue) + (0.3 * norm_impression)
                final_score = math.ceil(combined_score * 5)
                if final_score == 0 and (revenue > 0 or impression > 0):
                    final_score = 1

                processed_output["branding_priorities"].append({
                    "train_id": brand.get("trainid"),
                    "score": int(final_score)
                })
        except (ValueError, KeyError) as e:
            print(f"Skipping branding record due to error: {e} - Record: {brand}")
            continue

    # 4. Process Mileage
    mileage_data = all_data.get('mileage', [])
    for item in mileage_data:
        try:
            mileage_float = float(item.get('mileage', 0))
            processed_output["mileage"].append({
                "train_id": item.get("train_id"),
                "mileage": int(mileage_float)
            })
        except (ValueError, KeyError) as e:
            print(f"Skipping mileage record due to error: {e} - Record: {item}")
            continue
            
    return processed_output

def send_to_ml_api(data):
    """Sends processed data to the ML model API."""
    api_config = PIPELINE_CONFIG["output"]["destination_api"]
    url = api_config["url"]
    headers = api_config["headers"]
    method = api_config["method"]
    attempts = PIPELINE_CONFIG["error_handling"]["retry_attempts"]
    delay = PIPELINE_CONFIG["error_handling"]["retry_delay_seconds"]

    payload = {"data": data}

    for attempt in range(attempts):
        try:
            response = requests.request(method, url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            print("Successfully sent data to ML model API.")
            return True
        except requests.exceptions.RequestException as e:
            if PIPELINE_CONFIG["error_handling"]["log_errors"]:
                print(f"Error sending data to ML API (attempt {attempt + 1}/{attempts}): {e}")
            if attempt < attempts - 1:
                time.sleep(delay)
            else:
                print(f"Failed to send data to ML API after {attempts} attempts.")
                return False

def fallback_storage(data):
    """Stores data locally as a fallback."""
    if not os.path.exists('fallback_data'):
        os.makedirs('fallback_data')
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"fallback_data/data_{timestamp}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data stored locally at {filename}")
    except IOError as e:
        if PIPELINE_CONFIG["error_handling"]["log_errors"]:
            print(f"Error saving data locally: {e}")

def run_pipeline():
    """Main function to run the entire data pipeline."""
    print("Starting data pipeline...")
    
    all_fetched_data = {}
    endpoints = PIPELINE_CONFIG["input"]["endpoints"]
    
    for endpoint in endpoints:
        print(f"Fetching data from: {endpoint['name']}")
        csv_data = fetch_csv_data(endpoint)
        if csv_data:
            parsed_data = parse_csv(csv_data)
            all_fetched_data[endpoint['name']] = parsed_data

    if not all_fetched_data:
        print("No data fetched. Exiting pipeline.")
        return

    print("Processing data...")
    processed_data = process_data(all_fetched_data)

    if not processed_data:
        print("No data to send. Exiting pipeline.")
        return

    print("Sending data to ML model API...")
    success = send_to_ml_api(processed_data)

    if not success and PIPELINE_CONFIG["error_handling"]["fallback"] == "Store data locally if API call fails.":
        print("ML API call failed. Executing fallback.")
        fallback_storage(processed_data)

    print("Data pipeline finished.")

if __name__ == "__main__":
    run_pipeline()
