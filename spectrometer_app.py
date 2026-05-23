#!/usr/bin/env python3
"""
Enhanced spectroscopy application with logging and real-time visualization.
"""

from processor import SpectrometerProcessor
from datalogger import SpectroscopyLogger
from realtime_plotter import RealtimeSpectrumPlotter
import numpy as np
import json
import time

class SpectrometerApp:
    def __init__(self, enable_realtime=True, enable_logging=True):
        """
        Initialize application.
        
        Args:
            enable_realtime: Enable real-time plotting
            enable_logging: Enable data logging
        """
        self.processor = SpectrometerProcessor(wavelength_range=(400, 700))
        self.load_default_calibration()
        
        # Optional features
        self.logger = SpectroscopyLogger() if enable_logging else None
        self.plotter = RealtimeSpectrumPlotter() if enable_realtime else None
        
        print(f"✓ Spectrometer initialized")
        print(f"  - Logging: {'ON' if enable_logging else 'OFF'}")
        print(f"  - Real-time plot: {'ON' if enable_realtime else 'OFF'}")
    
    def load_default_calibration(self):
        """Default linear calibration for testing"""
        calibration_points = [
            (0, 400),
            (640, 550),
            (1279, 700)
        ]
        self.processor.wavelength_calibration(calibration_points)
    
    def analyze_sample(self, image_2d, sample_id=None):
        """
        Complete analysis of a sample with logging and visualization.
        
        Args:
            image_2d: Raw sensor data
            sample_id: Optional sample identifier
        
        Returns:
            dict with analysis results
        """
        print(f"\nAnalyzing {sample_id or 'sample'}...")
        
        # Process spectrum
        spectrum_raw = self.processor.extract_spectrum(image_2d)
        wavelengths, spectrum = self.processor.apply_calibration(spectrum_raw)
        spectrum_corrected = self.processor.baseline_correction(spectrum)
        spectrum_smooth = self.processor.smooth_spectrum(spectrum_corrected)
        
        # Find peaks
        peak_wl, peak_int, _ = self.processor.find_peaks(wavelengths, spectrum_smooth)
        
        # Analyze for biosignatures
        analysis = self.detect_biosignatures(peak_wl, peak_int)
        
        # Prepare results
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
        
        # Update real-time plot
        if self.plotter:
            self.plotter.update(wavelengths, spectrum_smooth, peaks=(peak_wl, peak_int))
        
        # Log data
        if self.logger:
            self.logger.log_measurement(results, sample_id=sample_id)
        
        return results
    
    def detect_biosignatures(self, peak_wavelengths, peak_intensities):
        """Look for signs of life in the spectrum"""
        has_chlorophyll = any(425 < p < 435 for p in peak_wavelengths) or \
                         any(655 < p < 665 for p in peak_wavelengths)
        
        has_carotenoids = any(450 < p < 550 for p in peak_wavelengths)
        has_organics = any(400 < p < 450 for p in peak_wavelengths)
        
        indicators = sum([has_chlorophyll, has_carotenoids, has_organics])
        
        if indicators == 0:
            confidence = "none"
            interpretation = "No biosignatures detected"
        elif indicators == 1:
            confidence = "low"
            interpretation = "Weak biosignature detected"
        elif indicators == 2:
            confidence = "medium"
            interpretation = "Multiple biosignatures detected"
        else:
            confidence = "high"
            interpretation = "Strong biosignature pattern detected"
        
        return {
            'chlorophyll': has_chlorophyll,
            'carotenoids': has_carotenoids,
            'organics': has_organics,
            'confidence': confidence,
            'interpretation': interpretation
        }
    
    def shutdown(self):
        """Clean shutdown of application"""
        if self.logger:
            print(self.logger.get_summary())
            self.logger.end_session()
        
        if self.plotter:
            self.plotter.save_plot('final_spectrum.png')
            self.plotter.close()
        
        print("✓ Application shutdown complete")


def demo_batch_processing():
    """Demo: Process multiple samples"""
    print("=== Batch Processing Demo ===\n")
    
    # Initialize app with all features
    app = SpectrometerApp(enable_realtime=True, enable_logging=True)
    
    # Process multiple samples
    num_samples = 5
    for i in range(num_samples):
        # Load or generate sample data
        sample_data = np.load('test_spectrum.npy')
        
        # Add some variation to make it interesting
        noise = np.random.normal(0, 100, sample_data.shape)
        sample_data = sample_data + noise
        
        # Analyze
        results = app.analyze_sample(sample_data, sample_id=f"field_sample_{i+1}")
        
        # Print quick summary
        bio = results['biosignature_analysis']
        print(f"  → {bio['confidence'].upper()}: {bio['interpretation']}")
        
        time.sleep(0.5)  # Simulate time between samples
    
    print("\n" + "="*50)
    input("Press Enter to finish...")
    
    # Shutdown
    app.shutdown()


if __name__ == "__main__":
    demo_batch_processing()
