import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energy.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS energy_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL,
            appliance TEXT,
            usage_time REAL,
            time_of_day TEXT,
            day_type TEXT,
            season TEXT,
            power REAL,
            cost_per_unit REAL,
            predicted_energy REAL,
            estimated_cost REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_prediction_to_db(data, prediction, cost_per_unit=0.15):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    estimated_cost = prediction * float(cost_per_unit)
    
    try:
        cursor.execute('''
            INSERT INTO energy_history (
                timestamp, temperature, appliance, usage_time, time_of_day, 
                day_type, season, power, cost_per_unit, predicted_energy, estimated_cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            float(data.get('Temperature', 25)),
            str(data.get('Appliance', 'Other')),
            float(data.get('UsageTime', 1.0)),
            str(data.get('TimeOfDay', 'Afternoon')),
            str(data.get('DayType', 'Weekday')),
            str(data.get('Season', 'Summer')),
            float(data.get('Power', 500)),
            float(cost_per_unit),
            float(prediction),
            float(estimated_cost)
        ))
        
        conn.commit()
        return {
            'timestamp': timestamp,
            'predicted_energy': prediction,
            'estimated_cost': estimated_cost
        }
    except Exception as e:
        print(f"DB Error in save_prediction_to_db: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def save_predictions_bulk_to_db(records):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    data_tuples = []
    for rec in records:
        data = rec['data']
        pred = rec['prediction']
        cost_per_unit = float(data.get('CostPerUnit', 0.15))
        est_cost = pred * cost_per_unit
        
        data_tuples.append((
            timestamp,
            float(data.get('Temperature', 25)),
            str(data.get('Appliance', 'Other')),
            float(data.get('UsageTime', 1.0)),
            str(data.get('TimeOfDay', 'Afternoon')),
            str(data.get('DayType', 'Weekday')),
            str(data.get('Season', 'Summer')),
            float(data.get('Power', 500)),
            cost_per_unit,
            float(pred),
            float(est_cost)
        ))
        
    try:
        cursor.executemany('''
            INSERT INTO energy_history (
                timestamp, temperature, appliance, usage_time, time_of_day, 
                day_type, season, power, cost_per_unit, predicted_energy, estimated_cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data_tuples)
        
        conn.commit()
    except Exception as e:
        print(f"DB Error in save_predictions_bulk_to_db: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_history_from_db():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM energy_history ORDER BY id DESC LIMIT 5000')
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            'id': r['id'],
            'timestamp': r['timestamp'],
            'temperature': r['temperature'],
            'appliance': r['appliance'],
            'usage_time': r['usage_time'],
            'time_of_day': r['time_of_day'],
            'day_type': r['day_type'],
            'season': r['season'],
            'power': r['power'],
            'cost_per_unit': r['cost_per_unit'],
            'predicted_energy': r['predicted_energy'],
            'estimated_cost': r['estimated_cost']
        })
    return result

def reset_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM energy_history')
    conn.commit()
    conn.close()

init_db()
