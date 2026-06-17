import requests

try:
    resp = requests.get("http://localhost:8000/admin", timeout=3)
    print(f"Server is running! Status: {resp.status_code}")
except Exception as e:
    print(f"Server is not running or failed to connect: {e}")
