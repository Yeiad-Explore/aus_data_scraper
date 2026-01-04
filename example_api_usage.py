"""Example script demonstrating how to use the Scraper API."""

import requests
import time
import json

# API base URL
API_URL = "http://localhost:8000"


def submit_scrape_job():
    """Submit a scraping job to the API."""

    # Request body
    payload = {
        "url": "https://immi.homeaffairs.gov.au/entering-and-leaving-australia/entering-australia/overview",
        "name": "entering_australia",
        "depth": 1,
        "max_pages": 10,
        "filter": "same_path",
        "save_individual_pages": True,
        "final_synthesis": True
    }

    print("Submitting scraping job...")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")

    # Submit the job
    response = requests.post(f"{API_URL}/scrape", json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Job submitted successfully!")
        print(f"  Job ID: {result['job_id']}")
        print(f"  Job Name: {result['job_name']}")
        print(f"  Status: {result['status']}")
        print(f"  URL: {result['url']}\n")
        return result['job_id']
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"  {response.text}")
        return None


def check_job_status(job_id):
    """Check the status of a scraping job."""

    print(f"Checking status for job {job_id}...\n")

    response = requests.get(f"{API_URL}/jobs/{job_id}")

    if response.status_code == 200:
        job = response.json()
        print(f"Job Status: {job['status']}")
        print(f"Created At: {job['created_at']}")

        if job['status'] == 'completed':
            print(f"\n✓ Job completed successfully!")
            if job.get('result'):
                print(f"  Pages scraped: {job['result'].get('pages_scraped', 0)}")
                print(f"  Duration: {job['result'].get('duration_seconds', 0):.2f}s")
                print(f"  Output: {job['result'].get('output_path', 'N/A')}")
                if job['result'].get('failed_urls'):
                    print(f"  Failed URLs: {len(job['result']['failed_urls'])}")

        elif job['status'] == 'failed':
            print(f"\n✗ Job failed!")
            print(f"  Error: {job.get('error', 'Unknown error')}")

        elif job['status'] == 'running':
            print(f"\n⏳ Job is still running...")

        return job
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"  {response.text}")
        return None


def list_all_jobs():
    """List all scraping jobs."""

    print("Fetching all jobs...\n")

    response = requests.get(f"{API_URL}/jobs")

    if response.status_code == 200:
        data = response.json()
        print(f"Total jobs: {data['total']}\n")

        for job in data['jobs']:
            print(f"Job ID: {job['job_id']}")
            print(f"  Name: {job['job_name']}")
            print(f"  URL: {job['url']}")
            print(f"  Status: {job['status']}")
            print(f"  Created: {job['created_at']}")
            print()
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"  {response.text}")


def main():
    """Main example workflow."""

    print("=" * 60)
    print("Generic Web Scraper API - Example Usage")
    print("=" * 60)
    print()

    # Check API health
    try:
        health = requests.get(f"{API_URL}/health")
        if health.status_code == 200:
            print("✓ API is healthy\n")
        else:
            print("✗ API health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Make sure the server is running:")
        print("  python -m src.main api\n")
        return

    # Submit a scraping job
    job_id = submit_scrape_job()

    if not job_id:
        return

    # Poll for job completion
    print("Polling for job completion (press Ctrl+C to stop)...")
    print()

    try:
        while True:
            job = check_job_status(job_id)

            if job and job['status'] in ['completed', 'failed']:
                break

            time.sleep(5)  # Wait 5 seconds before checking again
            print("\n" + "-" * 60 + "\n")

    except KeyboardInterrupt:
        print("\n\nStopped polling. Job is still running in the background.")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
