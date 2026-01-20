from tkinter import filedialog
from split_wav import split_wav
import mysql.connector
import numpy as np
import json
from AudioUtils import extract_mfcc


class Database:
    DB_CONFIG = {
      "host": "localhost",
      "user": "root",
      "password": "yaheli11",
      "database": "mydatabase"
    }

    @staticmethod
    def _get_connection():
      return mysql.connector.connect(**Database.DB_CONFIG)

    @staticmethod
    def get_clients_database():
      with Database._get_connection() as mydb:
        with mydb.cursor() as cursor:
          cursor.execute("SELECT * FROM Clients")
          return cursor.fetchall()

    @staticmethod
    def delete_client(username):
      with Database._get_connection() as mydb:
        with mydb.cursor() as cursor:
          cursor.execute("SELECT COUNT(*) FROM Clients WHERE username = %s", (username,))
          if cursor.fetchone()[0] > 0:
            cursor.execute("DELETE FROM Clients WHERE username = %s", (username,))
            print(f"{cursor.rowcount} record(s) deleted.")
          else:
            print("Username not found.")
          mydb.commit()

    def update_clients_database(username, password):
      import hashlib

      with Database._get_connection() as mydb:
        with mydb.cursor() as cursor:
          cursor.execute("SELECT COUNT(*) FROM Clients WHERE username = %s", (username,))
          if cursor.fetchone()[0] == 0:
            md5_pass = hashlib.md5(password.encode()).hexdigest()
            cursor.execute("INSERT INTO Clients (username, password) VALUES (%s, %s)",(username, md5_pass))
            print(f"{cursor.rowcount} record(s) inserted.")
          else:
            print("Username already exists.")
          mydb.commit()

    @staticmethod
    def create_database():
      database = {}
      with Database._get_connection() as mydb:
        with mydb.cursor() as cursor:
          cursor.execute("SELECT * FROM mfcc_songs_db")
          results = cursor.fetchall()
          for row in results:
            # row[1] is song_name, row[2] is data
            database[row[1]] = np.array(json.loads(row[2]))
      return database

    def add_database_song(self):
      selected_file = filedialog.askopenfilename(
        title="Select a prerecorded audio file",
        filetypes=(("WAV Files", "*.wav"), ("All Files", "*.*"))
      )
      if not selected_file:
        return
      splits = split_wav(selected_file, "database")

      with Database._get_connection() as mydb:
        with mydb.cursor() as cursor:
          sql = "INSERT INTO mfcc_songs_db (song_name, mfcc_data) VALUES (%s, %s)"
          cursor.executemany(sql, splits)
          mydb.commit()
          print(f"{cursor.rowcount} record(s) inserted.")

    def insert_mfcc_songs_db(self):
      val = []
      for i in range(0, 300, 5):
        filename = f'SplitSpaceSong/Space{i}_{i + 5}.wav'
        song_name = f'SpaceSong_{i}_{i + 5}'
        mfcc_data = extract_mfcc(filename)

        if mfcc_data:
          val.append((song_name, mfcc_data))

      if not val:
        print("No valid MFCC data found to insert.")
        return

      with Database._get_connection() as mydb:
        with mydb.cursor() as cursor:
          sql = "INSERT INTO mfcc_songs_db (song_name, mfcc_data) VALUES (%s, %s)"
          cursor.executemany(sql, val)
          mydb.commit()
          print(f"{cursor.rowcount} record(s) inserted.")

    @staticmethod
    def delete_song_mfcc(song_name):
      with Database._get_connection() as mydb:
        with mydb.cursor() as cursor:
          cursor.execute("SELECT COUNT(*) FROM mfcc_songs_db WHERE song_name = %s", (song_name,))
          if cursor.fetchone()[0] > 0:
            cursor.execute("DELETE FROM mfcc_songs_db WHERE song_name = %s", (song_name,))
            print(f"{cursor.rowcount} record(s) deleted.")
          else:
            print("Song name not found.")
          mydb.commit()

    @staticmethod
    def delete_duplicates():
      with Database._get_connection() as mydb:
        with mydb.cursor() as cursor:
          cursor.execute("""SELECT song_name, COUNT(*) FROM mfcc_songs_db GROUP BY song_name HAVING COUNT(*) > 1""")
          duplicates = cursor.fetchall()
          deleted_total = 0
          for song_name, count in duplicates:
            limit = count - 1
            cursor.execute("DELETE FROM mfcc_songs_db WHERE song_name = %s LIMIT %s",(song_name, limit))
            deleted_total += cursor.rowcount

          mydb.commit()
          print(f"Deleted {deleted_total} duplicate record(s).")

    @staticmethod
    def renumber_ids():
      with Database._get_connection() as mydb:
        with mydb.cursor() as cursor:
          try:
            cursor.execute("CREATE TABLE temp_table LIKE mfcc_songs_db")

            cursor.execute("""INSERT INTO temp_table (song_name, mfcc_data) SELECT song_name, mfcc_data FROM mfcc_songs_db""")
            cursor.execute("DROP TABLE mfcc_songs_db")
            cursor.execute("RENAME TABLE temp_table TO mfcc_songs_db")
            mydb.commit()
            print("IDs renumbered successfully.")
          except mysql.connector.Error as err:
            print(f"Error renumbering IDs: {err}")
            mydb.rollback()

if __name__ == "__main__":
    db = Database()
    print("Please select Song")
    db.add_database_song()