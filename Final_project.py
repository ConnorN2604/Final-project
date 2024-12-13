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

# Function to fetch and store NFL data from an external API
def fetch_and_store_nfl_data():
    conn = sqlite3.connect("sports_crime.db")
    cursor = conn.cursor()


    # API details for fetching NFL data
    api_key = "f105b43470724d57820780e9a7a809e7"
    url = "https://api.sportsdata.io/v3/nfl/scores/json/Standings/2023"
    headers = {"Ocp-Apim-Subscription-Key": api_key}


    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        nfl_data = response.json()
        row_count = 0
        for team in nfl_data[:25]:  # Limit to 25 items to comply with project requirements
            cursor.execute('''
                INSERT INTO NFL_Data (team_name, wins, losses, points_scored)
                VALUES (?, ?, ?, ?)
            ''', (
                team["Team"],
                team["Wins"],
                team["Losses"],
                team.get("PointsScored", 0)  # Default to 0 if points scored is not available
            ))
            row_count += 1
        print(f"Inserted {row_count} rows of NFL data.")
    else:
        print(f"Failed to fetch NFL data: {response.status_code}")


    conn.commit()
    conn.close()


# Function to fetch and store crime data from an external API
