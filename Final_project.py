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


    # Create NFL_Data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS NFL_Data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            wins INTEGER,
            losses INTEGER,
            points_scored INTEGER
        )
    ''')


    # Create Crime_Data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Crime_Data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nfl_team_id INTEGER,
            crime_type TEXT,
            date TEXT,
            crime_count INTEGER,
            FOREIGN KEY (nfl_team_id) REFERENCES NFL_Data (id)
        )
    ''')


    # Verify table creation
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables created:", tables)  # Debugging output


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
def fetch_and_store_crime_data():
    conn = sqlite3.connect("sports_crime.db")
    cursor = conn.cursor()


    # API details for fetching crime data
    api_key = "iiHnOKfno2Mgkt5AynpvPpUQTEyxE77jo1RU8PIv"
    url = "https://api.usa.gov/crime/fbi/cde/arrest/national/all"
    params = {
        "type": "counts",
        "from": "01-2021",
        "to": "12-2023",
        "API_KEY": api_key
    }
    headers = {"accept": "application/json"}


    crime_categories = ["Drug-Related", "Violent Crime", "Theft"]  # Specific crime categories


    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses
        crime_data = response.json()


        # Extract and process crime data
        actuals = crime_data.get("actuals", {}).get("United States Arrests", {})
        row_count = 0
        for date, count in list(actuals.items())[:25]:  # Limit to 25 items
            try:
                # Parse and validate the date format
                crime_date = pd.to_datetime(date, format="%m-%Y", errors="coerce")
                if pd.isna(crime_date):
                    print(f"Skipping invalid date: {date}")
                    continue
                crime_date = crime_date.strftime("%Y-%m-%d")
            except ValueError:
                print(f"Skipping invalid date: {date}")
                continue


            nfl_team_id = random.randint(1, 25)  # Randomly map crime data to an NFL team
            crime_type = random.choice(crime_categories)  # Assign a random crime type


            # Insert crime data into the database, including crime count
            cursor.execute('''
                INSERT INTO Crime_Data (nfl_team_id, crime_type, date, crime_count)
                VALUES (?, ?, ?, ?)
            ''', (nfl_team_id, crime_type, crime_date, count))
            row_count += 1
        print(f"Inserted {row_count} rows of crime data.")


    except requests.exceptions.RequestException as e:
        print(f"Error: Request failed - {e}")
    except ValueError as e:
        print(f"Error: JSON parsing failed - {e}")
    finally:
        conn.commit()
        conn.close()

# Function to calculate and write summary statistics to a text file
def calculate_and_write_summary():
    conn = sqlite3.connect("sports_crime.db")
    cursor = conn.cursor()


    # Query to join NFL data with crime data and calculate total crime counts
    cursor.execute('''
        SELECT NFL_Data.team_name, NFL_Data.wins, NFL_Data.losses, SUM(Crime_Data.crime_count) AS total_crime
        FROM NFL_Data
        JOIN Crime_Data ON NFL_Data.id = Crime_Data.nfl_team_id
        GROUP BY NFL_Data.team_name, NFL_Data.wins, NFL_Data.losses
    ''')


    results = cursor.fetchall()
    conn.close()


    # Determine column widths for formatting
    col_widths = {
        "Team": max(len("Team"), *(len(row[0]) for row in results)),
        "Wins": max(len("Wins"), *(len(str(row[1])) for row in results)),
        "Losses": max(len("Losses"), *(len(str(row[2])) for row in results)),
        "Total Crime": max(len("Total Crime"), *(len(str(row[3])) for row in results))
    }


    # Write the formatted table to a text file
    with open("crime_summary.txt", "w") as file:
        # Header row
        header = f"| {'Team':<{col_widths['Team']}} | {'Wins':<{col_widths['Wins']}} | {'Losses':<{col_widths['Losses']}} | {'Total Crime':<{col_widths['Total Crime']}} |"
        separator = "+" + "+".join("-" * (col_widths[col] + 2) for col in col_widths) + "+"
        file.write(separator + "\n")
        file.write(header + "\n")
        file.write(separator + "\n")

        # Data rows
        for row in results:
            file.write(f"| {row[0]:<{col_widths['Team']}} | {row[1]:<{col_widths['Wins']}} | {row[2]:<{col_widths['Losses']}} | {row[3]:<{col_widths['Total Crime']}} |\n")


        # Final separator
        file.write(separator + "\n")


