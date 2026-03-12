import requests
import json
import base64

# Start session
session = requests.Session()

# Find a cleaning task that is not completed
r = session.get("http://127.0.0.1:5000/limpieza")
# Actually, just send a request directly.
# First login
login_data = {"username": "admin", "password": "password"}
r = session.post("http://127.0.0.1:5000/login", data=login_data)

# Let's create a dummy image (1x1 red pixel)
red_pixel_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
import base64
with open("test.png", "wb") as f:
    f.write(base64.b64decode(red_pixel_b64))

# Find first uncompleted task
# I will just fetch from API or raw HTML
html = session.get("http://127.0.0.1:5000/limpieza").text
import re
match = re.search(r'action="/limpieza/completar/(\d+)"', html)
if match:
    lid = match.group(1)
    print(f"Found pending cleaning task lid={lid}. Completing with image...")
    
    with open("test.png", "rb") as f:
        files = {"evidencia": ("test.png", f, "image/png")}
        resp = session.post(f"http://127.0.0.1:5000/limpieza/completar/{lid}", files=files)
        
    print("Response status:", resp.status_code)
    print("Redirection:", resp.url)
else:
    print("No pending cleaning tasks found. Generate mock data first.")
