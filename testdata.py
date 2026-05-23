import numpy as np
import matplotlib.pyplot as plt

def generate_synthetic_spectrometer_image(width=1280, height=1024, num_peaks=3):
    """
    Simulates what Python 1300 sensor outputs for a spectrometer.
    
    For a spectrometer with 2D sensor:
    - Each COLUMN = one wavelength
    - Each ROW = spatial position along entrance slit
    - Vertical axis shows if sample is uniform along slit
    
    Returns:
        2D numpy array simulating sensor output
    """
    
    # Create base noise (sensor dark current)
    image = np.random.normal(100, 10, (height, width))
    
    # Add spectral lines (these would be absorption/emission from sample)
    # Peaks at different wavelengths (columns)
    peak_positions = np.linspace(200, width-200, num_peaks)
    peak_heights = np.random.uniform(500, 2000, num_peaks)
    peak_widths = np.random.uniform(20, 50, num_peaks)
    
    # FIXED: Renamed 'height' to 'peak_height' to avoid shadowing the parameter
    for pos, peak_height, width_sigma in zip(peak_positions, peak_heights, peak_widths):
        # Create Gaussian peak
        x = np.arange(width)
        gaussian = peak_height * np.exp(-((x - pos)**2) / (2 * width_sigma**2))
        
        # Add to all rows (uniform illumination along slit)
        for row in range(height):
            image[row, :] += gaussian * (1 + 0.1 * np.random.randn())  # Add slight spatial variation
    
    # Clip to sensor range (12-bit sensor = 0-4095)
    image = np.clip(image, 0, 4095).astype(np.uint16)
    
    return image

def save_test_image(filename="test_spectrum.npy"):
    """Generate and save test data"""
    test_data = generate_synthetic_spectrometer_image()
    np.save(filename, test_data)
    print(f"✓ Generated test data: {test_data.shape}")
    print(f"✓ Saved to: {filename}")
    return test_data

if __name__ == "__main__":
    # Generate test data
    data = save_test_image()
    
    # Quick visualization
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.imshow(data, cmap='gray', aspect='auto')
    plt.title('Raw 2D Sensor Data')
    plt.xlabel('Pixel Column (Wavelength)')
    plt.ylabel('Pixel Row (Spatial)')
    plt.colorbar(label='Intensity')
    
    plt.subplot(1, 2, 2)
    spectrum = np.mean(data, axis=0)  # Average all rows
    plt.plot(spectrum)
    plt.title('Extracted 1D Spectrum')
    plt.xlabel('Pixel Number')
    plt.ylabel('Intensity')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('test_spectrum_preview.png')
    print("✓ Preview saved to: test_spectrum_preview.png")
    plt.show()