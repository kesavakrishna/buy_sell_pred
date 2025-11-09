"""
Day 1: Fetch Fear & Greed Index
Simple script to fetch the current crypto Fear & Greed Index
"""

import requests
import pandas as pd
from datetime import datetime


def fetch_fear_greed_index():
    """
    Fetch the Fear & Greed Index from the free API
    API: https://api.alternative.me/fng/
    """
    url = "https://api.alternative.me/fng/"

    try:
        print("Fetching Fear & Greed Index data...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if 'data' in data and len(data['data']) > 0:
            current_data = data['data'][0]

            value = current_data['value']
            classification = current_data['value_classification']
            timestamp = current_data['timestamp']

            # Convert timestamp to readable date
            date = datetime.fromtimestamp(int(timestamp))

            print("\n" + "="*50)
            print("CRYPTO FEAR & GREED INDEX")
            print("="*50)
            print(f"Date: {date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Value: {value}")
            print(f"Classification: {classification}")
            print("="*50 + "\n")

            # Save to CSV
            df = pd.DataFrame([{
                'date': date,
                'value': value,
                'classification': classification
            }])

            csv_file = 'fear_greed_data.csv'
            df.to_csv(csv_file, index=False)
            print(f"Data saved to {csv_file}")

            return {
                'date': date,
                'value': int(value),
                'classification': classification
            }
        else:
            print("Error: No data received from API")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


if __name__ == "__main__":
    result = fetch_fear_greed_index()

    if result:
        print("\nDay 1 Task Complete!")
        print("Next steps:")
        print("- Review the fear_greed_data.csv file")
        print("- Move on to Day 2 to fetch Bitcoin price data")
