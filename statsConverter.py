'''
Python script that converts the stats from a CSV file into meaningful
pitcher and batter stats.

Author: Demarco Guajardo
'''

# Imports
import csv
from collections import defaultdict

# Define constants for wOBA calculation based on 2024 season
# Values found on https://www.fangraphs.com/guts.aspx?type=cn
wOBA_AVG = 0.310
wOBA_SCALE = 1.24
wOBA_WEIGHTS = {
    'BB': 0.69,
    'HBP': 0.72,
    '1B': 0.88,
    '2B': 1.25,
    '3B': 1.59,
    'HR': 2.05
}

def read_csv(file_path):
    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

def calculate_stats(data):
    players = defaultdict(lambda: defaultdict(int))
    plate_appearances = set()

    # Iterate through the data
    for row in data:
        pitcher_name = row['Pitcher']
        pitcher_id = row['PitcherId']
        batter_name = row['Batter']
        batter_id = row['BatterId']
        pitcher_team_name = row['PitcherTeam']
        batter_team_name = row['BatterTeam']
        play_result = row['PlayResult']
        hit_type = row['TaggedHitType']
        korbb = row['KorBB']
        pitch_call = row['PitchCall']
        runs_scored = int(row['RunsScored']) if 'RunsScored' in row else 0
        outs_before = int(row['Outs']) if 'Outs' in row else 0
        pitch_number = int(row['PitchNumber']) if 'PitchNumber' in row else 0
        inning = row['Inning']
        inning_half = row['Top/Bottom']
        pa_of_inning = row['PAofInning']
        outs_on_play = int(row['OutsOnPlay']) if 'OutsOnPlay' in row else 0

        # Create a unique identifier for each plate appearance
        pa_identifier = (batter_name, inning, inning_half, pa_of_inning)

        # Check if this is a new plate appearance
        if pa_identifier not in plate_appearances:
            plate_appearances.add(pa_identifier)
            players[batter_name]['PA'] += 1

        # Plays and correlated stats
        if play_result == 'Single':
            players[batter_name]['1B'] += 1 # Single
            players[batter_name]['H'] += 1 # Hit
            players[batter_name]['TB'] += 1 # Total Bases
        elif play_result == 'Double':
            players[batter_name]['2B'] += 1 # Double
            players[batter_name]['H'] += 1
            players[batter_name]['TB'] += 2
        elif play_result == 'Triple':
            players[batter_name]['3B'] += 1 # Triple
            players[batter_name]['H'] += 1
            players[batter_name]['TB'] += 3
        elif play_result == 'HomeRun':
            players[batter_name]['HR'] += 1 # Home Run
            players[batter_name]['H'] += 1 
            players[batter_name]['TB'] += 4 
        elif play_result == 'Sacrifice':
            if hit_type == 'Bunt':
                players[batter_name]['SH'] += 1
            elif hit_type in ['FlyBall', 'Popup']: 
                players[batter_name]['SF'] += 1

        if korbb == 'Strikeout':
            players[batter_name]['K'] += 1 # Strikeout
            players[batter_name]['AB'] += 1 # Strikeout counts as AB
        elif korbb == 'Walk':
            players[batter_name]['BB'] += 1 # Walk

        if pitch_call == 'HitByPitch':
            players[batter_name]['HBP'] += 1 # Hit By Pitch
        
        # Increment AB based on definition
        # AB = Batter reaches base via fielder's choice, hit, or error,
        # or non-sacrifice out.
        if play_result in ['Single', 'Double', 'Triple', 'HomeRun', 'Error',
                     'FieldersChoice', 'Out'] and play_result != 'Sacrifice':
            players[batter_name]['AB'] += 1

        # Increment RBI based on the definition
        # RBI = Result of PA is run scored, excluding errors and ground double plays
        if play_result not in ['Error', 'FieldersChoice'] and not (play_result == 'Out' and hit_type == 'GroundBall' and outs_on_play == 2):
            players[batter_name]['RBI'] += runs_scored
        elif play_result == 'Sacrifice':
            players[batter_name]['RBI'] += runs_scored # Sacrifice fly or hit
        if korbb == 'Walk' and runs_scored > 0:
            players[batter_name]['RBI'] += runs_scored # Bases-loaded walk
        if pitch_call == 'HitByPitch' and runs_scored > 0:
            players[batter_name]['RBI'] += runs_scored # Bases-loaded hit by pitch

        # Check for Ground into Double Play (GDP)
        if play_result == 'Out' and hit_type == 'GroundBall' and outs_on_play == 2:
            players[batter_name]['GDP'] += 1 # Ground into Double Play

    return players

