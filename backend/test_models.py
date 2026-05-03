import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from training import EnergyPredictor

def test():
    print("Testing EnergyPredictor model...")
    predictor = EnergyPredictor()
    if not predictor.is_trained:
        print("Model not trained, training now...")
        predictor.train()
    
    # Test a prediction
    test_data = {
        'Appliance': 'Air Conditioning',
        'Temperature': 24,
        'TimeOfDay': 'Afternoon',
        'UsageTime': 3,
        'Power': 1500,
        'HouseholdSize': 4,
        'Season': 'Summer',
        'DayType': 'Weekday'
    }
    
    df = pd.DataFrame([test_data])
    pred = predictor.predict(df)
    print(f"Prediction for {test_data['Appliance']}: {pred:.2f} kWh")

if __name__ == "__main__":
    test()
