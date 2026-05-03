def generate_suggestions(data, prediction, cost_per_unit):
    suggestions = []
    
    appliance = str(data.get('Appliance', ''))
    temperature = float(data.get('Temperature', 25))
    time_of_day = str(data.get('TimeOfDay', 'Afternoon'))
    usage_time = float(data.get('UsageTime', 1.0))
    power_w = float(data.get('Power', 0))
    estimated_cost = prediction * float(cost_per_unit)
    
    # Advanced Appliance Analysis
    if appliance == 'Air Conditioning':
        if temperature < 22 and usage_time > 2:
            suggestions.append({
                'title': 'AC Temperature Optimization',
                'icon': '❄️',
                'desc': 'Setting the AC below 22°C significantly increases power draw. Raising it to 24°C can reduce consumption by up to 18% without compromising comfort.'
            })
        if time_of_day == 'Morning' and temperature < 24:
            suggestions.append({
                'title': 'Morning Cooling Strategy',
                'icon': '🌅',
                'desc': 'Morning ambient temperatures are usually lower. Consider using ventilation instead of AC to save up to 0.5 kWh per hour.'
            })

    elif appliance in ['Washing Machine', 'Dishwasher']:
        if time_of_day in ['Evening', 'Afternoon']:
            suggestions.append({
                'title': 'Peak-Load Shifting',
                'icon': '📈',
                'desc': f'Running the {appliance} during peak hours strains the grid. Delaying this to late night or early morning utilizes off-peak rates, potentially lowering costs.'
            })
        if usage_time > 1.5:
            suggestions.append({
                'title': 'Eco-Mode Utilization',
                'icon': '💧',
                'desc': 'Your usage time is high. Ensure you are running full loads on "Eco Mode" which uses lower water temperatures and saves 30% energy.'
            })

    elif appliance == 'Heater':
        if usage_time > 4:
            suggestions.append({
                'title': 'Thermal Insulation Alert',
                'icon': '🔥',
                'desc': 'Continuous heating for over 4 hours implies potential heat loss. Check window seals and doors, or use a thermostat with a timer to prevent energy waste.'
            })

    elif appliance == 'Fridge':
        if power_w > 300:
            suggestions.append({
                'title': 'Compressor Health Check',
                'icon': '🧊',
                'desc': 'The reported power draw for this fridge is abnormally high (>300W). Clean the condenser coils or check the door seals to prevent continuous compressor running.'
            })

    elif appliance in ['Computer', 'TV']:
        if usage_time > 8:
            suggestions.append({
                'title': 'Vampire Drain Prevention',
                'icon': '🔌',
                'desc': 'Extended operation detected. Enable aggressive sleep settings and consider using a smart power strip to eliminate standby power when not in active use.'
            })

    # High Consumption Cost Alert
    if estimated_cost > 15.0:
        suggestions.append({
            'title': 'High Cost Anomaly',
            'icon': '💰',
            'desc': f'This single session is projected to cost ₹{estimated_cost:.2f}. Evaluate if this {appliance} usage is strictly necessary at this duration.'
        })

    # Fallback / Optimal
    if not suggestions:
        if prediction < 1.0:
            suggestions.append({
                'title': 'Optimal Efficiency',
                'icon': '🌱',
                'desc': 'This appliance is running efficiently. Your usage pattern matches our ideal eco-friendly profiles.'
            })
        else:
            suggestions.append({
                'title': 'Standard Operation',
                'icon': '⚡',
                'desc': f'The {appliance} is operating within normal parameters for {time_of_day} usage.'
            })
        
    return suggestions
