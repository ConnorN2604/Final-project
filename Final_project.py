#Final project
#Jonathan Jipping and Connor Nolan

import sqlite3
import random
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# Function to set up the SQLite database and create necessary tables
def setup_database():
    conn = sqlite3.connect("sports_crime.db")
    cursor = conn.cursor()


    # Create a table to store NFL team data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS NFL_Data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            wins INTEGER,
            losses INTEGER,
            points_scored INTEGER
        )
    ''')


    # Create a table to store crime data related to NFL teams
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Crime_Data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nfl_team_id INTEGER,
            crime_type TEXT,
            date TEXT,
            time TEXT,
            crime_count INTEGER,
            FOREIGN KEY (nfl_team_id) REFERENCES NFL_Data (id)
        )
    ''')
    conn.commit()
    conn.close()


setup_database()