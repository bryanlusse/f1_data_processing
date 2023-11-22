"""Data ingestor that ingests data from http://ergast.com/mrd/ and stores it in a local database"""

import os
import sqlite3
from typing import Dict, List

import requests

# Correctly import the setup_logger function from the utils module
from f1_data_processing.utils.logger.logger import setup_logger


class DataIngestor:
    """Class that ingests data from an API and stores it in a database"""

    def __init__(self):  # db_file
        self.api_base_url = "http://ergast.com/api/f1/"
        current_directory = os.path.abspath(os.path.dirname(__file__))
        database_directory = os.path.join(current_directory, "..", "database", "database.db")
        self.db_file = database_directory
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

        # Set up a logger by importing the configuration
        self.logger = setup_logger("DataIngestor", "data_ingestor.log")

    def ingest_results(self, season_list: list, race_list: list = None, qualifying: bool = False):
        # Make an API request to fetch data
        if (len(season_list) == 0) or (len(race_list) == 0):
            self.logger.error("The 'race_list' or 'season_list' arguments must not be empty.")

        for season in season_list:
            if race_list:
                for race in race_list:
                    data = self._ingest_race_results(season=season, race=race, qualifying=qualifying)
                    processed_data = self._process_race_results(data=data)
                    self.store_data_in_database(processed_data=processed_data)
            else:
                data = self._ingest_season_results(season=season, qualifying=qualifying)
                processed_data = self._process_season_results(season_data=data)
                self.store_data_in_database(processed_data=processed_data)

    def _ingest_race_results(self, season: int, race: int, qualifying: bool = False) -> dict:
        """
        # TODO Create a docstring for this method and fill it in with the following information:
        # TODO - What does this method do?
        # TODO - What arguments does it take?
        # TODO - What does it return?
        # TODO - What exceptions can it raise?
        """
        if qualifying:
            response = requests.get(f"{self.api_base_url}{season}/{race}/qualifying.json?limit=1000", timeout=5)
            if response.status_code == 200:
                qualifying_data = response.json()  # Assuming the API response is in JSON format
            else:
                raise self.logger.error(f"Failed to fetch data from API. Status code: {response.status_code}")
            return qualifying_data
        else:
            response = requests.get(f"{self.api_base_url}{season}/{race}/results.json?limit=1000", timeout=5)
            if response.status_code == 200:
                race_data = response.json()  # Assuming the API response is in JSON format
            else:
                raise self.logger.error(f"Failed to fetch data from API. Status code: {response.status_code}")
            return race_data

    def _process_race_results(self, data: dict):
        """ """

    def _ingest_season_results(self, season: int, qualifying: bool = False) -> dict:
        """
        # TODO Create a docstring for this method and fill it in with the following information:
        # TODO - What does this method do?
        # TODO - What arguments does it take?
        # TODO - What does it return?
        # TODO - What exceptions can it raise?
        """
        if qualifying:
            response = requests.get(f"{self.api_base_url}{season}/results.json?limit=1000", timeout=5)
            if response.status_code == 200:
                qualifying_data = response.json()
                self.logger.info("Successfully fetched data from API.")
            else:
                raise self.logger.error(f"Failed to fetch data from API. Status code: {response.status_code}")
            return qualifying_data
        else:
            response = requests.get(f"{self.api_base_url}{season}/results.json?limit=1000", timeout=5)
            if response.status_code == 200:
                race_data = response.json()
                self.logger.info("Successfully fetched data from API.")
            else:
                raise self.logger.error(f"Failed to fetch data from API. Status code: {response.status_code}")
            return race_data

    def _process_season_results(self, season_data) -> List[Dict]:
        """ """
        processed_data = []
        races = season_data["MRData"]["RaceTable"]["Races"]
        for race in races:
            race_id = f"{race['season']}_{race['round']}"
            race_data = {
                "race_id": race_id,
                "season": race["season"],
                "round": race["round"],
                "race_name": race["raceName"],
                "race_date": race["date"],
                "race_time": race["time"],
                # Add more race details if needed
            }

            results = race["Results"]
            results_data = []

            for result in results:
                if result.get("FastestLap", "") != "":
                    fastest_lap = result["FastestLap"]["Time"]["time"]
                    fastest_lap_speed = float(result["FastestLap"]["AverageSpeed"]["speed"])
                else:
                    fastest_lap = None
                    fastest_lap_speed = None

                result_id = f"{race_id}_{result['position']}"
                result_entry = {
                    "result_id": result_id,
                    "race_id": race_id,
                    "position": int(result["position"]),
                    "driver_name": f"{result['Driver']['givenName']} {result['Driver']['familyName']}",
                    "constructor_name": result["Constructor"]["name"],
                    "points": int(result["points"]),
                    "grid": int(result["grid"]),
                    "laps": int(result["laps"]),
                    "status": result["status"],
                    "fastest_lap_time": fastest_lap,
                    "fastest_lap_speed": fastest_lap_speed,
                }
                results_data.append(result_entry)

            processed_race = {"race_data": race_data, "results_data": results_data}

            processed_data.append(processed_race)

        return processed_data

    def create_tables(self):
        """Creates tables to store the data"""
        # Create a races table in the database (if it doesn't exist)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS races (
                race_id TEXT PRIMARY KEY,
                season TEXT,
                round INTEGER,
                race_name TEXT,
                race_date TEXT,
                race_time TEXT
            );
        """
        )

        # Create a results table in the database (if it doesn't exist)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                result_id TEXT PRIMARY KEY,
                race_id TEXT,
                position INTEGER,
                points INTEGER,
                driver_name TEXT,
                constructor_name TEXT,
                grid INTEGER,
                laps INTEGER,
                status TEXT,
                fastest_lap_time TEXT,
                fastest_lap_speed FLOAT,
                FOREIGN KEY (race_id) REFERENCES races(race_id)
            );
        """
        )

    def insert_race_data(self, race_data: Dict):
        """Inserts race data into the database"""
        sql = """
            INSERT OR REPLACE INTO races (race_id, season, round, race_name, race_date, race_time)
            VALUES (?, ?, ?, ?, ?, ?);
        """

        self.cursor.execute(
            sql,
            (
                race_data["race_id"],
                race_data["season"],
                race_data["round"],
                race_data["race_name"],
                race_data["race_date"],
                race_data["race_time"],
            ),
        )

        self.conn.commit()

    def insert_results_data(self, results_data: List[Dict]):
        """Inserts results data into the database"""
        sql = """
            INSERT OR REPLACE INTO results (result_id, race_id, position, points, driver_name, constructor_name, grid, laps, status, fastest_lap_time, fastest_lap_speed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        for result in results_data:
            self.cursor.execute(
                sql,
                (
                    result["result_id"],
                    result["race_id"],
                    result["position"],
                    result["points"],
                    result["driver_name"],
                    result["constructor_name"],
                    result["grid"],
                    result["laps"],
                    result["status"],
                    result["fastest_lap_time"],
                    result["fastest_lap_speed"],
                ),
            )

        self.conn.commit()

    def store_data_in_database(self, processed_data):
        """Stores the data in the database"""
        self.create_tables()

        for processed_race in processed_data:
            race_data = processed_race["race_data"]
            results_data = processed_race["results_data"]

            self.insert_race_data(race_data)
            self.insert_results_data(results_data)

        self.cursor.close()
        self.conn.close()


if __name__ == "__main__":
    test = DataIngestor()
    test.ingest_results(season_list=[2023])
    current_directory = os.path.abspath(os.path.dirname(__file__))
    database_directory = os.path.join(current_directory, "..", "database", "database.db")
    conn = sqlite3.connect(database_directory)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM races")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
