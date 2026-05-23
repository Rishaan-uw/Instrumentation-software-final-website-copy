#!/usr/bin/env python3
"""
Data logging system for spectroscopy measurements.
Saves all data with timestamps for post-competition analysis.
"""

import json
import os
from datetime import datetime
import numpy as np

class SpectroscopyLogger:
    def __init__(self, log_dir="spectroscopy_logs"):
        """
        Initialize logger.
        
        Args:
            log_dir: Directory to save log files
        """
        self.log_dir = log_dir
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(log_dir, f"session_{self.session_id}")
        
        # Create directories
        os.makedirs(self.session_dir, exist_ok=True)
        os.makedirs(os.path.join(self.session_dir, "spectra"), exist_ok=True)
        os.makedirs(os.path.join(self.session_dir, "images"), exist_ok=True)
        
        # Initialize session log
        self.session_log = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'measurements': []
        }
        
        print(f"✓ Logger initialized: {self.session_dir}")
    
    def log_measurement(self, measurement_data, sample_id=None):
        """
        Log a single measurement.
        
        Args:
            measurement_data: dict with spectrum, peaks, analysis results
            sample_id: optional identifier for the sample
        
        Returns:
            measurement_id: unique ID for this measurement
        """
        # Generate measurement ID
        measurement_id = len(self.session_log['measurements']) + 1
        timestamp = datetime.now().isoformat()
        
        if sample_id is None:
            sample_id = f"sample_{measurement_id:03d}"
        
        # Create measurement record
        record = {
            'measurement_id': measurement_id,
            'sample_id': sample_id,
            'timestamp': timestamp,
            'peaks_detected': measurement_data.get('peaks_detected', 0),
            'biosignature_analysis': measurement_data.get('biosignature_analysis', {})
        }
        
        # Save spectrum data separately (can be large)
        if 'wavelengths' in measurement_data and 'spectrum' in measurement_data:
            spectrum_file = os.path.join(
                self.session_dir, 
                "spectra", 
                f"{sample_id}_spectrum.npz"
            )
            np.savez(
                spectrum_file,
                wavelengths=measurement_data['wavelengths'],
                spectrum=measurement_data['spectrum'],
                peaks=measurement_data.get('peak_wavelengths', [])
            )
            record['spectrum_file'] = spectrum_file
        
        # Save raw image if provided
        if 'raw_image' in measurement_data:
            image_file = os.path.join(
                self.session_dir,
                "images",
                f"{sample_id}_raw.npy"
            )
            np.save(image_file, measurement_data['raw_image'])
            record['image_file'] = image_file
        
        # Add to session log
        self.session_log['measurements'].append(record)
        
        # Save session log
        self._save_session_log()
        
        print(f"✓ Logged measurement {measurement_id}: {sample_id}")
        return measurement_id
    
    def _save_session_log(self):
        """Save session log to JSON file"""
        log_file = os.path.join(self.session_dir, "session_log.json")
        with open(log_file, 'w') as f:
            json.dump(self.session_log, f, indent=2)
    
    def add_note(self, note):
        """Add a text note to the session log"""
        if 'notes' not in self.session_log:
            self.session_log['notes'] = []
        
        self.session_log['notes'].append({
            'timestamp': datetime.now().isoformat(),
            'note': note
        })
        self._save_session_log()
    
    def end_session(self):
        """Close the logging session"""
        self.session_log['end_time'] = datetime.now().isoformat()
        self._save_session_log()
        print(f"✓ Session ended: {len(self.session_log['measurements'])} measurements logged")
    
    def get_summary(self):
        """Get summary of current session"""
        total = len(self.session_log['measurements'])
        
        if total == 0:
            return "No measurements recorded"
        
        # Count biosignature detections
        high_conf = sum(1 for m in self.session_log['measurements'] 
                       if m['biosignature_analysis'].get('confidence') == 'high')
        medium_conf = sum(1 for m in self.session_log['measurements']
                         if m['biosignature_analysis'].get('confidence') == 'medium')
        
        summary = f"""
Session Summary:
- Total measurements: {total}
- High confidence biosignatures: {high_conf}
- Medium confidence biosignatures: {medium_conf}
- Session ID: {self.session_id}
- Log directory: {self.session_dir}
        """
        return summary


# Example usage and test
if __name__ == "__main__":
    # Test the logger
    logger = SpectroscopyLogger()
    
    # Simulate some measurements
    for i in range(3):
        fake_data = {
            'peaks_detected': np.random.randint(1, 5),
            'wavelengths': np.linspace(400, 700, 100),
            'spectrum': np.random.rand(100) * 1000,
            'peak_wavelengths': [450, 550],
            'biosignature_analysis': {
                'confidence': np.random.choice(['none', 'low', 'medium', 'high']),
                'chlorophyll': bool(np.random.randint(2)),
                'carotenoids': bool(np.random.randint(2))
            }
        }
        
        logger.log_measurement(fake_data, sample_id=f"test_sample_{i+1}")
    
    # Add a note
    logger.add_note("Test session - calibration check")
    
    # Print summary
    print(logger.get_summary())
    
    # End session
    logger.end_session()