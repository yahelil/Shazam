import librosa
import mysql.connector
import numpy as np
import hashlib


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
          md5_password = hashlib.md5(password.encode()).hexdigest()
          val = (username, md5_password)
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
      val = []
      for i in range(0, 360, 5):
        val.append(
          (f'BlindingLights_{i}_{i + 5}', self.extract_mfcc(f'SplitBlindingLights/BlindingLights{i}_{i + 5}.wav')), )

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

    @staticmethod
    def delete_song_mfcc(song_name):
      # Connect to the MySQL server
      mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yaheli11",
        database="mydatabase"
      )

      mycursor = mydb.cursor()

      try:
        # Check if the song name exists
        mycursor.execute("SELECT COUNT(*) FROM mfcc_songs_db WHERE song_name = %s", (song_name,))
        result = mycursor.fetchone()

        if result[0] > 0:
          # Delete the song with the given song name
          sql = "DELETE FROM mfcc_songs_db WHERE song_name = %s"
          mycursor.execute(sql, (song_name,))
          print(f"{mycursor.rowcount} record(s) deleted.")
        else:
          print("Song name not found. No deletion performed.")

        # Commit the transaction
        mydb.commit()

        # Fetch all data from the mfcc_songs_db table to verify the deletion
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

    @staticmethod
    def delete_duplicates():
      # Connect to the MySQL server
      mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yaheli11",
        database="mydatabase"
      )

      mycursor = mydb.cursor()

      try:
        # Find all duplicate song names
        find_duplicates_query = """
                      SELECT song_name, COUNT(*)
                      FROM mfcc_songs_db
                      GROUP BY song_name
                      HAVING COUNT(*) > 1;
                  """
        mycursor.execute(find_duplicates_query)
        duplicates = mycursor.fetchall()

        for song_name, count in duplicates:
          # Keep one record and delete the others
          delete_duplicates_query = """
                          DELETE FROM mfcc_songs_db
                          WHERE song_name = %s
                          LIMIT %s;
                      """
          # Delete (count - 1) records for each duplicate song_name
          mycursor.execute(delete_duplicates_query, (song_name, count - 1))

        # Commit the transaction
        mydb.commit()

        print(f"Deleted {mycursor.rowcount} duplicate record(s).")

        # Fetch all data from the mfcc_songs_db table to verify the deletions
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

    @staticmethod
    def renumber_ids():
      # Connect to the MySQL server
      mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yaheli11",
        database="mydatabase"
      )

      mycursor = mydb.cursor()

      try:
        # Create a temporary table with the same structure but with a new auto-incremented ID column
        mycursor.execute("""
                    CREATE TABLE temp_table LIKE mfcc_songs_db
                """)

        # Insert data from the original table into the temporary table
        mycursor.execute("""
                    INSERT INTO temp_table (song_name, mfcc_data)
                    SELECT song_name, mfcc_data
                    FROM mfcc_songs_db
                """)

        # Drop the original table
        mycursor.execute("DROP TABLE mfcc_songs_db")

        # Rename the temporary table to the original table name
        mycursor.execute("RENAME TABLE temp_table TO mfcc_songs_db")

        print("IDs renumbered successfully.")

        # Commit the transaction
        mydb.commit()

        # Fetch all data from the updated mfcc_songs_db table to verify the changes
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


#Database.delete_client("Elior")
#Database.delete_song_mfcc('FireToTheRain')
#Database.renumber_ids()
# g = Database()
# g.insert_mfcc_songs_db()