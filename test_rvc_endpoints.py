import requests

endpoints = ['/tts', '/api/tts', '/synthesize', '/api/synthesize', '/voice', '/api/voice']

print("Testing RVC endpoints...")
for endpoint in endpoints:
    try:
        response = requests.get(f"http://127.0.0.1:18888{endpoint}", timeout=2)
        print(f"Testing {endpoint}: {response.status_code}")
    except Exception as e:
        print(f"Testing {endpoint}: Error - {e}") 