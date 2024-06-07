import socket
import pyaudio
import wave
from ast import literal_eval
import tkinter as tk

# Define server address and port
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432

# Create a client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_HOST, SERVER_PORT))


def register(client_name="Client1", password="1678"):
    # Register with the server
    client_socket.send(f"REGISTER {client_name} {password}".encode('utf-8'))

    # Receive server response
    response = client_socket.recv(1024).decode('utf-8')
    print(f"Server response: {response}")
    client_socket.close()
    if response.startswith("Registered") or response.startswith(client_name):
        return "Registered"
    else:
        return "Failed"


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
            client_socket.sendall(data)
            if not data:
                break
    print("File sent successfully")


def assign(client_name="Client1", password="1678", filename="output.wav"):
    send_sample(client_socket, filename)
    client_socket.send("stop".encode('utf-8'))
    msg = client_socket.recv(1024).decode('utf-8')
    two_part_msg = msg.split("\n")
    Is_Dominant = two_part_msg[0].split()[1] != "False"
    if Is_Dominant:
        result = two_part_msg[1].split()[-1]
        return [result]
        #print(f'\n\nThe match that was found is {result}!!!')
    else:
        results = literal_eval(two_part_msg[1].split(":")[1][1:])
        return results
        #print(f'\n\nThe matches that were found are\n1. {results[0]}\n2. {results[1]}\n3. {results[2]}!!!')


def on_register():
    username = username_entry.get()
    password = password_entry.get()
    Did_succeed = register(username, password)
    register_window = tk.Toplevel(root)  # Create a new window
    register_window.title("Registration Confirmation")
    if Did_succeed == "Registered":
        # Create label and button in the new window
        label = tk.Label(register_window, text="You are registered!!")
        label.pack(pady=10)

        ok_button = tk.Button(register_window, text="OK", command=root.destroy)
        ok_button.pack(pady=10)
    else:
        # Create label and button in the new window
        label = tk.Label(register_window, text="You can't be registered :(")
        label.pack(pady=10)

        ok_button = tk.Button(register_window, text="OK", command=root.destroy)
        ok_button.pack(pady=10)

        try_again_button = tk.Button(register_window, text="Try Again", command=on_register)
        try_again_button.pack(pady=10)


def on_assign():
    def button_record():
        nonlocal record
        record = True
        button_clicked.set("record")

    def button_use_prerecorded():
        nonlocal record
        record = False
        button_clicked.set("prerecorded")
    record = False
    username = username_entry.get()
    password = password_entry.get()
    client_socket.send(f"ASSIGN {username} {password}".encode('utf-8'))

    response = client_socket.recv(1024).decode('utf-8')
    print(f"Server response: {response}")
    if response == "Connection APPROVED":
        register_window = tk.Toplevel(root)  # Create a new window
        register_window.title("Registration Confirmation")
        button_clicked = tk.StringVar()
        sample_button = tk.Button(register_window, text="Press Here To Record 2 seconds", command=button_record)
        sample_button.pack(pady=10)
        sample_button = tk.Button(register_window, text="Or Press Here To Use Prerecorded Sample", command=button_use_prerecorded)
        sample_button.pack(pady=10)
        # Wait for one of the buttons to be clicked
        register_window.wait_variable(button_clicked)
        if record:
            results = assign(username, password)
        else:
            results = assign(username, password, "MoreWavs/FireToTheRain2.wav")
        if len(results) == 1:
            label = tk.Label(register_window, text=f'The match that was found is {results[0]}!!!', font=("Helvetica", 24))
            label.pack(pady=10)
        else:
            # Create label and button in the new window
            label = tk.Label(register_window, text=f'The matches that were found are\n1. {results[0]}\n2. {results[1]}\n3. {results[2]}!!!')
            label.pack(pady=10)

        great_button = tk.Button(register_window, text="Great", command=root.destroy)
        great_button.pack(pady=10)
    if response == "Connection DENIED":
        client_socket.close()
        root.destroy()

# Create the main window
root = tk.Tk()
root.title("Sign Up")

# Set window size
window_width = 800
window_height = 600

# Get the screen dimension
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Find the center point
center_x = int(screen_width / 2 - window_width / 2)
center_y = int(screen_height / 2 - window_height / 2)

# Set the position of the window to the center of the screen
root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

f1 = tk.Frame(root, padx=5, pady=5)
f1.pack(side=tk.TOP)
f2 = tk.Frame(root, padx=5, pady=5)
f2.pack(side=tk.TOP)
# Create and place labels and entry fields
tk.Label(f1, text="Username").pack(side=tk.LEFT,)
username_entry = tk.Entry(f1)
username_entry.pack(side=tk.LEFT)

tk.Label(f2, text="Password").pack(side=tk.LEFT)
password_entry = tk.Entry(f2, show="*")
password_entry.pack(side=tk.LEFT)


# Create and place the buttons

register_button = tk.Button(root, text="Sign up", command=on_register, pady=10)
register_button.pack(side=tk.TOP)

assign_button = tk.Button(root, text="Sign in", command=on_assign, pady=10)
assign_button.pack(side=tk.TOP)

# Create and place the label in the center
center_row = int((window_height / 2) // 20)  # Calculate the center row based on window height
center_column = 0  # Center column
#tk.Label(root, text="Sign Up", font=("Helvetica", 16)).pack(padx=45, pady=85)

# Run the main event loop
root.mainloop()


# Close the connection
client_socket.close()



