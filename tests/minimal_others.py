
import requests
import logging

logging.basicConfig(level=logging.INFO)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

urls = {
    "Palo Alto": "https://security.paloaltonetworks.com/rss.xml",
    "Fortinet": "https://filestore.fortinet.com/fortiguard/rss/ir.xml"
}

for name, url in urls.items():
    print(f"\nFetching {name} from {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
    except Exception as e:
        print(f"Error fetching {name}: {e}")

print("Done")
