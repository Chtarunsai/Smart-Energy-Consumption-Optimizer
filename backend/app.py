from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import io
import os
import sys
import csv
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from training import EnergyPredictor
from db_handler import save_prediction_to_db, save_predictions_bulk_to_db, get_history_from_db, reset_db
from utils import generate_suggestions

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

predictor = EnergyPredictor()

# Background train on startup
if not predictor.is_trained:
    predictor.train_async()

@app.route('/')
def serve_frontend():
    return app.send_static_file('index.html')

@app.route('/predict', methods=['POST'])
def predict_energy():
    data = request.json
    try:
        prediction = predictor.predict(data)
        cost_per_unit = float(data.get('CostPerUnit', 0.15))
        
        # Save to DB
        db_record = save_prediction_to_db(data, prediction, cost_per_unit)
        
        # Suggestions
        suggestions = generate_suggestions(data, prediction, cost_per_unit)
        
        return jsonify({
            'prediction': prediction, 
            'estimated_cost': db_record['estimated_cost'],
            'suggestions': suggestions
        })
    except Exception as e:
        print(f"ERROR in /predict: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/predict_batch', methods=['POST'])
def predict_energy_batch():
    batch_data = request.json # Expecting a list of input dicts
    if not isinstance(batch_data, list):
        return jsonify({'error': 'Input must be a list of appliances'}), 400
        
    results = []
    try:
        predictions_batch = []
        for data in batch_data:
            prediction = predictor.predict(data)
            cost_per_unit = float(data.get('CostPerUnit', 0.15))
            
            # Prepare for DB and Response
            predictions_batch.append({'data': data, 'prediction': prediction})
            
            results.append({
                'appliance': data.get('Appliance', 'Other'),
                'prediction': prediction,
                'estimated_cost': prediction * cost_per_unit,
                'suggestions': generate_suggestions(data, prediction, cost_per_unit)
            })
            
        # Save to DB in bulk
        save_predictions_bulk_to_db(predictions_batch)
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        print(f"ERROR in /predict_batch: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    try:
        # Read the file using latin1 encoding which is much more robust for CSVs with special chars
        content = file.stream.read().decode("latin1")
        stream = io.StringIO(content)
        df = pd.read_csv(stream)
        
        # Clean column names
        df.columns = [c.strip().replace('"', '') for c in df.columns]
        
        df = df.head(10000) # Limit processing to 10,000 for web request stability
        
        # Flexible Column Mapping
        cols = {c.strip().replace('"', ''): c for c in df.columns}
        temp_key = next((c for c in cols if 'Temperature' in c), 'Temperature')
        app_key = next((c for c in cols if 'Appliance' in c), 'Appliance')
        power_key = next((c for c in cols if 'Power' in c), 'Power')
        time_key = next((c for c in cols if 'Duration' in c or 'UsageTime' in c), 'UsageTime')
        cost_key = next((c for c in cols if 'Cost' in c), 'CostPerUnit')

        predictions_batch = []
        for _, row in df.iterrows():
            try:
                data = {
                    'Temperature': float(pd.to_numeric(row.get(temp_key), errors='coerce') if pd.notnull(pd.to_numeric(row.get(temp_key), errors='coerce')) else 0),
                    'Appliance': str(row.get(app_key, 'Other')),
                    'UsageTime': float(pd.to_numeric(row.get(time_key), errors='coerce') if pd.notnull(pd.to_numeric(row.get(time_key), errors='coerce')) else 0),
                    'TimeOfDay': str(row.get('TimeOfDay', 'Afternoon')),
                    'DayType': str(row.get('DayType', 'Weekday')),
                    'Season': str(row.get('Season', 'Summer')),
                    'Power': float(pd.to_numeric(row.get(power_key), errors='coerce') if pd.notnull(pd.to_numeric(row.get(power_key), errors='coerce')) else 0),
                    'CostPerUnit': float(pd.to_numeric(row.get(cost_key), errors='coerce') if pd.notnull(pd.to_numeric(row.get(cost_key), errors='coerce')) else 0),
                    'Timestamp': str(row.get('Timestamp', ''))
                }
                pred = predictor.predict(data)
                predictions_batch.append({'data': data, 'prediction': pred})
            except: continue
            
        if not predictions_batch:
            return jsonify({'error': 'No valid data rows found in CSV.'}), 400

        save_predictions_bulk_to_db(predictions_batch)
        
        # Sample results for the frontend chart to prevent browser freeze (100k rows fix)
        display_limit = 1000
        step = max(1, len(predictions_batch) // display_limit)
        sampled_results = []
        for i in range(0, len(predictions_batch), step):
            item = predictions_batch[i]
            sampled_results.append({
                'appliance': item['data'].get('Appliance', 'Other'),
                'prediction': item['prediction'],
                'estimated_cost': item['prediction'] * item['data'].get('CostPerUnit', 0.15),
                'timestamp': item['data'].get('Timestamp', '')
            })

        return jsonify({
            'status': 'success',
            'message': f'{len(predictions_batch)} records processed.',
            'results': sampled_results[:display_limit]
        })
    except Exception as e:
        print(f"ERROR in /upload: {str(e)}")
        return jsonify({'error': f"Failed to process CSV: {str(e)}"}), 500

@app.route('/reports', methods=['GET'])
def get_reports():
    try:
        data = get_history_from_db()
        return jsonify(data)
    except Exception as e:
        print(f"ERROR in /reports: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    status = "Training" if predictor.is_training else ("Ready" if predictor.is_trained else "Not Trained")
    return jsonify({
        'status': status,
        'accuracy': f"{predictor.last_accuracy * 100:.2f}%" if predictor.is_trained else "0%"
    })

@app.route('/train', methods=['POST'])
def train_model():
    predictor.train_async()
    return jsonify({'status': 'success', 'message': 'Training started in background.'})

@app.route('/accuracy', methods=['GET'])
def get_accuracy():
    return jsonify({'accuracy': f"{predictor.last_accuracy * 100:.2f}%"})

@app.route('/reset', methods=['POST'])
def reset_data():
    reset_db()
    return jsonify({'status': 'success', 'message': 'Database reset successfully.'})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
