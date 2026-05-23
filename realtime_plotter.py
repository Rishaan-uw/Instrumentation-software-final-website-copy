#!/usr/bin/env python3
"""
Real-time spectrum visualization.
Updates plot as new data comes in.
"""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from collections import deque

class RealtimeSpectrumPlotter:
    def __init__(self, max_history=10):
        """
        Initialize real-time plotter.
        
        Args:
            max_history: Number of past spectra to keep in memory
        """
        self.max_history = max_history
        self.spectrum_history = deque(maxlen=max_history)
        
        # Set up the plot
        plt.ion()  # Interactive mode
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Current spectrum plot
        self.line_current, = self.ax1.plot([], [], 'b-', linewidth=2, label='Current')
        self.peaks_current = self.ax1.plot([], [], 'ro', markersize=8, label='Peaks')[0]
        self.ax1.set_xlabel('Wavelength (nm)')
        self.ax1.set_ylabel('Intensity')
        self.ax1.set_title('Current Spectrum')
        self.ax1.legend()
        self.ax1.grid(True, alpha=0.3)
        
        # History plot (overlaid spectra)
        self.lines_history = []
        self.ax2.set_xlabel('Wavelength (nm)')
        self.ax2.set_ylabel('Intensity')
        self.ax2.set_title(f'Last {max_history} Spectra')
        self.ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
    
    def update(self, wavelengths, spectrum, peaks=None):
        """
        Update plot with new spectrum.
        
        Args:
            wavelengths: 1D array of wavelength values
            spectrum: 1D array of intensities
            peaks: Optional tuple of (peak_wavelengths, peak_intensities)
        """
        # Update current spectrum
        self.line_current.set_data(wavelengths, spectrum)
        
        # Update peaks if provided
        if peaks is not None:
            peak_wl, peak_int = peaks
            self.peaks_current.set_data(peak_wl, peak_int)
        
        # Auto-scale axes
        self.ax1.relim()
        self.ax1.autoscale_view()
        
        # Add to history
        self.spectrum_history.append((wavelengths, spectrum))
        
        # Update history plot
        # Clear old lines
        for line in self.lines_history:
            line.remove()
        self.lines_history = []
        
        # Plot all spectra in history with fading alpha
        n = len(self.spectrum_history)
        for i, (wl, spec) in enumerate(self.spectrum_history):
            alpha = 0.2 + 0.6 * (i / max(n-1, 1))  # Fade older spectra
            line, = self.ax2.plot(wl, spec, 'b-', alpha=alpha, linewidth=1)
            self.lines_history.append(line)
        
        # Auto-scale history axes
        self.ax2.relim()
        self.ax2.autoscale_view()
        
        # Redraw
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.01)
    
    def save_plot(self, filename='current_spectrum.png'):
        """Save current plot to file"""
        self.fig.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"✓ Plot saved to {filename}")
    
    def close(self):
        """Close the plot"""
        plt.close(self.fig)


# Example usage
if __name__ == "__main__":
    import time
    
    plotter = RealtimeSpectrumPlotter(max_history=5)
    
    # Simulate incoming spectra
    for i in range(10):
        # Generate fake spectrum with peaks
        wavelengths = np.linspace(400, 700, 300)
        
        # Base spectrum with some peaks
        spectrum = 500 + 100 * np.sin(wavelengths / 50)
        
        # Add random peaks
        num_peaks = np.random.randint(2, 5)
        for _ in range(num_peaks):
            peak_pos = np.random.uniform(420, 680)
            peak_height = np.random.uniform(200, 500)
            spectrum += peak_height * np.exp(-((wavelengths - peak_pos)**2) / 100)
        
        # Add noise
        spectrum += np.random.normal(0, 20, len(wavelengths))
        
        # Find peaks (simple method)
        from scipy import signal
        peak_indices, _ = signal.find_peaks(spectrum, prominence=100)
        peak_wl = wavelengths[peak_indices]
        peak_int = spectrum[peak_indices]
        
        # Update plot
        plotter.update(wavelengths, spectrum, peaks=(peak_wl, peak_int))
        
        print(f"Updated spectrum {i+1}/10")
        time.sleep(1)  # Simulate time between measurements
    
    plotter.save_plot('realtime_demo.png')
    print("\nPress Enter to close...")
    input()
    plotter.close()