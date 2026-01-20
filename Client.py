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
from AudioUtils import extract_mfcc

# Define server address and port
#SERVER_HOST = "172.16.8.243"
#SERVER_HOST = "10.0.0.16"
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 2487


class Client:
    def __init__(self):
        # sockets
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((SERVER_HOST, SERVER_PORT))
        print("connected to server")

        self.Encryption = None
        self.fill_label = None
        self.username = None
        self.password = None
        self.root = self.register_window = self.username_entry = self.password_entry = None
        self.songs = self.distances = self.selected_file = None
        self.top_frame = None

    def encryption(self):
        self.Encryption = Encrypt(self.client_socket)
        self.Encryption.create_keys()
        self.Encryption.receive_public_key()
        self.Encryption.create_box()
        self.Encryption.send_key()

    def register(self, client_name="Client1", password="1678"):
        self.Encryption.send_encrypted_msg(f"REGISTER {client_name} {password}".encode('utf-8'))

        res = self.Encryption.decrypt()
        print(f"Server response: {res}")
        return "Invalid" if "Invalid" in res else "Registered" if "Registered" in res or u in res else "Failed"

    @staticmethod
    def record_audio(filename="Recorded.wav", sec=5, rate=44100, chunk=1024):
        audio = pyaudio.PyAudio()

        # Open stream
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True, frames_per_buffer=chunk)
        print("Recording...")

        frames = [stream.read(chunk) for _ in range(int(rate / chunk * sec))]
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print("Recording finished")

        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(rate)
            wf.writeframes(audio_data.tobytes())

        print(f"Audio saved to {filename}")

    def assign(self, filename="Recorded.wav"):
        sample_mfcc = extract_mfcc(filename)
        self.Encryption.send_encrypted_msg(sample_mfcc.encode('utf-8'))
        msg = self.Encryption.decrypt()
        print(msg)
        lines = msg.split("\n")
        if lines[0].split()[1] != "False":
            return [lines[1].split()[-1]], [lines[2].split()[-1]]
        return literal_eval(lines[1].split(":", 1)[1].strip()), literal_eval(lines[2].split(":", 1)[1].strip())

    @staticmethod
    def combine_funcs(*funcs):
        def combined_func(*args, **kwargs):
            for f in funcs:
                f(*args, **kwargs)
        return combined_func

    def on_register(self):
        self.get_info(False)
        Did_succeed = self.register(self.username_entry.get(), self.password_entry.get())
        print(f"{Did_succeed =}")
        if Did_succeed == "Registered":
            if self.fill_label:
                self.fill_label.pack_forget()
            register_window = tk.Toplevel(self.root)  # Create a new window
            register_window.title("Registration Confirmation")
            self.center_window(register_window, 150, 110)
            tk.Label(register_window, text="You are registered!!").pack(pady=10)
            tk.Button(register_window, text="OK", command=register_window.destroy).pack(pady=10)
        if Did_succeed.startswith("Invalid"):
            self.fill_label = tk.Label(self.top_frame, text="***Please fill both the username and the password!!***", font=("Helvetica", 14))
            self.fill_label.pack()

    def get_info(self, do_assign=True):
        if do_assign: self.check_validation()

    def check_validation(self):
        self.Encryption.send_encrypted_msg(f"ASSIGN {self.username_entry.get()} {self.password_entry.get()}".encode('utf-8'))
        response = self.Encryption.decrypt()
        print(f"Server response: {response}")
        if response == "Connection APPROVED":
            self.on_assign()
        elif response == "Connection DENIED":
            self.close_connection()
            self.root.destroy()

    def on_assign(self):
        self._clear(self.root)

        button_clicked = tk.StringVar()

        record_button = tk.Button(self.root, text="Press Here To Record", command=self.handle_record,
                                  font=("Helvetica", 14))
        record_button.pack(pady=10)
        prerecord_button = tk.Button(self.root, text="Or Press Here To Use Prerecorded Sample",
                                     command=self.handle_prerecorded, font=("Helvetica", 14))
        prerecord_button.pack(pady=10)

        self.root.wait_variable(button_clicked)

    def handle_record(self):
        self._clear(self.root)
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

        self.register_window = tk.Toplevel(self.root)  # Create a new window
        self.center_window(self.register_window)
        self.register_window.title("Processing")
        tk.Label(self.register_window, text="Processing...", font=("Helvetica", 16)).pack(pady=20)

        threading.Thread(target=self._process_file_thread, daemon=True).start()

    def _process_file_thread(self):
        self.songs, self.distances = self.assign(self.selected_file)
        self.root.after(0, self.display_results)

    def display_results(self):
        self._clear(self.register_window)

        if len(self.distances) == 1:
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
        self._clear(self.register_window)

        button_clicked = tk.StringVar()

        tk.Button(self.register_window, text="Press Here To Record 2 seconds", command=self.handle_record,
                                  font=("Helvetica", 14)).pack(pady=10)
        tk.Button(self.register_window, text="Or Press Here To Use Prerecorded Sample",
                                     command=self.handle_prerecorded, font=("Helvetica", 14)).pack(pady=10)

        self.register_window.wait_variable(button_clicked)

    def distances_window(self):
        self._clear(self.register_window)

        if len(self.distances) == 1:
            tk.Label(self.register_window,
                             text=f'The match that was found is:\n{self.songs[0]}\nThe distance: {self.distances[0]}!!!',
                             font=("Helvetica", 24)).pack(pady=10)
        else:
            tk.Label(self.register_window,
                             text=f'The matches that were found are\n1. {self.songs[0]} : {self.distances[0]}\n'
                                  f'2. {self.songs[1]} : {self.distances[1]}\n3. {self.songs[2]}'
                                  f' : {self.distances[2]}!!!', font=("Helvetica", 12)).pack(pady=10)

        # Create frames for buttons
        f1 = tk.Frame(self.register_window, padx=5, pady=5)
        f1.pack(side=tk.TOP)
        f2 = tk.Frame(self.register_window, padx=5, pady=5)
        f2.pack(side=tk.TOP)

        image = Image.open("guiimages/exit.png")
        image = image.resize((95, 75), resample=Image.BICUBIC)
        exit_image = ImageTk.PhotoImage(image)

        # Create buttons
        back_to_main_button = tk.Button(f1, text="Try different song",
                                        command=self.display_initial_options,
                                        font=("Helvetica", 14))
        back_to_main_button.pack(pady=10)

        exit_button = tk.Button(f2, text="Exit", image=exit_image,command=self.combine_funcs(self.root.destroy, self.close_connection), font=("Helvetica", 14))
        exit_button.image = exit_image
        exit_button.pack(pady=10)

    def main_window(self):
        self.root = tk.Tk()
        self.root.title("Yahelizam")

        self.center_window(self.root)

        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(pady=10)

        for tx, show in [("Username", None), ("Password", "*")]:
            f = tk.Frame(self.top_frame)
            f.pack()
            tk.Label(f, text=tx, font=("Helvetica", 20)).pack(side=tk.LEFT)
            e = tk.Entry(f, show=show, font=("Helvetica", 20))
            e.pack(side=tk.LEFT, padx=10, pady=5)
            if show:
                self.password_entry = e
            else:
                self.username_entry = e

        tk.Label(self.root, text="***Please fill both the username and the password!!***", font=("Helvetica", 20))

        middle_frame = tk.Frame(self.root)
        middle_frame.pack()

        imgs = {k: ImageTk.PhotoImage(Image.open(f"guiimages/{k}.png").resize((150, 105))) for k in
                ["sign-up", "sign-in"]}
        tk.Button(middle_frame, text="Sign up", image=imgs["sign-up"], command=self.on_register(), pady=10).pack(side=tk.LEFT, padx=25,pady=10)
        tk.Button(middle_frame, text="Sign in", image=imgs["sign-in"], command=self.combine_funcs(self.get_info, self.root.withdraw),padx=10, pady=10).pack(side=tk.LEFT, padx=25, pady=10)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=5)

        image = Image.open("guiimages/exit.png")
        image = image.resize((95, 75), resample=Image.BICUBIC)
        exit_image = ImageTk.PhotoImage(image)

        exit_button = tk.Button(bottom_frame, text="Exit", image=exit_image,
                                command=self.combine_funcs(self.root.destroy, self.close_connection),
                                font=("Helvetica", 14))
        exit_button.pack(pady=10)

        self.root.mainloop()
        self.close_connection()

    def center_window(self, win, w=500, h=400):
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        win.geometry(f'{w}x{h}+{x}+{y}')

    def close_connection(self):
        self.client_socket.close()

    def _clear(self, win):
        [w.destroy() for w in win.winfo_children()]

if __name__ == "__main__":
    g = Client()
    g.encryption()
    g.main_window()