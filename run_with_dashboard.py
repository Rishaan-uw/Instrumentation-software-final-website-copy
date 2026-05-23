#!/usr/bin/env python3
"""
Run spectroscopy app with web dashboard.
"""

from processor import SpectrometerProcessor
from datalogger import SpectroscopyLogger
from realtime_plotter import RealtimeSpectrumPlotter
import web_dashboard
import numpy as np
import time
import threading

class SpectrometerAppWithDashboard:
    def __init__(self):
        self.processor = SpectrometerProcessor(wavelength_range=(400, 700))
        self.logger = SpectroscopyLogger()
        self.plotter = RealtimeSpectrumPlotter()
        self.load_default_calibration()
        
        # Start web dashboard in background thread
        self.dashboard_thread = threading.Thread(
            target=web_dashboard.run_dashboard,
            daemon=True
        )
        self.dashboard_thread.start()
        
        print("✓ Application ready with web dashboard")
        time.sleep(2)  # Give dashboard time to start
    
    def load_default_calibration(self):
        calibration_points = [(0, 400), (640, 550), (1279, 700)]
        self.processor.wavelength_calibration(calibration_points)
    
    def analyze_sample(self, image_2d, sample_id=None):
        print(f"\nAnalyzing {sample_id or 'sample'}...")
        
        # Process
        spectrum_raw = self.processor.extract_spectrum(image_2d)
        wavelengths, spectrum = self.processor.apply_calibration(spectrum_raw)
        spectrum_corrected = self.processor.baseline_correction(spectrum)
        spectrum_smooth = self.processor.smooth_spectrum(spectrum_corrected)
        
        peak_wl, peak_int, _ = self.processor.find_peaks(wavelengths, spectrum_smooth)
        analysis = self.detect_biosignatures(peak_wl, peak_int)
        
        results = {
            'timestamp': time.time(),
            'sample_id': sample_id,
            'peaks_detected': len(peak_wl),
            'peak_wavelengths': peak_wl.tolist(),
            'wavelengths': wavelengths.tolist(),
            'spectrum': spectrum_smooth.tolist(),
            'raw_image': image_2d,
            'biosignature_analysis': analysis
        }
        
        # Update all displays
        self.plotter.update(wavelengths, spectrum_smooth, peaks=(peak_wl, peak_int))
        self.logger.log_measurement(results, sample_id=sample_id)
        web_dashboard.update_results(results)  # Update web dashboard
        
        return results
    
    def detect_biosignatures(self, peak_wavelengths, peak_intensities):
        has_chlorophyll = any(425 < p < 435 for p in peak_wavelengths) or \
                         any(655 < p < 665 for p in peak_wavelengths)
        has_carotenoids = any(450 < p < 550 for p in peak_wavelengths)
        has_organics = any(400 < p < 450 for p in peak_wavelengths)
        
        indicators = sum([has_chlorophyll, has_carotenoids, has_organics])
        
        if indicators == 0:
            confidence, interpretation = "none", "No biosignatures detected"
        elif indicators == 1:
            confidence, interpretation = "low", "Weak biosignature detected"
        elif indicators == 2:
            confidence, interpretation = "medium", "Multiple biosignatures detected"
        else:
            confidence, interpretation = "high", "Strong biosignature pattern detected"
        
        return {
            'chlorophyll': has_chlorophyll,
            'carotenoids': has_carotenoids,
            'organics': has_organics,
            'confidence': confidence,
            'interpretation': interpretation
        }
    
    def shutdown(self):
        print(self.logger.get_summary())
        self.logger.end_session()
        self.plotter.save_plot('final_spectrum.png')
        self.plotter.close()
        print("✓ Shutdown complete")


def main():
    print("="*60)
    print("HUSKY ROBOTICS - SPECTROSCOPY SYSTEM")
    print("URC 2025 - Prometheus Rover")
    print("="*60)
    
    app = SpectrometerAppWithDashboard()
    
    print("\n📱 Open web dashboard in browser:")
    print("   http://localhost:5000")
    print("\nProcessing samples...")
    
    # Process multiple samples
    for i in range(5):
        sample_data = np.load('test_spectrum.npy')
        noise = np.random.normal(0, 100, sample_data.shape)
        sample_data = sample_data + noise
        
        results = app.analyze_sample(sample_data, sample_id=f"mars_sample_{i+1}")
        
        bio = results['biosignature_analysis']
        print(f"  ✓ {bio['confidence'].upper()}: {bio['interpretation']}")
        
        time.sleep(3)  # Time between samples
    
    print("\n" + "="*60)
    print("Keep browser open to view dashboard")
    print("Press Ctrl+C to exit")
    print("="*60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        app.shutdown()


if __name__ == "__main__":
    main()