import requests
import json
import time
import argparse
from typing import Dict, Any

def submit_research_job(
    base_url: str,
    trade: str,
    city: str,
    state: str,
    min_bond: int,
    keywords: list
) -> str:
    """Submit a new research job and return the job ID"""
    url = f"{base_url}/research-jobs"
    
    payload = {
        "trade": trade,
        "city": city,
        "state": state,
        "min_bond": min_bond,
        "keywords": keywords
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        return result.get("job_id")
    else:
        print(f"Error submitting job: {response.status_code}")
        print(response.text)
        return None

def check_job_status(base_url: str, job_id: str) -> Dict[str, Any]:
    """Check the status of a research job"""
    url = f"{base_url}/research-jobs/{job_id}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error checking job status: {response.status_code}")
        print(response.text)
        return None

def wait_for_job_completion(base_url: str, job_id: str, max_wait_time: int = 300, check_interval: int = 5) -> Dict[str, Any]:
    """Wait for job to complete with timeout"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        result = check_job_status(base_url, job_id)
        
        if not result:
            print("Failed to get job status")
            return None
            
        status = result.get("status")
        print(f"Current status: {status}")
        
        if status == "SUCCEEDED":
            return result
        elif status == "FAILED":
            print(f"Job failed: {result.get('message', 'Unknown error')}")
            return None
            
        time.sleep(check_interval)
    
    print(f"Timeout after waiting {max_wait_time} seconds")
    return None

def print_results(results: Dict[str, Any]) -> None:
    """Print formatted results"""
    if not results or "results" not in results:
        print("No results available")
        return
        
    subcontractors = results["results"]
    
    print("\n==== SUBCONTRACTOR RESEARCH RESULTS ====\n")
    print(f"Total candidates found: {len(subcontractors)}")
    
    if not subcontractors:
        print("No matching subcontractors found")
        return
        
    print("\nTop 5 Matches:")
    for i, sub in enumerate(subcontractors[:5]):
        print(f"\n--- #{i+1}: {sub['name']} (Score: {sub['score']}) ---")
        print(f"Website: {sub['website']}")
        print(f"Location: {sub.get('city', 'Unknown')}, {sub.get('state', '')}")
        print(f"License: {'Active' if sub.get('lic_active') else 'Inactive or Unknown'} {sub.get('lic_number', '')}")
        
        bond = sub.get('bond_amount')
        if bond:
            print(f"Bond Amount: ${bond:,}")
        else:
            print("Bond Amount: Unknown")
            
        print(f"TX Projects (past 5 yrs): {sub.get('tx_projects_past_5yrs', 0)}")
        print(f"Evidence: {sub.get('evidence_text', 'None')}")
        
    # Save full results to file
    with open("research_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nFull results saved to research_results.json")

def main():
    parser = argparse.ArgumentParser(description="Subcontractor Research Client")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--trade", default="mechanical", help="Trade type")
    parser.add_argument("--city", default="Austin", help="City")
    parser.add_argument("--state", default="TX", help="State (2-letter code)")
    parser.add_argument("--min-bond", type=int, default=5000000, help="Minimum bonding capacity")
    parser.add_argument("--keywords", nargs="+", default=["hotel", "commercial"], help="Keywords")
    
    args = parser.parse_args()
    
    print(f"Submitting research job for {args.trade} contractors in {args.city}, {args.state}")
    print(f"Minimum bond: ${args.min_bond:,}")
    print(f"Keywords: {args.keywords}")
    
    job_id = submit_research_job(
        args.url,
        args.trade,
        args.city,
        args.state,
        args.min_bond,
        args.keywords
    )
    
    if job_id:
        print(f"Job submitted successfully with ID: {job_id}")
        
        print("Waiting for job completion...")
        results = wait_for_job_completion(args.url, job_id)
        
        if results:
            print_results(results)
    
if __name__ == "__main__":
    main()
