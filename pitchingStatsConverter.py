'''
pitchingStatsConverter.py

Python script that converts the stats from a CSV file into meaningful
pitcher stats.

Author: Demarco Guajardo
'''

# Imports
import csv
from collections import defaultdict
import statistics

# Define strike zone boundaries
STRIKE_ZONE = {
    'side_min': -0.7085,
    'side_max': 0.7085,
    'height_min': 1.7,
    'height_max': 3.4
}

# Define strike zone parts
#   Upper = 2.83 to 3.4
#   Middle = 2.27 to 2.83
#   Lower = 1.7 to 2.27
STRIKE_ZONE_HEIGHT = STRIKE_ZONE['height_max'] - STRIKE_ZONE['height_min']
UPPER_ZONE_MAX = STRIKE_ZONE['height_max']
UPPER_ZONE_MIN = STRIKE_ZONE['height_min'] + (2 * STRIKE_ZONE_HEIGHT / 3)
MID_ZONE_MAX = UPPER_ZONE_MIN
MID_ZONE_MIN = STRIKE_ZONE['height_min'] + (STRIKE_ZONE_HEIGHT / 3)
LOWER_ZONE_MAX = MID_ZONE_MIN
LOWER_ZONE_MIN = STRIKE_ZONE['height_min']

def read_csv(file_path):
    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

