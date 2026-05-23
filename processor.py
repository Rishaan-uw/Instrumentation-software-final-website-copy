import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.interpolate import interp1d

class SpectrometerProcessor:
    """
    Processes 2D sensor data from imaging spectrometer.
    
    Pipeline:
    Raw 2D image → 1D spectrum → Wavelength calibration → Analysis
    """
    
    def __init__(self, wavelength_range=(400, 700)):
        """
        Args:
            wavelength_range: (min_nm, max_nm) for visible spectrum
        """
        self.wavelength_range = wavelength_range
        self.calibration = None
        
    def extract_spectrum(self, image_2d, method='average'):
        """
        Extract 1D spectrum from 2D sensor image. 
        
        Args:
            image_2d: 2D numpy array from sensor (height x width)
            method: 'average', 'median', or 'center_row'
        
        Returns:
            1D spectrum array (length = image width)
        """
        if method == 'average':
            # Average all rows - good for uniform samples
            spectrum = np.mean(image_2d, axis=0)
        elif method == 'median':
            # More robust to outliers
            spectrum = np.median(image_2d, axis=0)
        elif method == 'center_row':
            # Use only center row - for point measurements
            center_row = image_2d.shape[0] // 2
            spectrum = image_2d[center_row, :]
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return spectrum
    
    def wavelength_calibration(self, pixel_wavelength_pairs):
        """
        Create wavelength calibration from known spectral lines.
        
        Args:
            pixel_wavelength_pairs: List of (pixel, wavelength_nm) tuples
                Example: [(200, 450), (640, 550), (1100, 650)]
        
        This would come from calibration with known light source.
        """
        pixels = [p[0] for p in pixel_wavelength_pairs]
        wavelengths = [p[1] for p in pixel_wavelength_pairs]
        
        # Create interpolation function
        self.calibration = interp1d(pixels, wavelengths, 
                                    kind='linear', 
                                    fill_value='extrapolate')
        
        print(f"✓ Calibration created with {len(pixels)} points")
        return self.calibration
    
    def apply_calibration(self, spectrum_raw):
        """
        Convert pixel numbers to wavelengths.
        
        Args:
            spectrum_raw: 1D array indexed by pixel number
        
        Returns:
            wavelengths: 1D array of wavelength values (nm)
            spectrum: 1D array of intensities at those wavelengths
        """
        if self.calibration is None:
            raise ValueError("No calibration loaded! Call wavelength_calibration() first")
        
        pixels = np.arange(len(spectrum_raw))
        wavelengths = self.calibration(pixels)
        
        return wavelengths, spectrum_raw
    
    def baseline_correction(self, spectrum, method='polynomial', degree=3):
        """
        Remove baseline drift from spectrum.
        
        Args:
            spectrum: 1D intensity array
            method: 'polynomial' or 'rolling_minimum'
            degree: polynomial degree for fitting
        
        Returns:
            corrected_spectrum: baseline-subtracted spectrum
        """
        if method == 'polynomial':
            # Fit polynomial to spectrum
            x = np.arange(len(spectrum))
            coeffs = np.polyfit(x, spectrum, degree)
            baseline = np.polyval(coeffs, x)
            corrected = spectrum - baseline
            
        elif method == 'rolling_minimum':
            # Rolling minimum filter
            window = len(spectrum) // 20
            baseline = signal.medfilt(spectrum, kernel_size=window)
            corrected = spectrum - baseline
        else:
            raise ValueError(f"Unknown baseline method: {method}")
        
        return corrected
    
    def find_peaks(self, wavelengths, spectrum, prominence=100):
        """
        Find absorption/emission peaks in spectrum.
        
        Args:
            wavelengths: 1D array of wavelength values
            spectrum: 1D array of intensities
            prominence: minimum peak prominence
        
        Returns:
            peak_wavelengths: wavelengths of detected peaks
            peak_intensities: intensities at peaks
        """
        # Find peaks
        peak_indices, properties = signal.find_peaks(spectrum, prominence=prominence)
        
        peak_wavelengths = wavelengths[peak_indices]
        peak_intensities = spectrum[peak_indices]
        
        return peak_wavelengths, peak_intensities, properties
    
    def normalize_spectrum(self, spectrum):
        """Normalize spectrum to 0-1 range"""
        return (spectrum - np.min(spectrum)) / (np.max(spectrum) - np.min(spectrum))
    
    def smooth_spectrum(self, spectrum, window_length=11):
        """Apply Savitzky-Golay smoothing filter"""
        return signal.savgol_filter(spectrum, window_length, 3)


