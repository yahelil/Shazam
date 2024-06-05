import socket
import threading
import librosa
import numpy as np
from scipy.spatial.distance import euclidean

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432
clients = [("Client1", "1678")]


def extract_mfcc(file_path, n_mfcc=13):
    y, sr = librosa.load(file_path, sr=None)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    mfccs_mean = np.mean(mfccs[1:].T, axis=0)
    mfccs_var = np.var(mfccs[1:].T, axis=0)
    return np.concatenate((mfccs_mean, mfccs_var))
    #return mfcc_mean
    #return mfcc_var


def recognize_song(test_mfcc, database):
    min_distance = float('inf')
    recognized_song = None

    for song_name, song_mfcc in database.items():
        distance = euclidean(test_mfcc, song_mfcc)
        if distance < min_distance:
            min_distance = distance
            recognized_song = song_name

    return recognized_song


database = {
            'oasis': extract_mfcc(r'wav-s\livail-oasis-114751.wav'),
            'see-you-later': extract_mfcc(r'wav-s\see-you-later-203103.wav'),
            'LetItBe': extract_mfcc(r'MoreWavs\LetItBe.wav'),
            'Yesterday': extract_mfcc(r'MoreWavs\Yesterday.wav'),
            'HereComesTheSun': extract_mfcc(r'MoreWavs\HereComesTheSun.wav'),
            'FireToTheRain': extract_mfcc(r'MoreWavs\FireToTheRain.wav'),
            'PressStart': extract_mfcc(r'MoreWavs\PressStart.wav')
            # Add more songs to the database
        }


class Server:

    def start(self):
        # Set up server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((SERVER_HOST, SERVER_PORT))
        self.server_socket.listen(5)
        print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

        # Main loop to accept and handle client connections
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                client_handler.start()
        except KeyboardInterrupt:
            print("Server shutting down.")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, client_address):
        print(f"New connection: {client_address}")
        try:
            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                print(f"Received from {client_address}: {message}")
                if message.startswith('REGISTER'):
                    client_name = message.split()[1]
                    client_password = message.split()[2]
                    clients.append((client_name, client_password))
                    client_socket.send(f"Registered as {client_name}".encode('utf-8'))
                elif message.startswith('ASSIGN'):
                    client_name = message.split()[1]
                    client_password = message.split()[2]
                    if (client_name, client_password) in clients:
                        client_socket.send("Connection APPROVED".encode('utf-8'))
                        self.get_sample(client_socket)
                        print("The sampled song is : received_output.wav")
                        test_mfcc = extract_mfcc('received_output.wav')
                        recognized_song = recognize_song(test_mfcc, database)
                        print(f'The recognized song is: {recognized_song}\n')
                    else:
                        client_socket.send("Connection DENIED".encode('utf-8'))
                else:
                    client_socket.send("Unknown command".encode('utf-8'))
        finally:
            print(f"Connection closed: {client_address}")
            client_socket.close()
        print(clients)
        quit()

    def get_sample(self, client_socket, output_filename="received_output.wav"):
        """
        Receives a .wav file from the client over the given socket and saves it.

        Args:
            client_socket (socket): The socket connected to the client.
            output_filename (str): The name of the file to save the received data.

        Returns:
            None
        """
        with open(output_filename, 'wb') as f:
            print("Receiving file...")
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                f.write(data)
        print(f"File received and saved as {output_filename}")



'''

# Example usage
database = {
    'song1': extract_mfcc(r'wav-s\livail-oasis-114751.wav'),
    'song2': extract_mfcc(r'wav-s\see-you-later-203103.wav'),
    'song3': extract_mfcc(r'MoreWavs\LetItBe.wav'),
    'song4': extract_mfcc(r'MoreWavs\Yesterday.wav'),
    'song5': extract_mfcc(r'MoreWavs\HereComesTheSun.wav'),
    'song6': extract_mfcc(r'MoreWavs\FireToTheRain.wav'),
    'song7': extract_mfcc(r'MoreWavs\PressStart.wav')
    # Add more songs to the database
}
print("The sampled song is : livail_audacity_5_sec.wav")
test_mfcc = extract_mfcc('sampled-wav-s/livail_audacity_5_sec.wav')
recognized_song = recognize_song(test_mfcc, database)
print(f'The recognized song is: {recognized_song}\n')

sample_name_list = ["LetItBe2", "Yesterday2", "HereComesTheSun2", "FireToTheRain2"]
for sample_name in sample_name_list:
    print(f"The sampled song is : {sample_name}")
    test_mfcc = extract_mfcc(f'MoreWavs/{sample_name}.wav')
    recognized_song = recognize_song(test_mfcc, database)
    print(f'The recognized song is: {recognized_song}\n')
'''
# print("The sampled song is : Yesterday2.wav")
# test_mfcc = extract_mfcc('MoreWavs/Yesterday2.wav')
# recognized_song = recognize_song(test_mfcc, database)
# print(f'The recognized song is: {recognized_song}')
#
# print("The sampled song is : HereComesTheSun2.wav")
# test_mfcc = extract_mfcc('MoreWavs/HereComesTheSun2.wav')
# recognized_song = recognize_song(test_mfcc, database)
# print(f'The recognized song is: {recognized_song}')
#
# print("The sampled song is : FireToTheRain2.wav")
# test_mfcc = extract_mfcc('MoreWavs/FireToTheRain2.wav')
# recognized_song = recognize_song(test_mfcc, database)
# print(f'The recognized song is: {recognized_song}')

if __name__ == "__main__":
    s = Server()
    s.start()