def calculate_pitching_stats(data):
    pitchers = defaultdict(lambda: defaultdict(int)) # Dictionary of pitchers and their stats
    fastball_vert_appr_anngles = defaultdict(list) # Stores VertApprAngles for fastballs
    fastball_upper_zone_angles = defaultdict(list) # Stores VertApprAngles for fastballs in the upper zone
    fastball_mid_zone_angles = defaultdict(list) # Stores VertApprAngles for fastballs in the middle zone
    fastball_lower_zone_angles = defaultdict(list) # Stores VertApprAngles for fastballs in the lower zone


    team_runs = defaultdict(int) # Tracks runs scored by each team
    pitcher_teams = defaultdict(str) # Tracks team of each pitcher
    current_batter = defaultdict(str) # Tracks unique batters faced by each pitcher
    first_three_pitches = defaultdict(lambda: defaultdict(list)) # Tracks first three pitches of each PA
    pitches_in_at_bat = defaultdict(lambda: defaultdict(int)) # Tracks pitches thrown in each at-bat

    # Iterate through the data
    for row in data:
        game_id = row['GameID']
        pitcher_name = row['Pitcher']
        batter_name = row['Batter']
        runs_scored = int(row['RunsScored']) if 'RunsScored' in row else 0
        outs_on_play = int(row['OutsOnPlay']) if 'OutsOnPlay' in row else 0
        korbb = row ['KorBB']
        pitcher_team = row['PitcherTeam']
        batter_team = row['BatterTeam']
        pitch_of_pa = int(row['PitchofPA']) if 'PitchofPA' in row else 0
        pitch_call = row['PitchCall']
        strikes = int(row['Strikes']) if 'Strikes' in row else 0
        balls = int(row['Balls']) if 'Balls' in row else 0
        tagged_hit_type = row['TaggedHitType']
        play_result = row['PlayResult']
        plate_loc_side = float(row['PlateLocSide']) if 'PlateLocSide' in row else 0
        plate_loc_height = float (row['PlateLocHeight']) if 'PlateLocHeight' in row else 0
        tagged_pitch_type = row['TaggedPitchType']
        vert_appr_angle = float(row['VertApprAngle']) if 'VertApprAngle' in row else 0

        # Initialize stats for each pitcher
        if pitcher_name not in pitchers:
            pitchers[pitcher_name] = {
                'EarnedRuns': 0,
                'InningsPitched': 0,
                'OutsRecorded': 0,
                'ERA': 0,
                'Wins': 0,
                'Losses': 0,
                'Strikeouts': 0,
                'Walks': 0,
                'TotalBattersFaced': 0,
                'FirstPitchStrikes': 0,
                'FirstPitchBalls': 0,
                'TotalPitches': 0,
                'Strikes': 0,
                'Balls': 0,
                'HitBatters': 0,
                'FoulsAfter2Strikes': 0,
                'First2of3StrikesOrInPlay': 0,
                'AtBatEfficiency': 0,
                'HomeRuns': 0,
                'FIP': 0,
                'Swings': 0,
                'Whiffs': 0,
                'CalledStrikes': 0,
                'IZSwings': 0,
                'IZWhiffs': 0,
                'IZPitches': 0,
                'OZSwings': 0,
                'OZWhiffs': 0,
                'OZPitches': 0,
                'Fastballs': 0,
                'FBVertApprAngles': [],
                'FBnVAA': 0,
                'UpperZonePitches': 0,
                'MidZonePitches': 0,
                'LowerZonePitches': 0,
                'FBVAAUpper': 0,
                'FBVAAMid': 0,
                'FBVAALower': 0,
                'Cutters': 0,
                'Sinkers': 0,
                'Sliders': 0
            }


        # Track total pitches thrown
        pitchers[pitcher_name]['TotalPitches'] += 1

        # Track total pitches thrown outside the strike zone
        if not (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
            pitchers[pitcher_name]['OZPitches'] += 1

        # Track total pitches thrown inside the strike zone
        if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
            STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
            pitchers[pitcher_name]['IZPitches'] += 1

            # Track pitches in different parts of the strike zone
            if UPPER_ZONE_MIN <= plate_loc_height <= UPPER_ZONE_MAX:
                pitchers[pitcher_name]['UpperZonePitches'] += 1
                if tagged_pitch_type in ['Fastball', 'FourSeamFastBall', 'TwoSeamFastBall']:
                    fastball_upper_zone_angles[pitcher_name].append(vert_appr_angle)
            elif MID_ZONE_MIN <= plate_loc_height <= MID_ZONE_MAX:
                pitchers[pitcher_name]['MidZonePitches'] += 1
                if tagged_pitch_type in ['Fastball', 'FourSeamFastBall', 'TwoSeamFastBall']:
                    fastball_mid_zone_angles[pitcher_name].append(vert_appr_angle)
            elif LOWER_ZONE_MIN <= plate_loc_height <= LOWER_ZONE_MAX:
                pitchers[pitcher_name]['LowerZonePitches'] += 1
                if tagged_pitch_type in ['Fastball', 'FourSeamFastBall', 'TwoSeamFastBall']:
                    fastball_lower_zone_angles[pitcher_name].append(vert_appr_angle)

        # Track pitch types
        if tagged_pitch_type in ['Fastball', 'FourSeamFastBall', 'TwoSeamFastBall']:
            pitchers[pitcher_name]['Fastballs'] += 1
            pitchers[pitcher_name]['FBVertApprAngles'].append(vert_appr_angle)
            fastball_vert_appr_anngles[pitcher_name].append(vert_appr_angle)
        elif tagged_pitch_type == 'Cutter':
            pitchers[pitcher_name]['Cutters'] += 1
        elif tagged_pitch_type == 'Sinker':
            pitchers[pitcher_name]['Sinkers'] += 1
        elif tagged_pitch_type == 'Slider':
            pitchers[pitcher_name]['Sliders'] += 1


        # Track earned runs for pitchers 
        #   Note: Can not track inherited runners or passed balls so this only accounts for runs excluding errors
        if row['PlayResult'] != 'Error':
            pitchers[pitcher_name]['EarnedRuns'] += runs_scored

        # Track outs recorded by pitchers
        pitchers[pitcher_name]['OutsRecorded'] += outs_on_play

        # Track strikeouts and walks for pitchers
        if korbb == 'Strikeout':
            pitchers[pitcher_name]['OutsRecorded'] += 1
            pitchers[pitcher_name]['Strikeouts'] += 1
        elif korbb == 'Walk':
            pitchers[pitcher_name]['Walks'] += 1

        # Track total batters faced
        if current_batter[pitcher_name] != batter_name:
            pitchers[pitcher_name]['TotalBattersFaced'] += 1
            current_batter[pitcher_name] = batter_name

        # Track first pitch strikes if a strike is thrown, there's a foul ball, or the ball is put in play
        if pitch_of_pa == 1 and (pitch_call == 'StrikeCalled' or 
                                 pitch_call == 'StrikeSwinging' or
                                 pitch_call == 'FoulBall' or
                                 pitch_call == 'InPlay'):
            pitchers[pitcher_name]['FirstPitchStrikes'] += 1

        # Track first pitch balls if a ball is thrown or if there's a hit by pitch
        if pitch_of_pa == 1 and (pitch_call == 'BallCalled' or
                                 pitch_call == 'BallinDirt' or
                                 pitch_call == 'BallIntentional' or
                                 pitch_call == 'HitByPitch'):
            pitchers[pitcher_name]['FirstPitchBalls'] += 1

        # Track Strikes and Balls and Fouls After 2 Strikes and Hit By Pitches
        if pitch_call in ['StrikeCalled', 'StrikeSwinging', 'InPlay']:
            pitchers[pitcher_name]['Strikes'] += 1
        elif pitch_call == 'FoulBall':
            if strikes < 2 or (strikes == 2 and tagged_hit_type == 'Bunt'):
                pitchers[pitcher_name]['Strikes'] += 1
            elif strikes == 2 and tagged_hit_type != 'Bunt':
                pitchers[pitcher_name]['FoulsAfter2Strikes'] += 1
        elif pitch_call in ['BallCalled', 'BallinDirt', 'BallIntentional']:
            pitchers[pitcher_name]['Balls'] += 1
        elif pitch_call == 'HitByPitch':
            pitchers[pitcher_name]['HitBatters'] += 1

        # Track Home Runs
        if play_result == 'HomeRun':
            pitchers[pitcher_name]['HomeRuns'] += 1

        # Track swings and whiffs
        if pitch_call in ['StrikeSwinging', 'InPlay', 'FoulBall']:
            pitchers[pitcher_name]['Swings'] += 1
            # Check if the pitch was inside the strike zone
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                pitchers[pitcher_name]['IZSwings'] += 1
            # Swing is outside strikezone
            else:
                pitchers[pitcher_name]['OZSwings'] += 1
        if pitch_call == 'StrikeSwinging':
            pitchers[pitcher_name]['Whiffs'] += 1
            # Check if the pitch was inside the strike zone
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                pitchers[pitcher_name]['IZWhiffs'] += 1
            # Whiff is outside strikezone
            else:
                pitchers[pitcher_name]['OZWhiffs'] += 1


        # Track called strikes
        if pitch_call == 'StrikeCalled':
            pitchers[pitcher_name]['CalledStrikes'] += 1

        # Track the first three pitches of each plate appearance
        if pitch_of_pa == 1:
            first_three_pitches[pitcher_name][batter_name] = [] # Initialize the list for new PA
        if pitch_of_pa <= 3: 
            first_three_pitches[pitcher_name][batter_name].append((pitch_call, strikes))
        # Check if the first two pitches are strikes or in play
        if pitch_of_pa == 3:
            first_three = first_three_pitches[pitcher_name][batter_name]
            strike_count = 0
            for pitch, strikes in first_three:
                if pitch in ['StrikeCalled', 'StrikeSwinging', 'InPlay']:
                    strike_count += 1
                elif pitch == 'FoulBall':
                    if strikes < 2 or (strikes == 2 and tagged_hit_type == 'Bunt'):
                        strike_count += 1
            if strike_count >= 2:
                pitchers[pitcher_name]['First2of3StrikesOrInPlay'] += 1
            first_three_pitches[pitcher_name][batter_name] = [] # Reset first three pitches

        # Track runs scored by each team
        team_runs[batter_team] += runs_scored
        # Track team of each pitcher
        pitcher_teams[pitcher_name] = pitcher_team

        # Track number of pitches in each at-bat
        pitches_in_at_bat[pitcher_name][batter_name] += 1
        # Check if the at-bat is completed
        if play_result in ['Single', 'Double', 'Triple', 'HomeRun', 'Error', 'FieldersChoice', 'Out'] and play_result != 'Sacrifice':
            if pitch_of_pa <= 4:
                pitchers[pitcher_name]['AtBatEfficiency'] += 1
            pitches_in_at_bat[pitcher_name][batter_name] = 0 # Reset for the next at-bat

    # Calculate stats for each pitcher
    for pitcher in pitchers:
        outs_recorded = pitchers[pitcher]['OutsRecorded'] # Outs Recorded
        earned_runs = pitchers[pitcher]['EarnedRuns'] # Earned Runs
        innings_pitched = outs_recorded / 3 # Innings Pitched
        pitchers[pitcher]['InningsPitched'] = innings_pitched 
        pitchers[pitcher]['ERA'] = (9 * earned_runs / innings_pitched) if innings_pitched > 0 else 0 # ERA
        home_runs = pitchers[pitcher]['HomeRuns'] # Home Runs
        walks = pitchers[pitcher]['Walks'] # Walks
        hit_by_pitches = pitchers[pitcher]['HitBatters'] # Hit Batters
        strikeouts = pitchers[pitcher]['Strikeouts']
        inn_pitched = pitchers[pitcher]['InningsPitched']
        FIP_constant = 3.17 # This is a constant used from the 2024 MLB season
        # Calculate FIP
        if inn_pitched > 0:
            pitchers[pitcher]['FIP'] = ((13 * home_runs) + (3 * (walks + hit_by_pitches)) 
                                        - (2 * strikeouts)) / inn_pitched + FIP_constant
        else:
            pitchers[pitcher]['FIP'] = 0

        #Calculate FB nVAA (using the median, because normalizing makes the mean less useful)
        if fastball_vert_appr_anngles[pitcher]:
            mean_vert_appr_angle = statistics.mean(fastball_vert_appr_anngles[pitcher])
            stddev_vert_appr_angle = statistics.stdev(fastball_vert_appr_anngles[pitcher])
            normalized_angles = [(angle - mean_vert_appr_angle) / stddev_vert_appr_angle
                                 for angle in fastball_vert_appr_anngles[pitcher]]
            pitchers[pitcher]['FBnVAA'] = statistics.median(normalized_angles)
            # # Debugging Prints
            # print(f"Pitcher: {pitcher}")
            # print(f"VertApprAngles: {fastball_vert_appr_anngles[pitcher]}")
            # print(f"Mean Vertical Approach Angle: {mean_vert_appr_angle}")
            # print(f"Standard Deviation of Vertical Approach Angle: {stddev_vert_appr_angle}")
            # print(f"Normalized Vertical Approach Angles: {normalized_angles}")
            # print(f"Sum of Normalized Angles: {sum(normalized_angles)}")
            # print(f"FB nVAA: {pitchers[pitcher]['FBnVAA']}")
            # print()
        else:
            pitchers[pitcher]['FBnVAA'] = 0

        # Calculate FB VAA for different strike zone parts (using mean bc not normalized))
        if fastball_upper_zone_angles[pitcher]:
            pitchers[pitcher]['FBVAAUpper'] = statistics.mean(fastball_upper_zone_angles[pitcher])
        else: 
            pitchers[pitcher]['FBVAAUpper'] = 0
        if fastball_mid_zone_angles[pitcher]:
            pitchers[pitcher]['FBVAAMid'] = statistics.mean(fastball_mid_zone_angles[pitcher])
        else:
            pitchers[pitcher]['FBVAAMid'] = 0
        if fastball_lower_zone_angles[pitcher]:
            pitchers[pitcher]['FBVAALower'] = statistics.mean(fastball_lower_zone_angles[pitcher])
        else:
            pitchers[pitcher]['FBVAALower'] = 0
        # Debugging prints for vertical approach angles in each zone
        print(f"Pitcher: {pitcher}")
        print(f"Upper Zone Pitches: {pitchers[pitcher]['UpperZonePitches']}, Mid Zone Pitches: {pitchers[pitcher]['MidZonePitches']}, Lower Zone Pitches: {pitchers[pitcher]['LowerZonePitches']}")
        print(f"Upper Zone VertApprAngles: {fastball_upper_zone_angles[pitcher]}")
        print(f"Mid Zone VertApprAngles: {fastball_mid_zone_angles[pitcher]}")
        print(f"Lower Zone VertApprAngles: {fastball_lower_zone_angles[pitcher]}")
        print(f"FB VAA Upper: {pitchers[pitcher]['FBVAAUpper']:.2f}, FB VAA Mid: {pitchers[pitcher]['FBVAAMid']:.2f}, FB VAA Lower: {pitchers[pitcher]['FBVAALower']:.2f}")
        print()

    return pitchers, team_runs, pitcher_teams

# Function to assign wins and losses to pitchers
def assign_wins_losses(pitchers, team_runs, pitcher_teams):
    teams = list(team_runs.keys())
    if len(teams) == 2:
        team1, team2 = teams
        runs_team1 = team_runs[team1]
        runs_team2 = team_runs[team2]

        # Skip practice games between AUB_TIG and AUB_PRC
        if set(teams) == {'AUB_TIG', 'AUB_PRC'}:
            return

        # Assign wins and losses to pitchers
        if runs_team1 > runs_team2:
            winning_team = team1
            losing_team = team2
        elif runs_team2 > runs_team1:
            winning_team = team2
            losing_team = team1
        else:
            return # Tie = No wins or losses assigned
        for pitcher, team in pitcher_teams.items():
            if team == winning_team:
                pitchers[pitcher]['Wins'] += 1
            elif team == losing_team:
                pitchers[pitcher]['Losses'] += 1

# Function that prints pitching stats
def print_pitching_stats(pitchers):
    for pitcher, stats in pitchers.items():

        # ----- Simple Pitching Stats ----- #

        earnedRuns = stats['EarnedRuns'] # Earned Runs
        IP = stats['InningsPitched'] # Innings Pitched
        ERA = stats['ERA'] # Earned Run Average
        W = stats['Wins'] # Wins
        L = stats['Losses'] # Losses
        K = stats['Strikeouts'] # Strikeouts
        BB = stats['Walks'] # Walks
        TBF = stats['TotalBattersFaced'] # Total Batters Faced
        fStrikes = stats['FirstPitchStrikes'] # First Pitch Strikes
        fBalls = stats['FirstPitchBalls'] # First Pitch Balls
        TP = stats['TotalPitches'] # Total Pitches
        Strikes = stats['Strikes'] # Strikes
        Balls = stats['Balls'] # Balls
        HBP = stats['HitBatters'] # Number of Batters Hit
        HR = stats['HomeRuns'] # Home Runs
        FoulsAfter2Strikes = stats['FoulsAfter2Strikes'] # Fouls After 2 Strikes
        First2of3StrikesOrInPlay = stats['First2of3StrikesOrInPlay'] # First 2 of 3 Strikes or In Play
        AtBatEfficiency = stats['AtBatEfficiency'] # At Bats in Less Than 4 Pitches
        FIP = stats['FIP'] # Fielding Independent Pitching
        Swings = stats['Swings'] # Swings
        Whiffs = stats['Whiffs'] # Whiffs
        CalledStrikes = stats['CalledStrikes'] # Called Strikes
        IZSwings = stats['IZSwings'] # Swings Inside the Strike Zone
        IZWhiffs = stats['IZWhiffs'] # Whiffs Inside the Strike Zone
        IZPitches = stats['IZPitches'] # Pitches Inside the Strike Zone
        OZSwings = stats['OZSwings'] # Swings Outside the Strike Zone
        OZWhiffs = stats['OZWhiffs'] # Whiffs Outside the Strike Zone
        OZPitches = stats['OZPitches'] # Pitches Outside the Strike Zone
        Fastballs = stats['Fastballs'] # Fastballs
        Cutters = stats['Cutters'] # Cutters
        Sinkers = stats['Sinkers'] # Sinkers
        Sliders = stats['Sliders'] # Sliders
        FBnVAA = stats['FBnVAA'] # Fastball normalized Vertical Approach Angle
        FBVAAUpper = stats['FBVAAUpper'] # Fastball Vertical Approach Angle in the Upper Zone
        FBVAAMid = stats['FBVAAMid'] # Fastball Vertical Approach Angle in the Middle Zone
        FBVAALower = stats['FBVAALower'] # Fastball Vertical Approach Angle in the Lower Zone

        # Additional Stats

        Kpercent = K / TBF * 100 if TBF > 0 else 0 # Strikeout Percentage
        BBpercent = BB / TBF * 100 if TBF > 0 else 0 # Walk Percentage
        fStrikePercent = fStrikes / TBF * 100 if TBF > 0 else 0 # First Pitch Strike Percentage
        fBallPercent = fBalls / TBF * 100 if TBF > 0 else 0 # First Pitch Ball Percentage
        strikePercent = Strikes / TP * 100 if TP > 0 else 0 # Strike Percentage
        ballPercent = Balls / TP * 100 if TP > 0 else 0 # Ball Percentage
        AtBatEfficiencyPercent = AtBatEfficiency / TBF * 100 if TBF > 0 else 0 # At Bat Efficiency Percentage
        WhiffPercent = Whiffs / Swings * 100 if Swings > 0 else 0 # Whiff Percentage
        CSWPercent = (CalledStrikes + Whiffs) / TP * 100 if TP > 0 else 0 # Called Strike or Whiff Percentage
        IZWhiffPercent = IZWhiffs / IZSwings * 100 if IZSwings > 0 else 0 # Whiff Percentage Inside the Strike Zone
        ChasePercent = OZSwings / OZPitches * 100 if OZPitches > 0 else 0 # Chase Percentage

        # --------------- Display Pitching Stats --------------- #

        print(f"Pitcher: {pitcher}")
        print(f"W-L: {W}-{L}")
        print(f"Earned Runs: {earnedRuns}, Innings Pitched: {IP:.2f}, TBF: {TBF}")
        print(f"ERA: {ERA:.2f}")
        print(f"Total Pitches: {TP}")
        print(f"Strikes: {Strikes}, Balls: {Balls}, Foul Balls (0-2 Count): {FoulsAfter2Strikes}, Batters Hit By Pitch: {HBP}")
        print(f"Strike%: {strikePercent:.2f}%, Ball%: {ballPercent:.2f}%")
        print(f"F-Strikes: {fStrikes}, F-Balls: {fBalls}")
        print(f"F-Strike%: {fStrikePercent:.2f}%, F-Ball%: {fBallPercent:.2f}%")
        print(f"First 2 of 3 Strikes or In Play: {First2of3StrikesOrInPlay}")
        print(f"At Bats in Less Than 4 Pitches: {AtBatEfficiency}, At Bat Efficiency(%): {AtBatEfficiencyPercent:.2f}%")
        print(f"K: {K}, BB: {BB}, Home Runs: {HR}")
        print(f"K%: {Kpercent:.2f}%, BB%: {BBpercent:.2f}%")
        print(f"FIP: {FIP:.2f}")
        print(f"Swings: {Swings}, Whiffs: {Whiffs}, Whiff%: {WhiffPercent:.2f}%")
        print(f"Called Strikes: {CalledStrikes}, CSW%: {CSWPercent:.2f}%")
        print(f"In-Zone Swings: {IZSwings}, In-Zone Whiffs: {IZWhiffs}, IZWhiff%: {IZWhiffPercent:.2f}%")
        print(f"Out-Zone Swings: {OZSwings}, Out-Zone Pitches: {OZPitches}, Chase%: {ChasePercent:.2f}%")
        print(f"Fastballs: {Fastballs}, Cutters: {Cutters}, Sinkers: {Sinkers}, Sliders: {Sliders}")
        print(f"FB nVAA: {FBnVAA:.2f}, FB VAA Upper: {FBVAAUpper:.2f}, FB VAA Mid: {FBVAAMid:.2f}, FB VAA Lower: {FBVAALower:.2f}")
        print()

# -------------------- MAIN FUNCTION -------------------- #
if __name__ == "__main__":
    file_path = input("Enter the path to the CSV file: ")
    
    data = read_csv(file_path)
    if data is not None:
        print()
        print("File found successfully! Opening now...")
        print()
        
        pitchers, team_runs, pitcher_teams = calculate_pitching_stats(data)
        assign_wins_losses(pitchers, team_runs, pitcher_teams)
        print_pitching_stats(pitchers)
    else:
        print("Failed to read the CSV file.")