def print_stats(players):
    for player, stats in players.items():

        # Simple Stats 

        PA = stats['PA'] # Plate Appearances
        AB = stats['AB'] # At Bats
        H = stats['H'] # Hits
        K = stats['K'] # Strikeouts
        BB = stats['BB'] # Walks
        HBP = stats['HBP'] # Hit By Pitch
        SH = stats['SH'] # Sacrifice Hits
        SF = stats['SF'] # Sacrifice Flies
        TB = stats['TB'] # Total Bases
        OneB = stats['1B'] # Singles
        TwoB = stats['2B'] # Doubles
        ThreeB = stats['3B'] # Triples
        HR = stats['HR'] # Home Runs
        RBI = stats['RBI'] # Runs Batted In
        GDP = stats['GDP'] # Ground into Double Play

        # Additional Stats

        AVG = H / AB if AB > 0 else 0 # Batting Average
        BBpercent = BB / PA * 100 if PA > 0 else 0 # Walk Percentage
        Kpercent = K / PA * 100 if PA > 0 else 0 # Strikeout Percentage

        # Advanced Stats

        OBP = (H + BB + HBP) / (AB + BB + HBP + SF) if (AB + BB + HBP + SF) > 0 else 0 # On Base Percentage
        SLG = TB / AB if AB > 0 else 0 # Slugging Percentage
        ISO = SLG - AVG if AB > 0 else 0 # Isolated Power
        BABIP = (H - HR) / (AB - K - HR + SF) if (AB - K - HR + SF) > 0 else 0 # Batting Average on Balls in Play

        wOBA = ((wOBA_WEIGHTS['BB'] * BB) +
                (wOBA_WEIGHTS['HBP'] * HBP) +
                (wOBA_WEIGHTS['1B'] * OneB) +
                (wOBA_WEIGHTS['2B'] * TwoB) +
                (wOBA_WEIGHTS['3B'] * ThreeB) +
                (wOBA_WEIGHTS['HR'] * HR)) / (
                    AB + BB + HBP + SF
                ) if (AB + BB + HBP + SF) > 0 else 0 # Weighted On Base Average
   
        # Display Stats
        print(f"Player: {player}")
        print(f"PA: {PA}, AB: {AB}, H: {H}")
        print(f"1B: {OneB}, 2B: {TwoB}, 3B: {ThreeB}, HR: {HR}")
        print(f"RBI: {RBI}, BB: {BB}, K: {K}, HBP: {HBP}, SF: {SF}, SH: {SH}, GDP: {GDP}")
        print(f"AVG: {AVG:.2f}, BB%: {BBpercent:.2f}%, K%: {Kpercent:.2f}%")
        print(f"OBP: {OBP:.2f}, SLG: {SLG:.2f}, ISO: {ISO:.2f}, BABIP: {BABIP:.2f}, wOBA: {wOBA:.2f}")
        print()

if __name__ == "__main__":
    file_path = input("Enter the path to the CSV file: ")
    
    data = read_csv(file_path)
    if data is not None:
        print()
        print("File found successfully! Opening now...")
        print()
        
        players = calculate_stats(data)
        print_stats(players)
    else:
        print("Failed to read the CSV file.")
