import requests
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
        "name": "fitness_certificates",
        "url": "http://localhost:8000/fitness_certificates",
        "method": "GET",
        "headers": {
          "Accept": "application/json"
        }
      },
      {
        "name": "job_card_status",
        "url": "http://localhost:8000/joboards",
        "method": "GET",
        "headers": {
          "Accept": "application/json"
        }
      },
      {
        "name": "branding_priorities",
        "url": "http://localhost:8000/branding",
        "method": "GET",
        "headers": {
          "Accept": "application/json"
        }
      },
      {
        "name": "mileage",
        "url": "http://localhost:8000/mileage",
        "method": "GET",
        "headers": {
          "Accept": "application/json"
        }
      }
    ]
  },
  "output": {
    "destination_api": {
      "url": "http://localhost:8000/postmodeldata/",
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

def fetch_json_data(endpoint):
    """Fetches JSON data from a single API endpoint with retries."""
    url = endpoint["url"]
    headers = endpoint["headers"]
    method = endpoint["method"]
    attempts = PIPELINE_CONFIG["error_handling"]["retry_attempts"]
    delay = PIPELINE_CONFIG["error_handling"]["retry_delay_seconds"]

    for attempt in range(attempts):
        try:
            response = requests.request(method, url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            if PIPELINE_CONFIG["error_handling"]["log_errors"]:
                print(f"Error fetching data from {url} (attempt {attempt + 1}/{attempts}): {e}")
            if attempt < attempts - 1:
                time.sleep(delay)
            else:
                print(f"Failed to fetch data from {url} after {attempts} attempts.")
                return None
        except json.JSONDecodeError as e:
            if PIPELINE_CONFIG["error_handling"]["log_errors"]:
                print(f"Error parsing JSON data from {url}: {e}")
            return None

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
    branding_data = all_data.get('branding_priorities', [])
    
    # Calculate the mean of all dates
    all_dates = []
    for brand in branding_data:
        try:
            all_dates.append(datetime.strptime(brand['start_date'], '%Y-%m-%d').date())
            all_dates.append(datetime.strptime(brand['end_date'], '%Y-%m-%d').date())
        except (ValueError, KeyError) as e:
            print(f"Skipping branding record in date calculation due to error: {e} - Record: {brand}")
            continue
    
    if all_dates:
        avg_timestamp = sum(d.toordinal() for d in all_dates) / len(all_dates)
        today = datetime.fromordinal(int(avg_timestamp)).date()
    else:
        today = datetime.now().date()

    # 1. Process Fitness Certificates
    fitness_data = all_data.get('fitness_certificates', [])
    for cert in fitness_data:
        status = True
        try:
            # Check validity date
            validity_date = datetime.strptime(cert['expiry_date'], '%d-%m-%Y').date()
            if validity_date < today:
                status = False
            
            # Check boolean fields if validity is ok
            if status:
                if not (cert['braking'].lower() == 'true' and \
                        cert['signal'].lower() == 'true' and \
                        cert['structural_integrity'].lower() == 'true'):
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
            "train_id": job.get("train"),
            "status": job.get("status")
        })

    # 3. Process Branding Priorities
    branding_data = all_data.get('branding_priorities', [])
    
    # Find max revenue and impressions for normalization
    max_revenue = 0
    max_impressions = 0
    for brand in branding_data:
        try:
            max_revenue = max(max_revenue, float(brand.get('revenue', 0)))
            max_impressions = max(max_impressions, float(brand.get('impressions', 0)))
        except (ValueError, KeyError) as e:
            print(f"Skipping branding record in max value calculation due to error: {e} - Record: {brand}")
            continue

    for brand in branding_data:
        score = 0
        try:
            start_date = datetime.strptime(brand['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(brand['end_date'], '%Y-%m-%d').date()

            if start_date <= today <= end_date:
                revenue = float(brand.get('revenue', 0))
                impression = float(brand.get('impressions', 0))

                # Normalization
                norm_revenue = revenue / max_revenue if max_revenue > 0 else 0
                norm_impression = impression / max_impressions if max_impressions > 0 else 0
                
                # Weighted score (70% revenue, 30% impressions)
                combined_score = (0.7 * norm_revenue) + (0.3 * norm_impression)
                
                # Scale to 1-5
                final_score = 1 + (combined_score * 4)
                score = int(round(final_score))


        except (ValueError, KeyError) as e:
            print(f"Skipping branding record due to error: {e} - Record: {brand}")
        
        processed_output["branding_priorities"].append({
            "train_id": brand.get("train"),
            "score": score
        })

    # 4. Process Mileage
    mileage_data = all_data.get('mileage', [])
    for item in mileage_data:
        try:
            mileage_float = float(item.get('total_kilometers', 0))
            processed_output["mileage"].append({
                "train_id": item.get("train"),
                "total_kilometers": int(mileage_float)
            })
        except (ValueError, KeyError) as e:
            print(f"Skipping mileage record due to error: {e} - Record: {item}")
            continue
    print(processed_output)
    return processed_output

def send_to_ml_api(data):
    try:
        print(requests.post(PIPELINE_CONFIG["output"]["destination_api"]["url"], json=data))
        print("Data sent to ML model API.")
        return True
    except Exception as e:
        print(f"Error sending data to ML model API: {e}")
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
        json_data = fetch_json_data(endpoint)
        if json_data:
            all_fetched_data[endpoint['name']] = json_data

    if not all_fetched_data:
        print("No data fetched. Exiting pipeline.")
        return
    print(all_fetched_data)

    print("Processing data...")
    processed_data = process_data(all_fetched_data)

    if not processed_data:
        print("No data to send. Exiting pipeline.")
        return
    #print(processed_data)
    print("Sending data to ML model API...")
    success = send_to_ml_api(processed_data)

    if not success and PIPELINE_CONFIG["error_handling"]["fallback"] == "Store data locally if API call fails.":
        print("ML API call failed. Executing fallback.")
        fallback_storage(processed_data)

    print("Data pipeline finished.")

if __name__ == "__main__":
    run_pipeline()