# Function to plot the total number of crimes by NFL team
def plot_crime_counts():
    conn = sqlite3.connect("sports_crime.db")
    cursor = conn.cursor()

    # Query to fetch summed crime counts per team
    cursor.execute('''
        SELECT NFL_Data.team_name, SUM(Crime_Data.crime_count) AS total_crime
        FROM NFL_Data
        JOIN Crime_Data ON NFL_Data.id = Crime_Data.nfl_team_id
        GROUP BY NFL_Data.team_name
    ''')
    data = cursor.fetchall()
    conn.close()

    # Create a bar chart
    df = pd.DataFrame(data, columns=["Team Name", "Total Crime"])
    plt.figure(figsize=(12, 6))
    sns.barplot(x="Team Name", y="Total Crime", data=df)
    plt.title("Total Crimes Per NFL Team")
    plt.xticks(rotation=45)
    plt.show()

def plot_top10_crime_distribution_by_team():
    conn = sqlite3.connect("sports_crime.db")
    cursor = conn.cursor()


    cursor.execute('''
        SELECT NFL_Data.team_name, SUM(Crime_Data.crime_count) AS total_crime
        FROM NFL_Data
        JOIN Crime_Data ON NFL_Data.id = Crime_Data.nfl_team_id
        GROUP BY NFL_Data.team_name
        ORDER BY total_crime DESC
        LIMIT 10
    ''')
    data = cursor.fetchall()
    conn.close()


    df = pd.DataFrame(data, columns=["Team Name", "Total Crime"])
    plt.figure(figsize=(10, 10))
    plt.pie(
        df["Total Crime"],
        labels=df["Team Name"],
        autopct='%1.1f%%',
        startangle=140,
        textprops={'fontsize': 9}
    )
    plt.title("Top 10 Teams by Crime Distribution")
    plt.show()

# Function to plot team performance vs. crime count
def plot_team_performance_vs_crimes():
    conn = sqlite3.connect("sports_crime.db")
    cursor = conn.cursor()

    # Query to fetch wins and summed crime counts per team
    cursor.execute('''
        SELECT NFL_Data.team_name, NFL_Data.wins, SUM(Crime_Data.crime_count) AS total_crime
        FROM NFL_Data
        JOIN Crime_Data ON NFL_Data.id = Crime_Data.nfl_team_id
        GROUP BY NFL_Data.team_name
    ''')
    data = cursor.fetchall()
    conn.close()

    # Create a scatter plot
    df = pd.DataFrame(data, columns=["Team Name", "Wins", "Total Crime"])
    plt.figure(figsize=(12, 8))  # Increase figure size for better spacing
    scatter = sns.scatterplot(
        x="Wins",
        y="Total Crime",
        data=df,
        hue="Team Name",
        palette="viridis",
        s=100
    )

    # Adjust legend placement and text
    scatter.legend(
        bbox_to_anchor=(1.05, 1),  # Position the legend to the right of the plot
        loc='upper left',
        title="Team Names",  # Add a legend title
        borderaxespad=0,
        fontsize=9  # Adjust font size for readability
    )

    plt.title("Team Performance vs. Total Crime")
    plt.xlabel("Wins")
    plt.ylabel("Total Crime")
    plt.tight_layout()  # Ensure everything fits without overlapping
    plt.show()


# Function to plot the distribution of crime counts by team losses
def plot_crime_distribution_by_losses():
    conn = sqlite3.connect("sports_crime.db")
    cursor = conn.cursor()




    # Query to fetch losses and summed crime counts per team
    cursor.execute('''
        SELECT NFL_Data.losses, SUM(Crime_Data.crime_count) AS total_crime
        FROM NFL_Data
        JOIN Crime_Data ON NFL_Data.id = Crime_Data.nfl_team_id
        GROUP BY NFL_Data.losses
    ''')
    data = cursor.fetchall()
    conn.close()


    # Create a histogram
    df = pd.DataFrame(data, columns=["Losses", "Total Crime"])
    plt.figure(figsize=(10, 6))
    sns.histplot(df, x="Losses", weights="Total Crime", bins=10, kde=False, color="purple")
    plt.title("Distribution of Crime Counts by Team Losses")
    plt.xlabel("Number of Losses")
    plt.ylabel("Total Crime")
    plt.show()


# Main function to run all processes
def main():
    # Gather data
    fetch_and_store_nfl_data()
    fetch_and_store_crime_data()

    # Process data
    calculate_and_write_summary()

    # Visualize data
    plot_crime_counts()
    plot_top10_crime_distribution_by_team()
    plot_team_performance_vs_crimes()
    plot_crime_distribution_by_losses()

if __name__ == "__main__":
    main()
