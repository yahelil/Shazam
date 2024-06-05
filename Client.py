import socket
import pyaudio
import wave

# Define server address and port
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432

# Create a client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_HOST, SERVER_PORT))

client_name = "Client1"
password = "1678"
def Register():
    # Register with the server
    client_socket.send(f"REGISTER {client_name} {password}".encode('utf-8'))

    # Receive server response
    response = client_socket.recv(1024).decode('utf-8')
    print(f"Server response: {response}")
    client_socket.close()

def record_audio(filename="output.wav", record_seconds=2, sample_rate=44100, chunk_size=1024, channels=1):
    audio = pyaudio.PyAudio()

    # Open stream
    stream = audio.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk_size)

    print("Recording...")

    frames = []

    for _ in range(0, int(sample_rate / chunk_size * record_seconds)):
        data = stream.read(chunk_size)
        frames.append(data)

    print("Recording finished")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded data as a WAV file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

    print(f"Audio saved to {filename}")


def send_sample(client_socket: socket, filename="output.wav"):
    """
    Sends a .wav file to the server over the given socket.

    Args:
        client_socket (socket): The socket connected to the server.
        filename (str): The name of the file to send.

    Returns:
        None
    """
    with open(filename, 'rb') as f:
        print("Sending file...")
        while True:
            data = f.read(1024)
            if not data:
                break
            client_socket.sendall(data)
    print("File sent successfully")

def Assign():
    client_socket.send(f"ASSIGN {client_name} {password}".encode('utf-8'))

    response = client_socket.recv(1024).decode('utf-8')
    print(f"Server response: {response}")
    if response == "Connection APPROVED":
        record_audio()
        send_sample(client_socket, "MoreWavs/FireToTheRain2.wav")
    if response == "Connection DENIED":
        client_socket.close()

register_or_assign = input("Do you want to register or assign?")
if register_or_assign == 'r':
    Register()
elif register_or_assign == 'a':
    Assign()

# Close the connection
client_socket.close()



