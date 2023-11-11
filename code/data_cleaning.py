import os
import pandas as pd
import gzip
import matplotlib.pyplot as plt
import ast
import numpy as np

# Path to the directory containing the files. Change the city to the city you choose.
directory = 'data/raw/Amsterdam'

# Initialize an empty list to store the dataframes
dataframes = []

# Loop over the files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.csv.gz'):
        # Extract the date from the filename
        date = filename.split('_')[1]

        # Create the file path
        file_path = os.path.join(directory, filename)

        # Read the csv file
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            df = pd.read_csv(f)

            # Append the dataframe to the list
            dataframes.append(df)

# Concatenate the dataframes
all_data = pd.concat(dataframes, ignore_index=True)

# Print the head and row count
print(all_data.head())
print(f'Row count: {len(all_data)}')

# Count the number of unique IDs
unique_id_count = all_data['id'].nunique()

# Get the list of all columns
columns_list = all_data.columns.tolist()

# Print the list of columns
print("List of columns in the DataFrame:")
for column in columns_list:
    print(column)

# Print the results
print(f'Number of unique IDs: {unique_id_count}')

#Keep only the columns you are interested in
columns_to_keep = ['id', 'last_scraped', 'host_id', 'host_listings_count', 'host_total_listings_count', 'availability_365', 'number_of_reviews',
                   'number_of_reviews_ltm', 'review_scores_rating', 'reviews_per_month', 'neighbourhood_cleansed',
                   'host_is_superhost', 'host_since', 'host_response_time', 'host_response_rate', 'property_type', 'room_type',
                   'accommodates', 'bathrooms', 'bedrooms', 'beds', 'amenities', 'price', 'availability_30', 'availability_60',
                   'availability_90']
all_data = all_data[columns_to_keep]


# Remove both dollar signs and commas from the 'price' column before converting to float, then to integer
all_data['price'] = all_data['price'].replace({'\$': '', ',': ''}, regex=True).astype(float).astype(int)

# Convert stringified lists into actual lists
all_data['amenities'] = all_data['amenities'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Flatten the list of amenities into a single list and count the occurrences of each amenity
amenities_flat_list = [amenity for sublist in all_data['amenities'] for amenity in sublist]
amenities_counts = pd.Series(amenities_flat_list).value_counts()

# Get the top 20 most frequent amenities
top_20_amenities = amenities_counts.nlargest(20).index.tolist()

# Create dummy variables for the top 20 amenities
for amenity in top_20_amenities:
    all_data[amenity] = all_data['amenities'].apply(lambda x: int(amenity in x))

# Drop the original 'amenities' column if it's no longer needed
all_data.drop('amenities', axis=1, inplace=True)

# Sort the DataFrame by 'last_scraped' in descending order to get the latest date first
all_data_sorted = all_data.sort_values('last_scraped', ascending=False)

# Get the date prior to the earliest 'last_scraped' date in the DataFrame
if len(all_data_sorted['last_scraped']) > 1:
    # Use the second to last date as the reference date
    reference_date = all_data_sorted['last_scraped'].iloc[-2]
else:
    # If there's only one date, use the date three months prior as the reference date
    reference_date = all_data_sorted['last_scraped'].iloc[-1] - pd.DateOffset(months=3)

all_data['previous_scraped_date'] = reference_date
# Now, you can use reference_date as needed in your logic
# For example, to generate 'entrant_host' where it equals 1 if 'host_since' is later than the 'reference_date'
all_data['entrant_host'] = (all_data['host_since'] > reference_date).astype(int)

# create a new column book_365
all_data['book_365'] = 365 - all_data['availability_365']

# Generate new_review
all_data['new_review'] = all_data.groupby('id')['number_of_reviews'].diff()

all_data['new_book'] = all_data.groupby('id')['book_365'].diff()

# Show the resulting DataFrame
all_data.head()

# List of columns to check for NaN values
columns_to_check = ['price']

# Drop rows where NaN values are present in any of the specified columns
# all_data = all_data.dropna(subset=columns_to_check)
all_data = all_data.fillna(0)


# After dropping NaN values, you may also want to reset the index
all_data = all_data.reset_index(drop=True)

# Save the DataFrame to a CSV file without the index
all_data.to_csv('data/middle/boston_listing.csv', index=False)


# Print the number of listings per host
listings_per_host = all_data['host_id'].value_counts()
print('Number of listings per host:')
print(listings_per_host)

# Print the number of unique hosts
unique_hosts = all_data['host_id'].nunique()
print(f'Number of unique hosts: {unique_hosts}')

# Calculate summary statistics for the specified columns
summary_stats = all_data[['number_of_reviews', 'review_scores_rating', 'price', 'new_review', 'new_book', 'entrant_host']].describe()

# Select only the rows for mean, 50%, min, and max
summary_stats = summary_stats.loc[['mean', '50%', 'min', 'max']]

# Print the summary statistics
print('Summary statistics for mean, 50% (median), min, and max:')
print(summary_stats)

