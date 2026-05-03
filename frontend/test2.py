import requests
import os

def test_csv_upload():
    url = "http://127.0.0.1:5000/upload_csv"
    csv_file = os.path.join(os.path.dirname(__file__), "Book1.csv")
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Creating it first...")
        with open(csv_file, "w") as f:
            f.write("Appliance,Temperature,TimeOfDay,UsageTime,Power,HouseholdSize,Season,DayType\n")
            f.write("Air Conditioning,22,Afternoon,5,1500,3,Summer,Weekday\n")
            f.write("Washing Machine,25,Morning,1,500,3,Summer,Weekend\n")

    print(f"Uploading {csv_file} to {url}...")
    try:
        with open(csv_file, "rb") as f:
            files = {"file": f}
            response = requests.post(url, files=files)
            print(f"Status: {response.status_code}")
            print("Response:", response.json())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_csv_upload()
