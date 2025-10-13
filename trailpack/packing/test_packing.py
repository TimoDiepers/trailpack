
import pandas as pd

# Create minimal working sample data 
# as a list of dictionaries
data = [
    {'location': 'New York', 'timestamp': '2025-10-13 08:00:00', 'amount': 4},
    {'location': 'Berlin', 'timestamp': '2025-10-13 09:30:00', 'amount': 10},
    {'location': 'Tokyo', 'timestamp': '2025-10-13 11:15:00', 'amount':5}
]

# Create DataFrame
df = pd.DataFrame(data)

# Convert timestamp column to pandas DateTime format
df['timestamp'] = pd.to_datetime(df['timestamp'])

metadata = { # check to add all relevant fields for datapackage
  "name": "example-datapackage",
  "title": "Example Data Package",
  "licenses": [
    {
      "name": "CC-BY-4.0",
      "title": "Creative Commons Attribution 4.0",
      "path": "https://creativecommons.org/licenses/by/4.0/"
    }
  ],
  "resources": [
    {
      "name": "data",
      "path": "data.csv",
      "schema": {
        "fields": [ # match this to the standard we found for columns & add more fields?
          {"name": "location", "type": "string", "unit":"geolocation", "unit_uri":"", "name_uri":""},
          {"name": "timestamp", "type": "datetime", "unit":"datetime format", "unit_uri":"", "name_uri":""},
          {"name": "amount", "type": "integer", "unit":"kilogram", "unit_uri":"", "name_uri":""}
        ]
      }
    }
  ]
}

