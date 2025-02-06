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

       # Safely convert exit speed and launch angle to float
        try:
            exit_speed = float(row['ExitSpeed']) if 'ExitSpeed' in row else 0
        except ValueError:
            exit_speed = 0

        try:
            launch_angle = float(row['Angle']) if 'Angle' in row else 0
        except ValueError:
            launch_angle = 0

        # Initialize stats for each batter
        if batter_name not in players:
            players[batter_name] = {
                'ExitSpeeds': [],
                'Angles': [],
                'PA': 0,
                '1B': 0,
                '2B': 0,
                '3B': 0,
                'HR': 0,
                'H': 0,
                'TB': 0,
                'K': 0,
                'BB': 0,
                'HBP': 0,
                'SH': 0,
                'SF': 0,
                'AB': 0,
                'RBI': 0,
                'GDP': 0,
             }
        # Append exit speed and launch angle to the player's list to get avgs.
        if exit_speed != 0:
            players[batter_name]['ExitSpeeds'].append(exit_speed)
        if launch_angle != 0:
            players[batter_name]['Angles'].append(launch_angle)

        # Initialize stats for each pitcher
        # TO DO: Initialize pitcher stats

        # Create a unique identifier for each batter's plate appearance
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

        # Calculate Average Exit Velocity and Average Launch Angle for each player
        for player in players:
            exit_speeds = players[player]['ExitSpeeds']
            angles = players[player]['Angles']
            
            avg_exit_velocity = sum(exit_speeds) / len(exit_speeds) if exit_speeds else 0
            avg_launch_angle = sum(angles) / len(angles) if angles else 0
            
            players[player]['AvgExitVelocity'] = avg_exit_velocity
            players[player]['AvgLaunchAngle'] = avg_launch_angle

    return players

# Function that prints all Stats
def print_stats(players):
    for player, stats in players.items():

        # ----- Simple Hitting Stats ----- #

        PA = stats['PA'] # Plate Appearances
        AB = stats['AB'] # At Bats
        H = stats['H'] # Hits
        K = stats['K'] # Strikeouts
        BB = stats['BB'] # Walks
        HBP = stats['HBP'] # Hit By Pitch
        SH = stats['SH'] # Sacrifice Hits
        SF = stats['SF'] # Sacrifice Flies
        TB = stats['TB'] # Total Bases
        oneB = stats['1B'] # Singles
        twoB = stats['2B'] # Doubles
        threeB = stats['3B'] # Triples
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
        OPS = (OBP + SLG) # On Base Plus Slugging Percentage
        ISO = SLG - AVG # Isolated Power
        BABIP = (H - HR) / (AB - K - HR + SF) if (AB - K - HR + SF) > 0 else 0 # Batting Average on Balls in Play

        wOBA = ((wOBA_WEIGHTS['BB'] * BB) +
                (wOBA_WEIGHTS['HBP'] * HBP) +
                (wOBA_WEIGHTS['1B'] * oneB) +
                (wOBA_WEIGHTS['2B'] * twoB) +
                (wOBA_WEIGHTS['3B'] * threeB) +
                (wOBA_WEIGHTS['HR'] * HR)) / (
                    AB + BB + HBP + SF
                ) if (AB + BB + HBP + SF) > 0 else 0 # Weighted On Base Average
   
        # --------------- Display Hitting Stats ---------------#
        print(f"Player: {player}")
        print(f"PA: {PA}, AB: {AB}, H: {H}, TB: {TB}")
        print(f"1B: {oneB}, 2B: {twoB}, 3B: {threeB}, HR: {HR}")
        print(f"RBI: {RBI}, BB: {BB}, K: {K}, HBP: {HBP}, SF: {SF}, SH: {SH}, GDP: {GDP}")
        print(f"AVG: {AVG:.2f}, BB%: {BBpercent:.2f}%, K%: {Kpercent:.2f}%")
        print(f"OBP: {OBP:.2f}, SLG: {SLG:.2f}, OPS: {OPS:.2f}, ISO: {ISO:.2f}, BABIP: {BABIP:.2f}, wOBA: {wOBA:.2f}")
        print(f"Avg Exit Velocity: {stats['AvgExitVelocity']:.2f} MPH, Avg Launch Angle: {stats['AvgLaunchAngle']:.2f} degrees")
        print()

        # ----- Simple Pitching Stats ----- #
        # TO DO: Add pitching stats

        # --------------- Display Pitching Stats --------------- #
        # TO DO: Print pitching stats

# -------------------- MAIN FUNCTION -------------------- #
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
