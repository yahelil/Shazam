import librosa
import mysql.connector
import numpy as np


class Database:
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

    @staticmethod
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

    @staticmethod
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


    @staticmethod
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

    @staticmethod
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


    def insert_mfcc_songs_db(self):
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
        ('FireToTheRain_eli', self.extract_mfcc(r'DataBaseSongs/sample2_fireToTheRainNormalized.wav')),
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