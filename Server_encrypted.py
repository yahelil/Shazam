import socket
import threading
import numpy as np
from scipy.spatial.distance import euclidean
from protocol import Protocol
from Database import *
from Encryption import Encryption
import hashlib

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65433
database = {}


# This function is originally for the client but I added it in the server for tests only
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


def recognize_song(test_mfcc):
    """
    Recognizes a song by comparing the MFCC features of the test audio to the database.

    Args:
        test_mfcc (np.ndarray): MFCC feature vector of the test audio.
        database (dict): A dictionary where keys are song names and values are MFCC feature vectors of known songs.

    Returns:
        tuple: The recognized song or top matches, and a boolean indicating if the match is dominant.
    """
    database = Database.create_database()

    try:
        if not test_mfcc:
            raise ValueError("test_mfcc is empty or None")

        # Convert test_mfcc to a numpy array if it's not already
        test_mfcc = np.fromstring(test_mfcc.strip('[]'), sep=' ')

        # Calculate the Euclidean distance from the test MFCC to each song's MFCC in the database
        distances = [(euclidean(test_mfcc, song_mfcc), song_name) for song_name, song_mfcc in database.items()]

        # Print the calculated distances for debugging purposes
        for distance, song_name in distances:
            print(f"Distance to {song_name}: {distance}")
        # Sort the list by distance in ascending order
        distances.sort()
        prev_name_list = [distances[0][1].split('_')[0]]
        top_3_distances = [distances[0][0]]
        top_3_matches = [distances[0][1].split('_')[0]]
        for distance, name in distances:
            if name.split('_')[0] not in prev_name_list:
                top_3_distances.append(distance)
                top_3_matches.append(name.split('_')[0])
                prev_name_list.append(name.split('_')[0])
        # Determine whether the recognized song is dominant
        #top_2_distances = [distance for distance, _ in distances[:2]]
        Is_Dominant = top_3_distances[0] / top_3_distances[1] < 0.5
        # Extract the top 3 matches
        # top_3_matches = [song_name for _, song_name in distances[:3]]
        # Return the best match if dominant, otherwise return the top 3 matches
        return (top_3_matches[0], top_3_distances[0], Is_Dominant) if Is_Dominant else (top_3_matches[:3], top_3_distances[:3], Is_Dominant)
    except Exception as e:
        # Handle any exceptions that occur during the recognition process
        print(f"Error recognizing song: {e}")
        return None, None, False


class Server:

    def __init__(self):
        self.server_socket = None
        self.prot = None
        self.Encryption = None

    @staticmethod
    def combine_funcs(*funcs):
        def combined_func(*args, **kwargs):
            for f in funcs:
                f(*args, **kwargs)

        return combined_func

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((SERVER_HOST, SERVER_PORT))
        self.server_socket.listen(5)
        print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"Accepted new connection from {client_address}")
                self.prot = Protocol(client_socket)
                client_handler = threading.Thread(target=self.combine_funcs(self.encryption, self.handle_client), args=(client_socket, client_address))
                client_handler.start()
        except KeyboardInterrupt:
            print("Server shutting down.")
        finally:
            self.server_socket.close()

    def encryption(self, client_socket, adress):
        self.Encryption = Encryption(client_socket)
        self.Encryption.create_keys()
        self.Encryption.send_key()
        self.Encryption.receive_public_key()
        self.Encryption.create_box()

    def handle_client(self, client_socket, client_address):
        print(f"New connection: {client_address}")
        try:
            while True:
                message = self.prot.get_msg()[1]
                if not message:
                    break
                message = self.Encryption.decrypt(message)
                self.process_message(message)
        except ConnectionAbortedError:
            print(f"{client_address} disconnected")
        finally:
            print(f"Connection closed: {client_address}")
            client_socket.close()

    def process_message(self, message):
        if message.startswith('REGISTER'):
            self.register_client(message)
        elif message.startswith('ASSIGN'):
            self.assign_client(message)
        else:
            self.calculate_sample(message)

    def register_client(self, message):
        try:
            _, client_name, client_password = message.split()
        except ValueError:
            self.Encryption.send_encrypted_msg("Invalid format. Use REGISTER <username> <password>".encode('utf-8'))
            return
        if not client_name or not client_password:
            self.Encryption.send_encrypted_msg("Username and password cannot be empty".encode('utf-8'))
            return
        clients = Database.get_clients_database()
        registered = False
        for client in clients:
            print(f"{client[1] =}, {client[2] =}")
            if (client_name, hashlib.md5(client_password.encode()).hexdigest()) == (client[1], client[2]):
                self.Encryption.send_encrypted_msg(f"{client_name} already registered".encode('utf-8'))
                registered = True
        if not registered:
            Database.update_clients_database(client_name, client_password)
            self.Encryption.send_encrypted_msg(f"Registered as {client_name}".encode('utf-8'))

    def assign_client(self, message):
        try:
            client_name, client_password = message.split()[1:3]
        except ValueError:
            self.Encryption.send_encrypted_msg("Invalid format. Use ASSIGN <username> <password>".encode('utf-8'))
            return
        clients = Database.get_clients_database()
        for client in clients:
            if (client_name, hashlib.md5(client_password.encode()).hexdigest()) == (client[1], client[2]):
                self.Encryption.send_encrypted_msg("Connection APPROVED".encode('utf-8'))
                return

    def calculate_sample(self, test_mfcc):
        if test_mfcc is not None:
            recognized_song, distances, Is_Dominant = recognize_song(test_mfcc)
            self.Encryption.send_encrypted_msg(f'Is_Dominant: {Is_Dominant}\nThe recognized song is: {recognized_song}\nThe distances are: {distances}'.encode("utf-8"))
        else:
            self.Encryption.send_encrypted_msg("Error processing audio sample".encode("utf-8"))


# A function only for test.
# I only run it when I need to test results quick
def test():
    print("The sampled song is : FireToTheRain_eli1.wav")
    test_mfcc = extract_mfcc('MoreWavs/sample1_fireToTheRain.wav')
    recognized_song = recognize_song(test_mfcc)
    print(f'The recognized song is: {recognized_song}\n')

    print("The sampled song is : FireToTheRain_eli2.wav")
    test_mfcc = extract_mfcc('MoreWavs/sample2_fireToTheRainNormalized.wav')
    recognized_song = recognize_song(test_mfcc)
    print(f'The recognized song is: {recognized_song}\n')

    print("The sampled song is : FireToTheRain_eli3.wav")
    test_mfcc = extract_mfcc('MoreWavs/sample3_fireToTheRain.wav')
    recognized_song = recognize_song(test_mfcc)
    print(f'The recognized song is: {recognized_song}\n')


def main():
    s = Server()
    s.start()


if __name__ == "__main__":
    main()
    # test()
