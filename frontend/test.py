import requests
import json

def test_manual_prediction():
    url = "http://127.0.0.1:5000/predict"
    payload = {
        "mode": "manual",
        "Appliance": "Air Conditioning",
        "Temperature": 22,
        "TimeOfDay": "Afternoon",
        "UsageTime": 5,
        "Power": 1500,
        "HouseholdSize": 3,
        "Season": "Summer",
        "DayType": "Weekday"
    }
    
    print(f"Sending manual prediction request to {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print("Response:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_manual_prediction()
