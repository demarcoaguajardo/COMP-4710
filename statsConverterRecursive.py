import csv
import os
import glob
from collections import defaultdict

# Define constants for wOBA calculation based on 2024 season
wOBA_WEIGHTS = {
    'BB': 0.69,
    'HBP': 0.72,
    '1B': 0.88,
    '2B': 1.25,
    '3B': 1.59,
    'HR': 2.05
}

# Function to read all CSV files in a directory, including subdirectories
def read_csv_directory(directory_path):
    all_data = []
    csv_files = glob.glob(os.path.join(directory_path, '**', '*.csv'), recursive=True)

    for file_path in csv_files:
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                data = []
                for row in reader:
                    # Normalize column names by stripping spaces and converting to lowercase
                    normalized_row = {key.strip().lower(): value for key, value in row.items()}
                    data.append(normalized_row)
                all_data.extend(data)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
    
    return all_data

# Function to calculate player statistics
def calculate_stats(data):
    players = defaultdict(lambda: defaultdict(int))
    plate_appearances = set()

    for row in data:
        # Safely access required columns (use .get() for missing columns)
        game_id = row.get('gameid', '').strip()
        batter_name = row.get('batter', '').strip()
        batter_team = row.get('batterteam', '').strip()  # Get player team
        play_result = row.get('playresult', '').strip()
        hit_type = row.get('taggedhittype', '').strip()
        korbb = row.get('korbb', '').strip()
        pitch_call = row.get('pitchcall', '').strip()
        runs_scored = int(row.get('runsscored', '0')) if row.get('runsscored', '0').isdigit() else 0
        outs_on_play = int(row.get('outsonplay', '0')) if row.get('outsonplay', '0').isdigit() else 0
        inning = row.get('inning', '').strip()
        inning_half = row.get('top/bottom', '').strip()
        pa_of_inning = row.get('paofinning', '').strip()

        try:
            exit_speed = float(row.get('exitspeed', '0'))
        except ValueError:
            exit_speed = 0

        try:
            launch_angle = float(row.get('angle', '0'))
        except ValueError:
            launch_angle = 0

        if batter_name not in players:
            players[batter_name] = {
                'ExitSpeeds': [], 'Angles': [], 'PA': 0, '1B': 0, '2B': 0, '3B': 0,
                'HR': 0, 'H': 0, 'TB': 0, 'K': 0, 'BB': 0, 'HBP': 0, 'SH': 0,
                'SF': 0, 'AB': 0, 'RBI': 0, 'GDP': 0, 'Team': batter_team  # Store the team name
            }

        if exit_speed:
            players[batter_name]['ExitSpeeds'].append(exit_speed)
        if launch_angle:
            players[batter_name]['Angles'].append(launch_angle)

        # Unique plate appearance tracking
        pa_identifier = (game_id, batter_name, inning, inning_half, pa_of_inning)
        if pa_identifier not in plate_appearances:
            plate_appearances.add(pa_identifier)
            players[batter_name]['PA'] += 1

        # Explicitly handle play results
        if play_result == 'Single':
            players[batter_name]['1B'] += 1
            players[batter_name]['H'] += 1
            players[batter_name]['TB'] += 1
        elif play_result == 'Double':
            players[batter_name]['2B'] += 1
            players[batter_name]['H'] += 1
            players[batter_name]['TB'] += 2
        elif play_result == 'Triple':
            players[batter_name]['3B'] += 1
            players[batter_name]['H'] += 1
            players[batter_name]['TB'] += 3
        elif play_result == 'HomeRun':
            players[batter_name]['HR'] += 1
            players[batter_name]['H'] += 1
            players[batter_name]['TB'] += 4

        if play_result == 'Sacrifice':
            players[batter_name]['SH' if hit_type == 'Bunt' else 'SF'] += 1

        if korbb == 'Strikeout':
            players[batter_name]['K'] += 1
            players[batter_name]['AB'] += 1
        elif korbb == 'Walk':
            players[batter_name]['BB'] += 1

        if pitch_call == 'HitByPitch':
            players[batter_name]['HBP'] += 1

        if play_result in ['Single', 'Double', 'Triple', 'HomeRun', 'Error', 'FieldersChoice', 'Out'] and play_result != 'Sacrifice':
            players[batter_name]['AB'] += 1

        if play_result not in ['Error', 'FieldersChoice'] and not (play_result == 'Out' and hit_type == 'GroundBall' and outs_on_play == 2):
            players[batter_name]['RBI'] += runs_scored
        elif play_result == 'Sacrifice':
            players[batter_name]['RBI'] += runs_scored
        if korbb == 'Walk' and runs_scored > 0:
            players[batter_name]['RBI'] += runs_scored
        if pitch_call == 'HitByPitch' and runs_scored > 0:
            players[batter_name]['RBI'] += runs_scored

        if play_result == 'Out' and hit_type == 'GroundBall' and outs_on_play == 2:
            players[batter_name]['GDP'] += 1

    # Compute missing advanced stats and averages
    for player in players:
        stats = players[player]
        exit_speeds = stats['ExitSpeeds']
        angles = stats['Angles']

        # Calculate the average exit speed and average launch angle
        stats['AvgExitVelocity'] = sum(exit_speeds) / len(exit_speeds) if exit_speeds else 0
        stats['AvgLaunchAngle'] = sum(angles) / len(angles) if angles else 0

        # Calculate basic and advanced stats
        PA, AB, H, BB, K, HBP, SF, TB, oneB, twoB, threeB, HR, RBI = (
            stats['PA'], stats['AB'], stats['H'], stats['BB'], stats['K'], stats['HBP'],
            stats['SF'], stats['TB'], stats['1B'], stats['2B'], stats['3B'], stats['HR'], stats['RBI']
        )

        stats['AVG'] = H / AB if AB > 0 else 0
        stats['BB%'] = (BB / PA) * 100 if PA > 0 else 0
        stats['K%'] = (K / PA) * 100 if PA > 0 else 0
        stats['OBP'] = (H + BB + HBP) / (AB + BB + HBP + SF) if (AB + BB + HBP + SF) > 0 else 0
        stats['SLG'] = TB / AB if AB > 0 else 0
        stats['OPS'] = stats['OBP'] + stats['SLG']
        stats['ISO'] = stats['SLG'] - stats['AVG']
        stats['BABIP'] = (H - HR) / (AB - K - HR + SF) if (AB - K - HR + SF) > 0 else 0
        stats['wOBA'] = sum(wOBA_WEIGHTS[stat] * stats[stat] for stat in wOBA_WEIGHTS if stat in stats) / (AB + BB + HBP + SF) if (AB + BB + HBP + SF) > 0 else 0

    return players

# Function to write stats to a new CSV file
def write_stats_to_csv(players, output_file):
    fieldnames = ['Player', 'Team', 'PA', 'AB', 'H', 'TB', '1B', '2B', '3B', 'HR', 'RBI', 
                  'BB', 'K', 'HBP', 'SF', 'SH', 'GDP', 'AVG', 'BB%', 'K%', 
                  'OBP', 'SLG', 'OPS', 'ISO', 'BABIP', 'wOBA', 'AvgExitVelocity', 'AvgLaunchAngle']

    with open(output_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for player, stats in players.items():
            # Remove unwanted fields
            cleaned_stats = {k: v for k, v in stats.items() if k not in ['ExitSpeeds', 'Angles']}
            writer.writerow({'Player': player, 'Team': cleaned_stats['Team'], **cleaned_stats})

if __name__ == "__main__":
    directory_path = input("Enter the directory path: ")
    output_file = input("Enter the output CSV file path: ")

    data = read_csv_directory(directory_path)
    if data:
        players = calculate_stats(data)
        write_stats_to_csv(players, output_file)
        print(f"Stats saved to {output_file}")
    else:
        print("No CSV files found.")