import socket
import sys
import numpy as np
import pyaudio
import wave
import librosa
from ast import literal_eval
import tkinter as tk
from PIL import Image, ImageTk
from protocol import Protocol
from Encryption import Encryption as Encrypt
from nacl.public import PublicKey


# Define server address and port
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65433


class Client:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((SERVER_HOST, SERVER_PORT))
        self.prot = Protocol(self.client_socket)
        self.root = None
        self.username_entry = None
        self.password_entry = None
        self.Encryption = None

    def close_connection(self):
        self.client_socket.close()

    def encryption(self):
        self.Encryption = Encrypt(self.client_socket)
        self.Encryption.create_keys()
        # Receive the server's public key
        self.Encryption.receive_public_key()
        self.Encryption.create_box()
        # Send the client's public key to the server
        self.Encryption.send_key()

    def register(self, client_name="Client1", password="1678"):
        # Register with the server
        self.Encryption.send_encrypted_msg(f"REGISTER {client_name} {password}".encode('utf-8'))

        # Receive server response
        response = self.Encryption.decrypt(self.prot.get_msg()[1])
        print(f"Server response: {response}")
        if response == "Invalid format. Use REGISTER <username> <password>":
            return "Invalid format. Use REGISTER <username> <password>"
        self.close_connection()
        return "Registered" if response.startswith("Registered") or response.startswith(client_name) else "Failed"

    @staticmethod
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

        # Convert recorded data to numpy array
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)

        # Normalize audio data
        max_val = np.max(np.abs(audio_data))
        normalized_data = (audio_data / max_val) * 32767
        normalized_data = normalized_data.astype(np.int16)

        # Convert normalized numpy array back to bytes
        normalized_frames = normalized_data.tobytes()

        # Save the recorded data as a WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(normalized_frames)

        print(f"Audio saved to {filename}")


    @staticmethod
    def extract_mfcc(file_path, n_mfcc=13):
        """
        Extracts MFCC features from an audio file.

        Args:
            file_path (str): Path to the audio file.
            n_mfcc (int): Number of MFCC coefficients to extract.

        Returns:
            np.ndarray: Concatenated mean and variance of the MFCC features, or None if an error occurs.
        """
        try:
            # Load the audio file
            y, sr = librosa.load(file_path, sr=None)

            # Extract MFCC features from the audio
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)

            # Calculate the mean of the MFCC features (excluding the first coefficient)
            mfccs_mean = np.mean(mfccs.T, axis=0)

            # Calculate the variance of the MFCC features (excluding the first coefficient)
            mfccs_var = np.var(mfccs.T, axis=0)

            return str(mfccs_var)

        except Exception as e:
            # Handle any exceptions that occur during file loading or feature extraction
            print(f"Error loading file {file_path}: {e}")
            return None

    def assign(self, filename="output.wav"):
        sample_mfcc = self.extract_mfcc(filename)
        msg = sample_mfcc.encode('utf-8')
        msg = self.prot.create_msg(msg)
        self.client_socket.send(msg)
        msg = self.prot.get_msg()[1].decode('utf-8')
        print(msg)
        two_part_msg = msg.split("\n")
        Is_Dominant = two_part_msg[0].split()[1] != "False"
        if Is_Dominant:
            result = two_part_msg[1].split()[-1]
            return [result]
        else:
            results = literal_eval(two_part_msg[1].split(":")[1][1:])
            return results

    @staticmethod
    def combine_funcs(*funcs):
        def combined_func(*args, **kwargs):
            for f in funcs:
                f(*args, **kwargs)
        return combined_func

    def on_register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        Did_succeed = self.register(username, password)
        register_window = tk.Toplevel(self.root)  # Create a new window
        register_window.title("Registration Confirmation")
        if Did_succeed == "Registered":
            # Create label and button in the new window
            tk.Label(register_window, text="You are registered!!").pack(pady=10)
            tk.Button(register_window, text="OK", command=self.root.destroy).pack(pady=10)
        else:
            # Create label and button in the new window
            tk.Label(register_window, text="You can't be registered :(").pack(pady=10)

            tk.Button(register_window, text="OK", command=self.combine_funcs(self.close_connection, self.root.destroy)).pack(pady=10)
            tk.Button(register_window, text="Try Again", command=self.combine_funcs(self.root.destroy, self.main_window)).pack(pady=10)

    def on_assign(self):
        def button_record():
            nonlocal record
            record = True
            button_clicked.set("record")

        def button_use_prerecorded():
            nonlocal record
            record = False
            button_clicked.set("prerecorded")
        record = False
        username = self.username_entry.get()
        password = self.password_entry.get()
        msg = f"ASSIGN {username} {password}".encode('utf-8')
        msg = self.prot.create_msg(msg)
        self.client_socket.send(msg)

        response = self.client_socket.recv(1024).decode('utf-8')
        print(f"Server response: {response}")
        if response == "Connection APPROVED":
            register_window = tk.Toplevel(self.root)  # Create a new window
            register_window.title("Registration Confirmation")
            button_clicked = tk.StringVar()
            record_button = tk.Button(register_window, text="Press Here To Record 2 seconds", command=button_record)
            record_button.pack(pady=10)
            prerecord_button = tk.Button(register_window, text="Or Press Here To Use Prerecorded Sample", command=button_use_prerecorded)
            prerecord_button.pack(pady=10)
            # Wait for one of the buttons to be clicked
            register_window.wait_variable(button_clicked)
            if record:
                self.record_audio()
                results = self.assign()
            else:
                results = self.assign("MoreWavs/SAMinorChord.wav")
            if len(results) == 1:
                label = tk.Label(register_window, text=f'The match that was found is {results[0]}!!!', font=("Helvetica", 24))
                label.pack(pady=10)
            else:
                # Create label and button in the new window
                label = tk.Label(register_window, text=f'The matches that were found are\n1. {results[0]}\n2. {results[1]}\n3. {results[2]}!!!')
                label.pack(pady=10)
            record_button.destroy()
            prerecord_button.destroy()
            tk.Button(register_window, text="Great", command=self.combine_funcs(register_window.destroy, sys.exit)).pack(pady=10)
        if response == "Connection DENIED":
            self.close_connection()
            self.root.destroy()

    def main_window(self):
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Yahelizam")

        # Set window size
        window_width = 500
        window_height = 270

        # Get the screen dimension
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Find the center point
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)

        # Set the position of the window to the center of the screen
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        f1 = tk.Frame(self.root, padx=5, pady=5)
        f1.pack(side=tk.TOP)
        f2 = tk.Frame(self.root, padx=5, pady=5)
        f2.pack(side=tk.TOP)
        f3 = tk.Frame(self.root, padx=5, pady=5)
        f3.pack(side=tk.TOP)
        # Create and place labels and entry fields
        tk.Label(f1, text="Username", font=("Helvetica", 20)).pack(side=tk.LEFT,)
        self.username_entry = tk.Entry(f1, font=("Helvetica", 20))
        self.username_entry.pack(side=tk.LEFT)

        tk.Label(f2, text="Password", font=("Helvetica", 20)).pack(side=tk.LEFT)
        self.password_entry = tk.Entry(f2, show="*", font=("Helvetica", 20))
        self.password_entry.pack(side=tk.LEFT)

        image = Image.open("guiimages/sign-up.png")
        image = image.resize((150,100), resample=Image.BICUBIC)
        sign_up_image = ImageTk.PhotoImage(image)
        image = Image.open("guiimages/sign-in.png")
        image = image.resize((150,100), resample=Image.BICUBIC)
        sign_in_image = ImageTk.PhotoImage(image)

        # Create and place the buttons

        register_button = tk.Button(f3, text="Sign up", image=sign_up_image, command=self.combine_funcs(self.on_register, self.root.withdraw), pady=10)
        register_button.pack(side=tk.LEFT, padx=25, pady=20)

        assign_button = tk.Button(f3, text="Sign in", image=sign_in_image, command=self.combine_funcs(self.root.withdraw, self.on_assign), padx=10, pady=10)
        assign_button.pack(side=tk.LEFT, padx=25,pady=20)

        # Create and place the label in the center
        center_row = int((window_height / 2) // 20)  # Calculate the center row based on window height
        center_column = 0  # Center column

        # Run the main event loop
        self.root.mainloop()

        self.close_connection()


def main():
    g = Client()
    g.encryption()
    g.main_window()


if __name__ == "__main__":
    main()

