import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import csv
import threading

class EnergyPredictor:
    def __init__(self, model_path='energy_model.joblib'):
        self.model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), model_path)
        self.model = None
        self.le_appliance = LabelEncoder()
        self.le_appliance.fit(['Air Conditioning', 'Fan', 'Light', 'Fridge', 'Heater', 
                     'Washing Machine', 'TV', 'Microwave', 'Oven', 'Dishwasher', 'Other'])
        
        self.time_map = {'Morning': 0, 'Afternoon': 1, 'Evening': 2, 'Night': 3}
        self.day_map = {'Weekday': 0, 'Weekend': 1}
        self.season_map = {'Summer': 0, 'Winter': 1, 'Rainy': 2}
        
        self.is_training = False
        self.is_trained = False
        self.last_accuracy = 0
        
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                self.last_accuracy = 0 
            except:
                pass

    def train_async(self, df=None):
        thread = threading.Thread(target=self.train, args=(df,))
        thread.start()

    def train(self, df=None):
        self.is_training = True
        try:
            if df is None:
                root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                real_dataset = os.path.join(root_dir, 'energy consumption_dataset.csv')
                book1_dataset = os.path.join(root_dir, 'Book1.csv')
                
                dataset_path = None
                if os.path.exists(real_dataset):
                    dataset_path = real_dataset
                elif os.path.exists(book1_dataset):
                    dataset_path = book1_dataset

                if dataset_path:
                    raw_df = pd.read_csv(dataset_path, encoding='latin1')
                    raw_df.columns = [c.strip().replace('"', '') for c in raw_df.columns]
                    
                    df = pd.DataFrame()
                    temp_col = next((c for c in raw_df.columns if 'Outdoor Temperature' in c), 'Temperature')
                    app_col = next((c for c in raw_df.columns if 'Appliance Type' in c), 'Appliance')
                    power_col = next((c for c in raw_df.columns if 'Power' in c), 'Power')
                    time_col = next((c for c in raw_df.columns if 'Duration' in c), 'UsageTime')
                    energy_col = next((c for c in raw_df.columns if 'Energy' in c), 'EnergyConsumption')

                    df['Temperature'] = pd.to_numeric(raw_df[temp_col], errors='coerce').fillna(25)
                    df['TimeOfDay'] = raw_df.get('TimeOfDay', pd.Series(['Afternoon']*len(raw_df))).map(self.time_map).fillna(1)
                    df['DayType'] = raw_df.get('DayType', pd.Series(['Weekday']*len(raw_df))).map(self.day_map).fillna(0)
                    df['Season'] = raw_df.get('Season', pd.Series(['Summer']*len(raw_df))).map(self.season_map).fillna(0)
                    df['Appliance'] = raw_df[app_col]
                    df['Power'] = pd.to_numeric(raw_df[power_col], errors='coerce').fillna(500)
                    df['UsageTime'] = pd.to_numeric(raw_df[time_col], errors='coerce').fillna(1)
                    df['EnergyConsumption'] = pd.to_numeric(raw_df[energy_col], errors='coerce').fillna(0.1)
                    
                    df['ApplianceEncoded'] = df['Appliance'].apply(lambda x: x if x in self.le_appliance.classes_ else 'Other')
                    df['ApplianceEncoded'] = self.le_appliance.transform(df['ApplianceEncoded'])
                    df = df.drop('Appliance', axis=1)
                else:
                    raise FileNotFoundError("No dataset found for training.")
                
            # Outlier Handling: Drop top 1% of extreme energy consumption values
            q_hi = df["EnergyConsumption"].quantile(0.99)
            df = df[df["EnergyConsumption"] < q_hi]
            
            X = df[['Temperature', 'ApplianceEncoded', 'UsageTime', 'TimeOfDay', 'DayType', 'Season', 'Power']]
            y = df['EnergyConsumption']
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Using HistGradientBoostingRegressor as specified
            self.model = HistGradientBoostingRegressor(max_iter=200, max_depth=15, random_state=42)
            self.model.fit(X_train, y_train)
            
            joblib.dump(self.model, self.model_path)
            self.is_trained = True
            
            score = self.model.score(X_test, y_test)
            self.last_accuracy = score
            self.is_training = False
            return score
        except Exception as e:
            self.is_training = False
            print("Training failed:", e)
            return 0

    def predict(self, data):
        if self.model is None:
            if not self.is_training:
                self.train_async()
            # STRICT REQUIREMENT: No fake/mock data fallbacks
            return 0
            
        # Handle if data is passed as a DataFrame or Series
        if isinstance(data, (pd.DataFrame, pd.Series)):
            if isinstance(data, pd.DataFrame):
                data = data.iloc[0].to_dict()
            else:
                data = data.to_dict()

        time_of_day = self.time_map.get(data.get('TimeOfDay', 'Afternoon'), 1)
        day_type = self.day_map.get(data.get('DayType', 'Weekday'), 0)
        season = self.season_map.get(data.get('Season', 'Summer'), 0)
        
        appliance = str(data.get('Appliance', 'Other'))
        if appliance not in self.le_appliance.classes_:
            appliance = 'Other'
        appliance_encoded = self.le_appliance.transform([appliance])[0]
        
        features = {
            'Temperature': float(data.get('Temperature', 25)),
            'ApplianceEncoded': appliance_encoded,
            'UsageTime': float(data.get('UsageTime', 1)),
            'TimeOfDay': time_of_day,
            'DayType': day_type,
            'Season': season,
            'Power': float(data.get('Power', 500))
        }
        
        df = pd.DataFrame([features])
        prediction = self.model.predict(df)[0]
        return max(0.01, prediction) 

if __name__ == "__main__":
    print("Initializing EnergyPredictor...")
    predictor = EnergyPredictor()
    print("Starting Model Training...")
    accuracy = predictor.train()
    print("-" * 30)
    print(f"TRAINING COMPLETE")
    print(f"Model Accuracy: {accuracy * 100:.2f}%")
    print("-" * 30)
