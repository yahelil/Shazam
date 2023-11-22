import numpy as np
from matplotlib import pyplot as plt
from scipy.fft import rfft, rfftfreq, irfft

SAMPLE_RATE = 44100  # Hertz
DURATION = 5  # Seconds


def generate_sine_wave(freq, sample_rate, duration):
    x = np.linspace(0, duration, sample_rate * duration, endpoint=False)
    frequencies = x * freq
    # 2pi because np.sin takes radians
    y = np.sin((2 * np.pi) * frequencies)
    return x, y


# Generate a 2 hertz sine wave that lasts for 5 seconds
_, nice_tone = generate_sine_wave(400, SAMPLE_RATE, DURATION)
_, noise_tone = generate_sine_wave(4000, SAMPLE_RATE, DURATION)
noise_tone = noise_tone * 0.3

mixed_tone = nice_tone + noise_tone
normalized_tone = np.int16((mixed_tone / mixed_tone.max()) * 32767)

# Furior transform
N = SAMPLE_RATE * DURATION
yf = rfft(normalized_tone)
xf = rfftfreq(N, 1 / SAMPLE_RATE)

# The maximum frequency is half the sample rate
points_per_freq = len(xf) / (SAMPLE_RATE / 2)

# Our target frequency is 4000 Hz
target_idx = int(points_per_freq * 4000)

yf[target_idx - 1 : target_idx + 2] = 0
new_sig = irfft(yf)
plt.plot(new_sig[:1000])
plt.show()
#scipy.io.wavfile.write("mysinewave.wav", SAMPLE_RATE, normalized_tone)
