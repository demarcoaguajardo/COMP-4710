import pandas as pd
import os

def combine_csv_files(source_directory, output_filename):
    all_dataframes = []

    # Walk through all subdirectories
    for root, _, files in os.walk(source_directory):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                try:
                    df = pd.read_csv(file_path)
                    df['SourceFile'] = file  # Optional: Track where each row came from
                    all_dataframes.append(df)
                except Exception as e:
                    print(f"Skipping {file_path} due to error: {e}")

    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        combined_df.to_csv(output_filename, index=False)
        print(f"Combined CSV saved to: {output_filename}")
    else:
        print("No valid CSV files found.")

if __name__ == "__main__":
    # Replace with your folder path and desired output file name
    source_directory = "C:/Users/William/OneDrive/Desktop/Testing"
    output_filename = "C:/Users/William/OneDrive/Desktop/Testing/PerGame.csv"
    combine_csv_files(source_directory, output_filename)
