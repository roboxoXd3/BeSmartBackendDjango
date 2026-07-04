import requests
import time

BASE_URL = "https://api.xbesmart.com"

def test_endpoint(url):
    print(f"\n--- Testing {url} ---")
    start = time.time()
    try:
        response = requests.get(url)
        elapsed = time.time() - start
        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"Structure: JSON Array (Length: {len(data)})")
                print("First item preview:")
                print(str(data[0])[:200] + "..." if data else "[]")
            elif isinstance(data, dict):
                print("Structure: JSON Object (Paginated)")
                print(f"Keys: {list(data.keys())}")
                print(f"Results Count: {len(data.get('results', []))}")
                print("First item preview:")
                if data.get('results'):
                    print(str(data['results'][0])[:200] + "...")
            else:
                print(f"Unknown structure: {type(data)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Test unpaginated (Backwards Compatibility)
    test_endpoint(f"{BASE_URL}/api/products/")
    
    # Test paginated
    test_endpoint(f"{BASE_URL}/api/products/?paginate=true")
