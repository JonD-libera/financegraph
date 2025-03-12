import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from dateutil.relativedelta import relativedelta

# -------------------------------
# Define the time periods
# -------------------------------
today = datetime.datetime.today()

# Period 1: From Jan 20, 2021 to (today minus 4 years)
start_period1 = datetime.datetime(2021, 1, 20)
end_period1 = today - relativedelta(years=4)

# Period 2: From Jan 20, 2025 to today
start_period2 = datetime.datetime(2025, 1, 20)
end_period2 = today

# -------------------------------
# Fetch data using yfinance
# -------------------------------
ticker = yf.Ticker("^GSPC")
# ticker = yf.Ticker("TSLA")

# Get the historical data with daily frequency for each period and select only the 'Close'
data_period1 = ticker.history(start=start_period1, end=end_period1, interval="1d")['Close']
data_period2 = ticker.history(start=start_period2, end=end_period2, interval="1d")['Close']

# -------------------------------
# Reindex to include all business days and forward-fill missing values
# -------------------------------
# Create business day date ranges for each period (with timezone localization)
date_range1 = pd.date_range(start=start_period1, end=end_period1, freq='B').tz_localize('America/New_York')
date_range2 = pd.date_range(start=start_period2, end=end_period2, freq='B').tz_localize('America/New_York')

# Reindex and forward-fill
df1 = data_period1.reindex(date_range1, method='ffill').to_frame(name='close')
df2 = data_period2.reindex(date_range2, method='ffill').to_frame(name='close')

# Ensure the first value of 'close' is not null
if df2['close'].isnull().iloc[0]:
    df2['close'].iloc[0] = df2['close'].dropna().iloc[0]

# -------------------------------
# Compute % change from the prior day (daily change, if needed)
# -------------------------------
df1['pct_change'] = df1['close'].pct_change() * 100
df2['pct_change'] = df2['close'].pct_change() * 100

# -------------------------------
# Reset index and add a day count so we can compare day-by-day
# -------------------------------
df1 = df1.reset_index().rename(columns={'index': 'date'})
df1['day'] = range(1, len(df1) + 1)

df2 = df2.reset_index().rename(columns={'index': 'date'})
df2['day'] = range(1, len(df2) + 1)

# -------------------------------
# Merge the two DataFrames on the "day" column
# -------------------------------
df_merged = pd.merge(df1, df2, on='day', suffixes=('_2021', '_2025'))

# -------------------------------
# Initialize missing values in 'close_2025' with the first non-null value
# -------------------------------
df_merged['close_2025'] = df_merged['close_2025'].fillna(method='ffill')

# Normalize the closing prices to show cumulative percent change from day 1
df_merged['close_2021'] = df_merged['close_2021'].fillna(method='ffill')
df_merged['close_2025'] = df_merged['close_2025'].fillna(method='ffill')

df_merged['norm_2021'] = (df_merged['close_2021'] / df_merged['close_2021'].iloc[0] - 1) * 100
df_merged['norm_2025'] = (df_merged['close_2025'] / df_merged['close_2025'].iloc[0] - 1) * 100

# Display the merged DataFrame (side by side) with normalized values
print(df_merged.head())

# -------------------------------
# Export the merged data to a JSON file
# -------------------------------
json_output = df_merged.to_json("sp500_comparison.json", orient='records', date_format='iso', indent=4)
print("JSON file 'sp500_comparison.json' has been created.")

# -------------------------------
# Generate and save a normalized graph comparing the two periods
# -------------------------------
plt.figure(figsize=(10, 6))
plt.plot(df_merged['day'], df_merged['norm_2021'], label="Biden")
plt.plot(df_merged['day'], df_merged['norm_2025'], label="Trump")
plt.xlabel("Trading Day (Relative)")
plt.ylabel("Cumulative % Change")
plt.title("Normalized S&P 500 Cumulative % Change Comparison")
plt.legend()
plt.grid(True)
plt.tight_layout()

# Save the graph as a PNG file
plt.savefig("sp500_normalized_comparison.png")
print("Graph saved as 'sp500_normalized_comparison.png'.")
plt.show()
