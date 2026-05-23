#!/usr/bin/env python3
"""
Simple web dashboard for viewing spectroscopy results.
Access from any browser on the network.
"""

from flask import Flask, render_template, jsonify
import json
import os
import numpy as np
from datetime import datetime

app = Flask(__name__)

# Global state
latest_results = None
session_stats = {
    'total_measurements': 0,
    'high_confidence': 0,
    'medium_confidence': 0,
    'low_confidence': 0
}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/latest')
def get_latest():
    """Get latest measurement results"""
    if latest_results is None:
        return jsonify({'status': 'no_data'})
    
    return jsonify({
        'status': 'ok',
        'data': latest_results
    })

@app.route('/api/stats')
def get_stats():
    """Get session statistics"""
    return jsonify(session_stats)

@app.route('/api/history')
def get_history():
    """Get recent measurement history"""
    # Find most recent session
    log_dir = "spectroscopy_logs"
    
    if not os.path.exists(log_dir):
        return jsonify({'status': 'no_logs', 'data': []})
    
    sessions = sorted([d for d in os.listdir(log_dir) if d.startswith('session_')])
    
    if not sessions:
        return jsonify({'status': 'no_logs', 'data': []})
    
    # Load most recent session
    latest_session = sessions[-1]
    session_file = os.path.join(log_dir, latest_session, 'session_log.json')
    
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    # Return last 10 measurements
    history = session_data.get('measurements', [])[-10:]
    
    return jsonify({
        'status': 'ok',
        'data': history
    })

def update_results(results):
    """Update dashboard with new results"""
    global latest_results, session_stats
    
    latest_results = results
    session_stats['total_measurements'] += 1
    
    confidence = results.get('biosignature_analysis', {}).get('confidence', 'none')
    if confidence == 'high':
        session_stats['high_confidence'] += 1
    elif confidence == 'medium':
        session_stats['medium_confidence'] += 1
    elif confidence == 'low':
        session_stats['low_confidence'] += 1

def run_dashboard(host='0.0.0.0', port=5001):
    """Start the web dashboard"""
    print(f"\n{'='*60}")
    print(f"🌐 Web Dashboard Starting")
    print(f"{'='*60}")
    print(f"Access dashboard at:")
    print(f"  - Local: http://localhost:{port}")
    print(f"  - Network: http://<rover-ip>:{port}")
    print(f"{'='*60}\n")
    
    app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    run_dashboard()