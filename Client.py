import json
import socket
import numpy as np
import pyaudio
import wave
import librosa
from ast import literal_eval
import tkinter as tk
from PIL import Image, ImageTk
from Encryption import Encryption as Encrypt
from tkinter import filedialog, messagebox
import threading

# Define server address and port
#SERVER_HOST = "172.16.8.243"
#SERVER_HOST = "10.0.0.16"
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 2487


class Client:
    def __init__(self):
        self.fill_label = None
        self.bottom_frame = None
        self.top_frame = None
        self.username = None
        self.password = None
        self.selected_file = None
        self.button_clicked = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((SERVER_HOST, SERVER_PORT))
        print("connected to server")
        self.root = None
        self.register_window = None
        self.username_entry = None
        self.password_entry = None
        self.songs = None
        self.distances = None
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
        response = self.Encryption.decrypt()
        print(f"Server response: {response}")
        if response == "Invalid format. Use REGISTER <username> <password>":
            return "Invalid format. Use REGISTER <username> <password>"
        return "Registered" if response.startswith("Registered") or response.startswith(client_name) else "Failed"

    @staticmethod
    def record_audio(filename="Recorded.wav", record_seconds=5, sample_rate=44100, chunk_size=1024, channels=1):
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

            return json.dumps(mfccs_var.tolist())

        except Exception as e:
            # Handle any exceptions that occur during file loading or feature extraction
            print(f"Error loading file {file_path}: {e}")
            return None

    def assign(self, filename="Recorded.wav"):
        sample_mfcc = self.extract_mfcc(filename)
        msg = sample_mfcc.encode('utf-8')
        self.Encryption.send_encrypted_msg(msg)
        msg = self.Encryption.decrypt()
        print(msg)
        three_part_msg = msg.split("\n")
        Is_Dominant = three_part_msg[0].split()[1] != "False"
        if Is_Dominant:
            song = three_part_msg[1].split()[-1]
            distance = three_part_msg[2].split()[-1]
            return [song], [distance]
        else:
            # Split by colon, take the second part, strip ALL whitespace, then eval
            songs = literal_eval(three_part_msg[1].split(":", 1)[1].strip())
            distances = literal_eval(three_part_msg[2].split(":", 1)[1].strip())
            return songs, distances

    @staticmethod
    def combine_funcs(*funcs):
        def combined_func(*args, **kwargs):
            for f in funcs:
                f(*args, **kwargs)
        return combined_func

    def on_register(self):
        self.get_info(False)
        Did_succeed = self.register(self.username, self.password)
        print(f"{Did_succeed =}")
        if Did_succeed == "Registered":
            if self.fill_label:
                self.fill_label.pack_forget()
            register_window = tk.Toplevel(self.root)  # Create a new window
            register_window.title("Registration Confirmation")
            self.center_window(register_window, 150, 110)
            # Create label and button in the new window
            tk.Label(register_window, text="You are registered!!").pack(pady=10)
            tk.Button(register_window, text="OK", command=register_window.destroy).pack(pady=10)
        if Did_succeed.startswith("Invalid"):
            self.fill_label = tk.Label(self.top_frame, text="***Please fill both the username and the password!!***", font=("Helvetica", 14))
            self.fill_label.pack()

    def get_info(self, assign=True):
        self.username = self.username_entry.get()
        self.password = self.password_entry.get()
        if assign:
            self.check_validation()

    def check_validation(self):
        self.Encryption.send_encrypted_msg(f"ASSIGN {self.username} {self.password}".encode('utf-8'))

        response = self.Encryption.decrypt()
        print(f"Server response: {response}")

        if response == "Connection APPROVED":
            self.on_assign()
        elif response == "Connection DENIED":
            self.close_connection()
            self.root.destroy()

    def on_assign(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.button_clicked = tk.StringVar()

        record_button = tk.Button(self.root, text="Press Here To Record 2 seconds", command=self.handle_record,
                                  font=("Helvetica", 14))
        record_button.pack(pady=10)
        prerecord_button = tk.Button(self.root, text="Or Press Here To Use Prerecorded Sample",
                                     command=self.handle_prerecorded, font=("Helvetica", 14))
        prerecord_button.pack(pady=10)

        self.root.wait_variable(self.button_clicked)

    def handle_record(self):
        self.button_clicked.set("record")
        for widget in self.root.winfo_children():
            widget.destroy()
        self.register_window = tk.Toplevel(self.root)
        self.register_window.title("Processing")
        tk.Label(self.register_window, text="Processing (Recording & Server)...", font=("Helvetica", 16)).pack(pady=20)

        threading.Thread(target=self._process_recording_thread, daemon=True).start()

    def _process_recording_thread(self):
        # This runs in parallel, so the UI doesn't freeze
        self.record_audio()

        self.songs, self.distances = self.assign()
        self.root.after(0, self.display_results)

    def handle_prerecorded(self):
        self.selected_file = filedialog.askopenfilename(title="Select a prerecorded audio file",
                                                   filetypes=(("WAV Files", "*.wav"), ("All Files", "*.*")))
        if not self.selected_file:
            messagebox.showerror("Error", "No file selected.")
            return

        self.button_clicked.set("prerecorded")
        self.register_window = tk.Toplevel(self.root)  # Create a new window
        self.center_window(self.register_window)
        self.register_window.title("Processing")
        tk.Label(self.register_window, text="Processing...", font=("Helvetica", 16)).pack(pady=20)

        threading.Thread(target=self._process_file_thread, daemon=True).start()

    def _process_file_thread(self):
        self.songs, self.distances = self.assign(self.selected_file)
        self.root.after(0, self.display_results)

    def display_results(self):
        # Clear all widgets specific to distances_window
        for widget in self.register_window.winfo_children():
            widget.destroy()

        if len(self.distances) == 1:
            # Add new label with distances information
            label = tk.Label(self.register_window,
                             text=f'The match that was found is:\n{self.songs[0]}!!!',
                             font=("Helvetica", 24))
            label.pack(pady=10)
        else:
            label = tk.Label(self.register_window,
                             text=f'The matches that were found are\n1. {self.songs[0]}\n2. {self.songs[1]}\n3. {self.songs[2]}!!!',
                             font=("Helvetica", 12))
            label.pack(pady=10)

        # Create buttons for different actions after displaying results
        tk.Button(self.register_window, text="Find out the distances", command=self.distances_window,
                  font=("Helvetica", 14)).pack(pady=10)
        tk.Button(self.register_window, text="Try different song", command=self.display_initial_options, font=("Helvetica", 14)).pack(
            pady=10)
        tk.Button(self.register_window, text="Exit",
                  command=self.combine_funcs(self.root.destroy, self.close_connection),
                  font=("Helvetica", 14)).pack(pady=10)

    def display_initial_options(self):
        for widget in self.register_window.winfo_children():
            widget.destroy()

        # Display options to record or use prerecorded sample
        self.button_clicked = tk.StringVar()

        record_button = tk.Button(self.register_window, text="Press Here To Record 2 seconds", command=self.handle_record,
                                  font=("Helvetica", 14))
        record_button.pack(pady=10)
        prerecord_button = tk.Button(self.register_window, text="Or Press Here To Use Prerecorded Sample",
                                     command=self.handle_prerecorded, font=("Helvetica", 14))
        prerecord_button.pack(pady=10)

        self.register_window.wait_variable(self.button_clicked)

    def distances_window(self):
        # Clear all widgets specific to distances_window
        for widget in self.register_window.winfo_children():
            widget.destroy()

        if len(self.distances) == 1:
            # Add new label with distances information
            label = tk.Label(self.register_window,
                             text=f'The match that was found is:\n{self.songs[0]}\nThe distance: {self.distances[0]}!!!',
                             font=("Helvetica", 24))
            label.pack(pady=10)
        else:
            label = tk.Label(self.register_window,
                             text=f'The matches that were found are\n1. {self.songs[0]} : {self.distances[0]}\n'
                                  f'2. {self.songs[1]} : {self.distances[1]}\n3. {self.songs[2]}'
                                  f' : {self.distances[2]}!!!', font=("Helvetica", 12))
            label.pack(pady=10)

        # Create frames for buttons
        f1 = tk.Frame(self.register_window, padx=5, pady=5)
        f1.pack(side=tk.TOP)
        f2 = tk.Frame(self.register_window, padx=5, pady=5)
        f2.pack(side=tk.TOP)

        # Load exit image and resize
        image = Image.open("guiimages/exit.png")
        image = image.resize((95, 75), resample=Image.BICUBIC)
        exit_image = ImageTk.PhotoImage(image)

        # Create buttons
        back_to_main_button = tk.Button(f1, text="Try different song",
                                        command=self.display_initial_options,
                                        font=("Helvetica", 14))
        back_to_main_button.pack(pady=10)

        exit_button = tk.Button(f2, text="Exit", image=exit_image,
                                command=self.combine_funcs(self.root.destroy, self.close_connection),
                                font=("Helvetica", 14))
        exit_button.image = exit_image  # Keep a reference to the image to prevent garbage collection
        exit_button.pack(pady=10)

    def main_window(self):
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Yahelizam")

        self.center_window(self.root)

        # Frame to hold username and password
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(pady=10)

        # Username
        username_frame = tk.Frame(self.top_frame)
        username_frame.pack()
        tk.Label(username_frame, text="Username", font=("Helvetica", 20)).pack(side=tk.LEFT)
        self.username_entry = tk.Entry(username_frame, font=("Helvetica", 20))
        self.username_entry.pack(side=tk.LEFT, padx=10, pady=5)

        # Password
        password_frame = tk.Frame(self.top_frame)
        password_frame.pack()
        tk.Label(password_frame, text="Password", font=("Helvetica", 20)).pack(side=tk.LEFT)
        self.password_entry = tk.Entry(password_frame, show="*", font=("Helvetica", 20))
        self.password_entry.pack(side=tk.LEFT, padx=10, pady=5)

        # Adding new label after username and password entries
        self.new_label = tk.Label(self.root, text="***Please fill both the username and the password!!***",
                                  font=("Helvetica", 20))

        # Frame to hold sign up and sign in buttons
        self.middle_frame = tk.Frame(self.root)
        self.middle_frame.pack()

        image = Image.open("guiimages/sign-up.png")
        image = image.resize((150, 105), resample=Image.BICUBIC)
        sign_up_image = ImageTk.PhotoImage(image)

        image = Image.open("guiimages/sign-in.png")
        image = image.resize((150, 105), resample=Image.BICUBIC)
        sign_in_image = ImageTk.PhotoImage(image)

        # Create and place the buttons
        register_button = tk.Button(self.middle_frame, text="Sign up", image=sign_up_image,
                                    command=self.combine_funcs(self.on_register), pady=10)
        register_button.pack(side=tk.LEFT, padx=25, pady=10)

        assign_button = tk.Button(self.middle_frame, text="Sign in", image=sign_in_image,
                                  command=self.combine_funcs(self.get_info, self.root.withdraw), padx=10, pady=10)
        assign_button.pack(side=tk.LEFT, padx=25, pady=10)

        # Frame to hold the exit button
        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.pack(pady=5)

        image = Image.open("guiimages/exit.png")
        image = image.resize((95, 75), resample=Image.BICUBIC)
        exit_image = ImageTk.PhotoImage(image)

        exit_button = tk.Button(self.bottom_frame, text="Exit", image=exit_image,
                                command=self.combine_funcs(self.root.destroy, self.close_connection),
                                font=("Helvetica", 14))
        exit_button.pack(pady=10)

        # Run the main event loop
        self.root.mainloop()
        self.close_connection()

    def center_window(self, root, window_width=500, window_height=395):
        # Set window size
        window_width = window_width
        window_height = window_height

        # Get the screen dimension
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Find the center point
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)

        # Set the position of the window to the center of the screen
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')


def main():
    g = Client()
    g.encryption()
    g.main_window()


if __name__ == "__main__":
    main()