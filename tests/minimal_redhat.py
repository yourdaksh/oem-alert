
import requests
import logging

logging.basicConfig(level=logging.INFO)

url = "https://access.redhat.com/rss/content/security-advisories"
print(f"Fetching {url}...")
try:
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.content)}")
except Exception as e:
    print(f"Error: {e}")
print("Done")
