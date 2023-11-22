from scipy.io.wavfile import read
import matplotlib.pyplot as plt
plt.rcParams["figure.figsize"] = [13, 7]
plt.rcParams["figure.autolayout"] = True
input_data = read("example2.wav")
audio = input_data[1]
plt.plot(audio[700:5024], "green")
plt.ylabel("Amplitude")
plt.xlabel("Time")
plt.show()