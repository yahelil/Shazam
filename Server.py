import socket
import threading
import librosa
import numpy as np
from scipy.spatial.distance import euclidean
import mysql.connector

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65433


def get_clints_database():
    # Connect to the MySQL server
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yaheli11",
        database="mydatabase"
    )

    mycursor = mydb.cursor()

    # Select all data from the Clients table
    mycursor.execute("SELECT * FROM Clients")

    # Fetch all rows from the executed query
    result = mycursor.fetchall()

    # Print each row
    return result


def delete_client(username):
    # Connect to the MySQL server
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yaheli11",
        database="mydatabase"
    )

    mycursor = mydb.cursor()

    try:
        # Check if the username exists
        mycursor.execute("SELECT COUNT(*) FROM Clients WHERE username = %s", (username,))
        result = mycursor.fetchone()

        if result[0] > 0:
            # Delete the user with the given username
            sql = "DELETE FROM Clients WHERE username = %s"
            mycursor.execute(sql, (username,))
            print(f"{mycursor.rowcount} record(s) deleted.")
        else:
            print("Username not found. No deletion performed.")

        # Commit the transaction
        mydb.commit()

        # Fetch all data from the Clients table to verify the deletion
        mycursor.execute("SELECT * FROM Clients")
        result = mycursor.fetchall()

        # Print each row to verify the data
        for row in result:
            print(row)

    except mysql.connector.Error as error:
        print("Error:", error)

    finally:
        # Close the cursor and connection
        mycursor.close()
        mydb.close()


def update_clients_database(username, password):
    # Connect to the MySQL server
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yaheli11",
        database="mydatabase"
    )

    mycursor = mydb.cursor()

    try:
        # Check if the username exists
        mycursor.execute("SELECT COUNT(*) FROM Clients WHERE username = %s", (username,))
        result = mycursor.fetchone()

        if result[0] == 0:
            # Insert the new username and password
            sql = "INSERT INTO Clients (username, password) VALUES (%s, %s)"
            val = (username, password)
            mycursor.execute(sql, val)
            print(f"{mycursor.rowcount} record(s) inserted.")
        else:
            print("Username already exists. No insertion performed.")

        # Commit the transaction
        mydb.commit()

        # Fetch all data from the Clients table to verify the update
        mycursor.execute("SELECT * FROM Clients")
        result = mycursor.fetchall()

        # Print each row to verify the data
        for row in result:
            print(row)

    except mysql.connector.Error as error:
        print("Error:", error)

    finally:
        # Close the cursor and connection
        mycursor.close()
        mydb.close()


def create_database():
    # Connect to the MySQL server
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yaheli11",
        database="mydatabase"
    )

    mycursor = mydb.cursor()

    # Fetch all data from the mfcc_songs_db table
    mycursor.execute("SELECT * FROM mfcc_songs_db")
    result = mycursor.fetchall()
    database = {}
    # Print each row
    for row in result:
        database[row[1]] = np.fromstring(row[2].decode("utf-8").strip('[]'), sep=' ')

    # Close the cursor and connection
    mycursor.close()
    mydb.close()
    return database


def update_mfcc_songs_db():
    # Connect to the MySQL server
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yaheli11",
        database="mydatabase"
    )

    mycursor = mydb.cursor()

    # Insert data into the mfcc_songs_db table
    sql = "INSERT INTO mfcc_songs_db (song_name, mfcc_data) VALUES (%s, %s)"
    val = [
        ('PressStart', extract_mfcc(r'MoreWavs/normalized_press_start.wav'))
    ]

    try:
        # Execute the SQL command for each row of data
        for v in val:
            mycursor.execute(sql, v)

        # Commit the transaction
        mydb.commit()

        print(mycursor.rowcount, "record(s) inserted.")

        # Fetch all data from the `mfcc_songs_db` table to verify the insertion
        mycursor.execute("SELECT * FROM mfcc_songs_db")
        result = mycursor.fetchall()

        # Print each row to verify the data
        for row in result:
            print(row)

    except mysql.connector.Error as error:
        print("Error:", error)

    finally:
        # Close the cursor and connection
        mycursor.close()
        mydb.close()


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

        # Concatenate the mean and variance to form the feature vector
        #return np.concatenate((mfccs_mean, mfccs_var))
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
    database = create_database()

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
        # Determine whether the recognized song is dominant
        top_2_distances = [distance for distance, _ in distances[:2]]
        Is_Dominant = top_2_distances[0] / top_2_distances[1] < 0.5
        # Extract the top 3 matches
        top_3_matches = [song_name for _, song_name in distances[:3]]
        # Return the best match if dominant, otherwise return the top 3 matches
        return top_3_matches[0] if Is_Dominant else top_3_matches, Is_Dominant
    except Exception as e:
        # Handle any exceptions that occur during the recognition process
        print(f"Error recognizing song: {e}")
        return None, False