def demo_processing_pipeline():
    """
    Demonstration of complete processing pipeline.
    Run this to test your code!
    """
    print("=== Spectroscopy Processing Demo ===\n")
    
    # 1. Load synthetic data (or real data when you have it)
    print("1. Loading test data...")
    image_2d = np.load('test_spectrum.npy')
    print(f"   Raw image shape: {image_2d.shape}")
    
    # 2. Initialize processor
    processor = SpectrometerProcessor(wavelength_range=(400, 700))
    
    # 3. Extract 1D spectrum from 2D image
    print("\n2. Extracting 1D spectrum...")
    spectrum_raw = processor.extract_spectrum(image_2d, method='average')
    print(f"   Spectrum length: {len(spectrum_raw)} pixels")
    
    # 4. Create wavelength calibration
    # These would come from measuring known spectral lines
    # For now, simulate linear calibration
    print("\n3. Applying wavelength calibration...")
    calibration_points = [
        (0, 400),      # Pixel 0 = 400nm
        (640, 550),    # Pixel 640 = 550nm (center)
        (1279, 700)    # Pixel 1279 = 700nm
    ]
    processor.wavelength_calibration(calibration_points)
    wavelengths, spectrum = processor.apply_calibration(spectrum_raw)
    
    # 5. Baseline correction
    print("\n4. Baseline correction...")
    spectrum_corrected = processor.baseline_correction(spectrum)
    
    # 6. Smoothing
    print("\n5. Smoothing spectrum...")
    spectrum_smooth = processor.smooth_spectrum(spectrum_corrected)
    
    # 7. Peak detection
    print("\n6. Finding peaks...")
    peak_wl, peak_int, _ = processor.find_peaks(wavelengths, spectrum_smooth, prominence=50)
    print(f"   Found {len(peak_wl)} peaks:")
    for wl, intensity in zip(peak_wl, peak_int):
        print(f"   - {wl:.1f} nm (intensity: {intensity:.0f})")
    
    # 8. Visualization
    print("\n7. Generating plots...")
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # Plot 1: Raw 2D image
    im = axes[0].imshow(image_2d, cmap='hot', aspect='auto')
    axes[0].set_title('Raw 2D Sensor Image')
    axes[0].set_xlabel('Pixel Column (Wavelength →)')
    axes[0].set_ylabel('Pixel Row (Spatial)')
    plt.colorbar(im, ax=axes[0], label='Intensity')
    
    # Plot 2: Spectrum processing steps
    axes[1].plot(wavelengths, spectrum, 'gray', alpha=0.5, label='Raw')
    axes[1].plot(wavelengths, spectrum_corrected, 'blue', alpha=0.7, label='Baseline Corrected')
    axes[1].plot(wavelengths, spectrum_smooth, 'red', linewidth=2, label='Smoothed')
    axes[1].set_title('Spectrum Processing Steps')
    axes[1].set_xlabel('Wavelength (nm)')
    axes[1].set_ylabel('Intensity')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # Plot 3: Final spectrum with peaks
    axes[2].plot(wavelengths, spectrum_smooth, 'black', linewidth=2)
    axes[2].plot(peak_wl, peak_int, 'ro', markersize=10, label=f'{len(peak_wl)} peaks detected')
    for wl, intensity in zip(peak_wl, peak_int):
        axes[2].annotate(f'{wl:.0f}nm', 
                        xy=(wl, intensity), 
                        xytext=(0, 10), 
                        textcoords='offset points',
                        ha='center', fontsize=9)
    axes[2].set_title('Final Spectrum with Peak Detection')
    axes[2].set_xlabel('Wavelength (nm)')
    axes[2].set_ylabel('Intensity')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('processing_pipeline_output.png', dpi=150)
    print("   ✓ Saved to: processing_pipeline_output.png")
    plt.show()
    
    # 9. Save processed data
    output_data = {
        'wavelengths': wavelengths,
        'spectrum_raw': spectrum,
        'spectrum_processed': spectrum_smooth,
        'peaks': {'wavelengths': peak_wl, 'intensities': peak_int}
    }
    np.savez('processed_spectrum.npz', **output_data)
    print("\n✓ Processed data saved to: processed_spectrum.npz")
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    demo_processing_pipeline()