database = {
            #'oasis': extract_mfcc(r'MoreWavs/normalized_livail-oasis-114751.wav'),
            #'see-you-later': extract_mfcc(r'wav-s\see-you-later-203103.wav'),
            #'LetItBe': extract_mfcc(r'MoreWavs\normalized_LetItBe.wav'),
            #'Yesterday': extract_mfcc(r'MoreWavs\normalized_Yesterday.wav'),
            #'HereComesTheSun': extract_mfcc(r'MoreWavs\HereComesTheSun.wav'),
            #'FireToTheRain': extract_mfcc(r'MoreWavs\FireToTheRain.wav'),
            #'PressStart': extract_mfcc(r'MoreWavs\PressStart.wav')
            # Add more songs to the database
        }


class Server:

    def __init__(self):
        self.server_socket = None

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((SERVER_HOST, SERVER_PORT))
        self.server_socket.listen(5)
        print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"Accepted new connection from {client_address}")
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
                self.process_message(message, client_socket)
        except ConnectionResetError:
            print(f"{client_address} disconnected")
        finally:
            print(f"Connection closed: {client_address}")
            client_socket.close()

    def process_message(self, message, client_socket):
        if message.startswith('REGISTER'):
            self.register_client(message, client_socket)
        elif message.startswith('ASSIGN'):
            self.assign_client(message, client_socket)
        else:
            client_socket.send("Unknown command".encode('utf-8'))

    def register_client(self, message, client_socket):
        try:
            _, client_name, client_password = message.split()
        except ValueError:
            client_socket.send("Invalid format. Use REGISTER <username> <password>".encode('utf-8'))
            return
        if not client_name or not client_password:
            client_socket.send("Username and password cannot be empty".encode('utf-8'))
            return
        clients = get_clints_database()
        registered = False
        for client in clients:
            if (client_name, client_password) == (client[1], client[2]):
                client_socket.send(f"{client_name} already registered".encode('utf-8'))
                registered = True
        if not registered:
            update_clients_database(client_name, client_password)
            client_socket.send(f"Registered as {client_name}".encode('utf-8'))

    def assign_client(self, message, client_socket):
        client_name, client_password = message.split()[1:3]
        clients = get_clints_database()
        for client in clients:
            if (client_name, client_password) == (client[1], client[2]):
                client_socket.send("Connection APPROVED".encode('utf-8'))
                self.get_sample(client_socket)
                test_mfcc = extract_mfcc('received_output.wav')
                if test_mfcc is not None:
                    recognized_song, Is_Dominant = recognize_song(test_mfcc)
                    client_socket.send(f'Is_Dominant: {Is_Dominant}\nThe recognized song is: {recognized_song}'.encode("utf-8"))
                else:
                    client_socket.send("Error processing audio sample".encode("utf-8"))
            else:
                client_socket.send("Connection DENIED".encode('utf-8'))

    @staticmethod
    def get_sample(client_socket, output_filename="received_output.wav"):
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
                if not data or data[-4:] == b'stop':
                    break
                f.write(data)
        print(f"File received and saved as {output_filename}")


if __name__ == "__main__":
    #update_mfcc_songs_db()
    #delete_client("Client1")
    #fetch_mfcc_songs_db()
    s = Server()
    s.start()
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

