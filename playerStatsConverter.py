'''
playerStatsConverter.py

Python script that converts the stats from a CSV file into meaningful
pitcher and batter stats.

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

# Unified player stats dictionary
players = defaultdict(lambda: {"PitchingStats": {}, "BattingStats": {}})

# Function to read CSV file
def read_csv(file_path):
    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    
# Function to calculate pitching stats
def calculate_pitching_stats(data, players):

    # Dictionaries for tracking pitching stats
    pitchers = defaultdict(lambda: defaultdict(int))  # Dictionary of pitchers and their stats
    fastball_vert_appr_angles = defaultdict(list)  # Stores VertApprAngles for fastballs
    fastball_upper_zone_angles = defaultdict(list)  # Stores VertApprAngles for fastballs in the upper zone
    fastball_mid_zone_angles = defaultdict(list)  # Stores VertApprAngles for fastballs in the middle zone
    fastball_lower_zone_angles = defaultdict(list)  # Stores VertApprAngles for fastballs in the lower zone

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
        rel_speed = float(row['RelSpeed']) if 'RelSpeed' in row else 0
        induced_vert_break = float(row['InducedVertBreak']) if 'InducedVertBreak' in row else 0
        horz_break = float(row['HorzBreak']) if 'HorzBreak' in row else 0
        try: # Had to make try/except block because some spin rates were empty strings
            spin_rate = float(row['SpinRate']) if 'SpinRate' in row and row['SpinRate'].strip() else 0
        except ValueError:
            print(f"Invalid SpinRate value: {row['SpinRate']} in row: {row}")
            spin_rate = 0
        release_height = float(row['RelHeight']) if 'RelHeight' in row else 0
        extension = float(row['Extension']) if 'Extension' in row else 0

        # Initialize stats for each player in players
        if pitcher_name not in players:
            players[pitcher_name] = {"PitchingStats": {}, "BattingStats": {}}

        if "PitchingStats" not in players[pitcher_name] or not players[pitcher_name]["PitchingStats"]:
            players[pitcher_name]["PitchingStats"] = {
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
                'FBVertApprAngles': [],
                'FBnVAA': 0,
                'UpperZonePitches': 0,
                'MidZonePitches': 0,
                'LowerZonePitches': 0,
                'FBVAAUpper': 0,
                'FBVAAMid': 0,
                'FBVAALower': 0,
                # Fastball
                'Fastballs': 0,
                'FastballIZ': 0,
                'FastballIZ%': 0,
                'FastballVelo': [],
                'FastballAvgVelo': 0,
                'FastballMaxVelo': 0,
                'FastballMinVelo': 0,
                'FastballIVB': [],
                'FastballAvgIVB': 0,
                'FastballMaxIVB': 0,
                'FastballMinIVB': 0,
                'FastballHB': [],
                'FastballAvgHB': 0,
                'FastballMaxHB': 0,
                'FastballMinHB': 0,
                'FastballSpin': [],
                'FastballAvgSpin': 0,
                'FastballMaxSpin': 0,
                'FastballMinSpin': 0,
                'FastballReleaseHeight': [],
                'FastballAvgReleaseHeight': 0,
                'FastballExtension': [],
                'FastballAvgExtension': 0,
                # Cutter
                'Cutters': 0,
                'CutterIZ': 0,
                'CutterIZ%': 0,
                'CutterVelo': [],
                'CutterAvgVelo': 0,
                'CutterMaxVelo': 0,
                'CutterMinVelo': 0,
                'CutterIVB': [],
                'CutterAvgIVB': 0,
                'CutterMaxIVB': 0,
                'CutterMinIVB': 0,
                'CutterHB': [],
                'CutterAvgHB': 0,
                'CutterMaxHB': 0,
                'CutterMinHB': 0,
                'CutterSpin': [],
                'CutterAvgSpin': 0,
                'CutterMaxSpin': 0,
                'CutterMinSpin': 0,
                'CutterReleaseHeight': [],
                'CutterAvgReleaseHeight': 0,
                'CutterExtension': [],
                'CutterAvgExtension': 0,
                # Sinker
                'Sinkers': 0,
                'SinkerIZ': 0,
                'SinkerIZ%': 0,
                'SinkerVelo': [],
                'SinkerAvgVelo': 0,
                'SinkerMaxVelo': 0,
                'SinkerMinVelo': 0,
                'SinkerIVB': [],
                'SinkerAvgIVB': 0,
                'SinkerMaxIVB': 0,
                'SinkerMinIVB': 0,
                'SinkerHB': [],
                'SinkerAvgHB': 0,
                'SinkerMaxHB': 0,
                'SinkerMinHB': 0,
                'SinkerSpin': [],
                'SinkerAvgSpin': 0,
                'SinkerMaxSpin': 0,
                'SinkerMinSpin': 0,
                'SinkerReleaseHeight': [],
                'SinkAvgReleaseHeight': 0,
                'SinkerExtension': [],
                'SinkerAvgExtension': 0,
                # Slider
                'Sliders': 0,
                'SliderIZ': 0,
                'SliderIZ%': 0,
                'SliderVelo': [],
                'SliderAvgVelo': 0,
                'SliderMaxVelo': 0,
                'SliderMinVelo': 0,
                'SliderIVB': [],
                'SliderAvgIVB': 0,
                'SliderMaxIVB': 0,
                'SliderMinIVB': 0,
                'SliderHB': [],
                'SliderAvgHB': 0,
                'SliderMaxHB': 0,
                'SliderMinHB': 0,
                'SliderSpin': [],
                'SliderAvgSpin': 0,
                'SliderMaxSpin': 0,
                'SliderMinSpin': 0,
                'SliderReleaseHeight': [],
                'SliderAvgReleaseHeight': 0,
                'SliderExtension': [],
                'SliderAvgExtension': 0
            }

        if "BattingStats" not in players[pitcher_name] or not players[pitcher_name]["BattingStats"]:
            players[pitcher_name]["BattingStats"] = {
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

        # # Track total pitches thrown
        players[pitcher_name]["PitchingStats"]['TotalPitches'] += 1

        # Track total pitches thrown outside the strike zone
        if not (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
            players[pitcher_name]["PitchingStats"]['OZPitches'] += 1

        # Track total pitches thrown inside the strike zone
        if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
            STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
            players[pitcher_name]["PitchingStats"]['IZPitches'] += 1

            # Track pitches in different parts of the strike zone
            if UPPER_ZONE_MIN <= plate_loc_height <= UPPER_ZONE_MAX:
                players[pitcher_name]["PitchingStats"]['UpperZonePitches'] += 1
                if tagged_pitch_type in ['Fastball', 'FourSeamFastBall', 'TwoSeamFastBall']:
                    fastball_upper_zone_angles[pitcher_name].append(vert_appr_angle)
            elif MID_ZONE_MIN <= plate_loc_height <= MID_ZONE_MAX:
                players[pitcher_name]["PitchingStats"]['MidZonePitches'] += 1
                if tagged_pitch_type in ['Fastball', 'FourSeamFastBall', 'TwoSeamFastBall']:
                    fastball_mid_zone_angles[pitcher_name].append(vert_appr_angle)
            elif LOWER_ZONE_MIN <= plate_loc_height <= LOWER_ZONE_MAX:
                players[pitcher_name]["PitchingStats"]['LowerZonePitches'] += 1
                if tagged_pitch_type in ['Fastball', 'FourSeamFastBall', 'TwoSeamFastBall']:
                    fastball_lower_zone_angles[pitcher_name].append(vert_appr_angle)

        # ---------- Track pitch types ----------

        # Fastballs
        if tagged_pitch_type in ['Fastball', 'FourSeamFastBall', 'TwoSeamFastBall']:
            players[pitcher_name]["PitchingStats"]['Fastballs'] += 1
            players[pitcher_name]["PitchingStats"]['FBVertApprAngles'].append(vert_appr_angle)

            # Track Velocity
            if rel_speed > 0: 
                players[pitcher_name]["PitchingStats"]['FastballVelo'].append(rel_speed)
            # Track Induced Vertical Break
            if induced_vert_break != 0:
                players[pitcher_name]["PitchingStats"]['FastballIVB'].append(induced_vert_break)
            # Track Horizontal Break
            if horz_break != 0:
                players[pitcher_name]["PitchingStats"]['FastballHB'].append(horz_break)
            # Track Spin Rate
            if spin_rate > 0:
                players[pitcher_name]["PitchingStats"]['FastballSpin'].append(spin_rate)
            # Track Release Height
            if release_height > 0:
                players[pitcher_name]["PitchingStats"]['FastballReleaseHeight'].append(release_height)
            # Track Extension
            if extension != 0:
                players[pitcher_name]["PitchingStats"]['FastballExtension'].append(extension)
            # Track In-Zone Pitches
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                players[pitcher_name]["PitchingStats"]['FastballIZ'] += 1

        # Cutters
        elif tagged_pitch_type == 'Cutter':
            players[pitcher_name]["PitchingStats"]['Cutters'] += 1

            # Track Velocity
            if rel_speed > 0: 
                players[pitcher_name]["PitchingStats"]['CutterVelo'].append(rel_speed)
            # Track Induced Vertical Break
            if induced_vert_break != 0:
                players[pitcher_name]["PitchingStats"]['CutterIVB'].append(induced_vert_break)
            # Track Horizontal Break
            if horz_break != 0:
                players[pitcher_name]["PitchingStats"]['CutterHB'].append(horz_break)
            # Track Spin Rate
            if spin_rate > 0:
                players[pitcher_name]["PitchingStats"]['CutterSpin'].append(spin_rate)
            # Track Release Height
            if release_height > 0:
                players[pitcher_name]["PitchingStats"]['CutterReleaseHeight'].append(release_height)
            # Track Extension
            if extension != 0:
                players[pitcher_name]["PitchingStats"]['CutterExtension'].append(extension)
            # Track In-Zone Pitches
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                players[pitcher_name]["PitchingStats"]['CutterIZ'] += 1

        # Sinkers
        elif tagged_pitch_type == 'Sinker':
            players[pitcher_name]["PitchingStats"]['Sinkers'] += 1

            # Track Velocity
            if rel_speed > 0: 
                players[pitcher_name]["PitchingStats"]['SinkerVelo'].append(rel_speed)
            # Track Induced Vertical Break
            if induced_vert_break != 0:
                players[pitcher_name]["PitchingStats"]['SinkerIVB'].append(induced_vert_break)
            # Track Horizontal Break
            if horz_break != 0:
                players[pitcher_name]["PitchingStats"]['SinkerHB'].append(horz_break)
            # Track Spin Rate
            if spin_rate > 0:
                players[pitcher_name]["PitchingStats"]['SinkerSpin'].append(spin_rate)
            # Track Release Height
            if release_height > 0:
                players[pitcher_name]["PitchingStats"]['SinkerReleaseHeight'].append(release_height)
            # Track Extension
            if extension != 0:
                players[pitcher_name]["PitchingStats"]['SinkerExtension'].append(extension)
            # Track In-Zone Pitches
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                players[pitcher_name]["PitchingStats"]['SinkerIZ'] += 1

        # Sliders
        elif tagged_pitch_type == 'Slider':
            players[pitcher_name]["PitchingStats"]['Sliders'] += 1

            # Track Velocity
            if rel_speed > 0: 
                players[pitcher_name]["PitchingStats"]['SliderVelo'].append(rel_speed)
            # Track Induced Vertical Break
            if induced_vert_break != 0:
                players[pitcher_name]["PitchingStats"]['SliderIVB'].append(induced_vert_break)
            # Track Horizontal Break
            if horz_break != 0:
                players[pitcher_name]["PitchingStats"]['SliderHB'].append(horz_break)
            # Track Spin Rate
            if spin_rate > 0:
                players[pitcher_name]["PitchingStats"]['SliderSpin'].append(spin_rate)
            # Track Release Height
            if release_height > 0:
                players[pitcher_name]["PitchingStats"]['SliderReleaseHeight'].append(release_height)
            # Track Extension
            if extension != 0:
                players[pitcher_name]["PitchingStats"]['SliderExtension'].append(extension)
            # Track In-Zone Pitches
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                players[pitcher_name]["PitchingStats"]['SliderIZ'] += 1

        # ---------- PITCH TYPE STATS DONE ----------

        # ---------- Continuing other pitcher stats ----------

        # Track earned runs for pitchers 
        # Note: Can not track inherited runners or passed balls so this only accounts for runs excluding errors
        if row['PlayResult'] != 'Error':
            players[pitcher_name]["PitchingStats"]['EarnedRuns'] += runs_scored

        # Track outs recorded by pitchers
        players[pitcher_name]["PitchingStats"]['OutsRecorded'] += outs_on_play

        # Track strikeouts and walks for pitchers
        if korbb == 'Strikeout':
            players[pitcher_name]["PitchingStats"]['OutsRecorded'] += 1
            players[pitcher_name]["PitchingStats"]['Strikeouts'] += 1
        elif korbb == 'Walk':
            players[pitcher_name]["PitchingStats"]['Walks'] += 1

        # Track total batters faced
        if current_batter[pitcher_name] != batter_name:
            players[pitcher_name]["PitchingStats"]['TotalBattersFaced'] += 1
            current_batter[pitcher_name] = batter_name

        # Track first pitch strikes if a strike is thrown, there's a foul ball, or the ball is put in play
        if pitch_of_pa == 1 and (pitch_call == 'StrikeCalled' or 
                                 pitch_call == 'StrikeSwinging' or
                                 pitch_call == 'FoulBall' or
                                 pitch_call == 'InPlay'):
            players[pitcher_name]["PitchingStats"]['FirstPitchStrikes'] += 1

        # Track first pitch balls if a ball is thrown or if there's a hit by pitch
        if pitch_of_pa == 1 and (pitch_call == 'BallCalled' or
                                 pitch_call == 'BallinDirt' or
                                 pitch_call == 'BallIntentional' or
                                 pitch_call == 'HitByPitch'):
            players[pitcher_name]["PitchingStats"]['FirstPitchBalls'] += 1

        # Track Strikes and Balls and Fouls After 2 Strikes and Hit By Pitches
        if pitch_call in ['StrikeCalled', 'StrikeSwinging', 'InPlay']:
            players[pitcher_name]["PitchingStats"]['Strikes'] += 1
        elif pitch_call == 'FoulBall':
            if strikes < 2 or (strikes == 2 and tagged_hit_type == 'Bunt'):
                players[pitcher_name]["PitchingStats"]['Strikes'] += 1
            elif strikes == 2 and tagged_hit_type != 'Bunt':
                players[pitcher_name]["PitchingStats"]['FoulsAfter2Strikes'] += 1
        elif pitch_call in ['BallCalled', 'BallinDirt', 'BallIntentional']:
            players[pitcher_name]["PitchingStats"]['Balls'] += 1
        elif pitch_call == 'HitByPitch':
            players[pitcher_name]["PitchingStats"]['HitBatters'] += 1

        # Track Home Runs
        if play_result == 'HomeRun':
            players[pitcher_name]["PitchingStats"]['HomeRuns'] += 1

        # Track swings and whiffs
        if pitch_call in ['StrikeSwinging', 'InPlay', 'FoulBall']:
            players[pitcher_name]["PitchingStats"]['Swings'] += 1
            # Check if the pitch was inside the strike zone
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                players[pitcher_name]["PitchingStats"]['IZSwings'] += 1
            # Swing is outside strikezone
            else:
                players[pitcher_name]["PitchingStats"]['OZSwings'] += 1
        if pitch_call == 'StrikeSwinging':
            players[pitcher_name]["PitchingStats"]['Whiffs'] += 1
            # Check if the pitch was inside the strike zone
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                players[pitcher_name]["PitchingStats"]['IZWhiffs'] += 1
            # Whiff is outside strikezone
            else:
                players[pitcher_name]["PitchingStats"]['OZWhiffs'] += 1


        # Track called strikes
        if pitch_call == 'StrikeCalled':
            players[pitcher_name]["PitchingStats"]['CalledStrikes'] += 1

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
                players[pitcher_name]["PitchingStats"]['First2of3StrikesOrInPlay'] += 1
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
                players[pitcher_name]["PitchingStats"]['AtBatEfficiency'] += 1
            pitches_in_at_bat[pitcher_name][batter_name] = 0 # Reset for the next at-bat

    # --------------- Calculate additional stats outside the CSV row loop ----------------
    for pitcher_name, stats in players.items():
        pitching_stats = stats["PitchingStats"]

        # Calculate Innings Pitched
        outs_recorded = pitching_stats['OutsRecorded'] # Outs recorded
        earned_runs = pitching_stats['EarnedRuns'] # Earned runs
        innings_pitched = outs_recorded / 3 # Innings Pitched 
        pitching_stats['InningsPitched'] = innings_pitched

        # Calculate ERA
        pitching_stats['ERA'] = (9 * earned_runs / innings_pitched) if innings_pitched > 0 else 0 # ERA

        # Calculate FIP
        home_runs = pitching_stats['HomeRuns'] # Home Runs
        walks = pitching_stats['Walks'] # Walks
        hit_by_pitches = pitching_stats['HitBatters'] # Hit Batters
        strikeouts = pitching_stats['Strikeouts']
        inn_pitched = pitching_stats['InningsPitched']
        FIP_constant = 3.17 # This is a constant used from the 2024 MLB season
        if inn_pitched > 0:
            pitching_stats['FIP'] = ((13 * home_runs) + (3 * (walks + hit_by_pitches)) 
                                        - (2 * strikeouts)) / inn_pitched + FIP_constant
        else:
            pitching_stats['FIP'] = 0

        # Calculate FB nVAA (using the median, because normalizing makes the mean less useful)
        if pitching_stats['FBVertApprAngles']:
            mean_vert_appr_angle = statistics.mean(pitching_stats['FBVertApprAngles'])
            stddev_vert_appr_angle = statistics.stdev(pitching_stats['FBVertApprAngles'])
            normalized_angles = [(angle - mean_vert_appr_angle) / stddev_vert_appr_angle
                                 for angle in pitching_stats['FBVertApprAngles']]
            pitching_stats['FBnVAA'] = statistics.median(normalized_angles)
        else:
            pitching_stats['FBnVAA'] = 0

        # Calculate FB VAA for different strike zone parts (using mean bc not normalized)
        if fastball_upper_zone_angles[pitcher_name]:
            pitching_stats['FBVAAUpper'] = statistics.mean(fastball_upper_zone_angles[pitcher_name])
        else:
            pitching_stats['FBVAAUpper'] = 0

        if fastball_mid_zone_angles[pitcher_name]:
            pitching_stats['FBVAAMid'] = statistics.mean(fastball_mid_zone_angles[pitcher_name])
        else:
            pitching_stats['FBVAAMid'] = 0

        if fastball_lower_zone_angles[pitcher_name]:
            pitching_stats['FBVAALower'] = statistics.mean(fastball_lower_zone_angles[pitcher_name])
        else:
            pitching_stats['FBVAALower'] = 0

        # ---------- VELOCITY ----------

        for pitch_type in ['Fastball', 'Cutter', 'Sinker', 'Slider']:
            velo_key = f'{pitch_type}Velo'
            if pitching_stats[velo_key]:
                velocities = pitching_stats[velo_key]
                pitching_stats[f'{pitch_type}AvgVelo'] = statistics.mean(velocities)
                pitching_stats[f'{pitch_type}MaxVelo'] = max(velocities)
                pitching_stats[f'{pitch_type}MinVelo'] = min(velocities)
            else:
                pitching_stats[f'{pitch_type}AvgVelo'] = 0
                pitching_stats[f'{pitch_type}MaxVelo'] = 0
                pitching_stats[f'{pitch_type}MinVelo'] = 0

        # ---------- INDUCED VERTICAL BREAK ----------
        for pitch_type in ['Fastball', 'Cutter', 'Sinker', 'Slider']:
            ivb_key = f'{pitch_type}IVB'
            if pitching_stats[ivb_key]:
                ivbs = pitching_stats[ivb_key]
                pitching_stats[f'{pitch_type}AvgIVB'] = statistics.mean(ivbs)
                pitching_stats[f'{pitch_type}MaxIVB'] = max(ivbs)
                pitching_stats[f'{pitch_type}MinIVB'] = min(ivbs)
            else:
                pitching_stats[f'{pitch_type}AvgIVB'] = 0
                pitching_stats[f'{pitch_type}MaxIVB'] = 0
                pitching_stats[f'{pitch_type}MinIVB'] = 0

        # ---------- HORIZONTAL BREAK ----------
        for pitch_type in ['Fastball', 'Cutter', 'Sinker', 'Slider']:
            hb_key = f'{pitch_type}HB'
            if pitching_stats[hb_key]:
                hbs = pitching_stats[hb_key]
                pitching_stats[f'{pitch_type}AvgHB'] = statistics.mean(hbs)
                pitching_stats[f'{pitch_type}MaxHB'] = max(hbs)
                pitching_stats[f'{pitch_type}MinHB'] = min(hbs)
            else:
                pitching_stats[f'{pitch_type}AvgHB'] = 0
                pitching_stats[f'{pitch_type}MaxHB'] = 0
                pitching_stats[f'{pitch_type}MinHB'] = 0

        # ---------- SPIN RATE ----------
        for pitch_type in ['Fastball', 'Cutter', 'Sinker', 'Slider']:
            spin_key = f'{pitch_type}Spin'
            if pitching_stats[spin_key]:
                spins = pitching_stats[spin_key]
                pitching_stats[f'{pitch_type}AvgSpin'] = statistics.mean(spins)
                pitching_stats[f'{pitch_type}MaxSpin'] = max(spins)
                pitching_stats[f'{pitch_type}MinSpin'] = min(spins)
            else:
                pitching_stats[f'{pitch_type}AvgSpin'] = 0
                pitching_stats[f'{pitch_type}MaxSpin'] = 0
                pitching_stats[f'{pitch_type}MinSpin'] = 0

        # ---------- IN-ZONE % ----------
        for pitch_type in ['Fastball', 'Cutter', 'Sinker', 'Slider']:
            iz_key = f'{pitch_type}IZ%'
            iz_pitches_key = f'{pitch_type}IZ'
            total_pitches_key = f'{pitch_type}s'
            # DEBUG
            #print(f"Checking keys for {pitcher_name}: {iz_pitches_key}, {total_pitches_key}")
            #print(f"PitchingStats: {pitching_stats}")
            if pitching_stats[iz_pitches_key] > 0:
                pitching_stats[iz_key] = (pitching_stats[iz_pitches_key] / pitching_stats[total_pitches_key]) * 100
            else:
                pitching_stats[iz_key] = 0

        # ---------- RELEASE HEIGHT ----------
        for pitch_type in ['Fastball', 'Cutter', 'Sinker', 'Slider']:
            release_height_key = f'{pitch_type}ReleaseHeight'
            if pitching_stats[release_height_key]:
                release_heights = pitching_stats[release_height_key]
                pitching_stats[f'{pitch_type}AvgReleaseHeight'] = statistics.mean(release_heights)
            else:
                pitching_stats[f'{pitch_type}AvgReleaseHeight'] = 0

        # ---------- EXTENSION ----------
        for pitch_type in ['Fastball', 'Cutter', 'Sinker', 'Slider']:
            extension_key = f'{pitch_type}Extension'
            if pitching_stats[extension_key]:
                extensions = pitching_stats[extension_key]
                pitching_stats[f'{pitch_type}AvgExtension'] = statistics.mean(extensions)
            else:
                pitching_stats[f'{pitch_type}AvgExtension'] = 0

    return players, team_runs, pitcher_teams

# Function to assign wins and losses to pitchers
def assign_wins_losses(players, team_runs, pitcher_teams):
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
            return  # Tie = No wins or losses assigned

        for pitcher_name, team in pitcher_teams.items():
            if team == winning_team:
                players[pitcher_name]["PitchingStats"]['Wins'] += 1
            elif team == losing_team:
                players[pitcher_name]["PitchingStats"]['Losses'] += 1

# Function that prints pitching stats
def print_pitching_stats(players):
    for pitcher_name, stats in players.items():
        pitching_stats = stats["PitchingStats"]

        # ---------- Simple Pitching Stats ---------- #
        earnedRuns = pitching_stats['EarnedRuns'] # Earned Runs
        IP = pitching_stats['InningsPitched'] # Innings Pitched
        ERA = pitching_stats['ERA'] # Earned Run Average
        W = pitching_stats['Wins'] # Wins
        L = pitching_stats['Losses'] # Losses
        K = pitching_stats['Strikeouts'] # Strikeouts
        BB = pitching_stats['Walks'] # Walks
        TBF = pitching_stats['TotalBattersFaced'] # Total Batters Faced
        fStrikes = pitching_stats['FirstPitchStrikes'] # First Pitch Strikes
        fBalls = pitching_stats['FirstPitchBalls'] # First Pitch Balls
        TP = pitching_stats['TotalPitches'] # Total Pitches
        Strikes = pitching_stats['Strikes'] # Strikes
        Balls = pitching_stats['Balls'] # Balls
        HBP = pitching_stats['HitBatters'] # Number of Batters Hit
        HR = pitching_stats['HomeRuns'] # Home Runs
        FoulsAfter2Strikes = pitching_stats['FoulsAfter2Strikes'] # Fouls After 2 Strikes
        First2of3StrikesOrInPlay = pitching_stats['First2of3StrikesOrInPlay'] # First 2 of 3 Strikes or In Play
        AtBatEfficiency = pitching_stats['AtBatEfficiency'] # At Bats in Less Than 4 Pitches
        FIP = pitching_stats['FIP'] # Fielding Independent Pitching
        Swings = pitching_stats['Swings'] # Swings
        Whiffs = pitching_stats['Whiffs'] # Whiffs
        CalledStrikes = pitching_stats['CalledStrikes'] # Called Strikes
        IZSwings = pitching_stats['IZSwings'] # Swings Inside the Strike Zone
        IZWhiffs = pitching_stats['IZWhiffs'] # Whiffs Inside the Strike Zone
        IZPitches = pitching_stats['IZPitches'] # Pitches Inside the Strike Zone
        OZSwings = pitching_stats['OZSwings'] # Swings Outside the Strike Zone
        OZWhiffs = pitching_stats['OZWhiffs'] # Whiffs Outside the Strike Zone
        OZPitches = pitching_stats['OZPitches'] # Pitches Outside the Strike Zone
        Fastballs = pitching_stats['Fastballs'] # Fastball Count
        Cutters = pitching_stats['Cutters'] # Cutter Count 
        Sinkers = pitching_stats['Sinkers'] # Sinker Count
        Sliders = pitching_stats['Sliders'] # Slider Count
        FBnVAA = pitching_stats['FBnVAA'] # Fastball normalized Vertical Approach Angle
        FBVAAUpper = pitching_stats['FBVAAUpper'] # Fastball Vertical Approach Angle in the Upper Zone
        FBVAAMid = pitching_stats['FBVAAMid'] # Fastball Vertical Approach Angle in the Middle Zone
        FBVAALower = pitching_stats['FBVAALower'] # Fastball Vertical Approach Angle in the Lower Zone
        
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

        # Store calculated stats in PitchingStats dictionary
        pitching_stats['Strikeout%'] = Kpercent
        pitching_stats['Walk%'] = BBpercent
        pitching_stats['FirstPitchStrike%'] = fStrikePercent
        pitching_stats['FirstPitchBall%'] = fBallPercent
        pitching_stats['Strike%'] = strikePercent
        pitching_stats['Ball%'] = ballPercent
        pitching_stats['AtBatEfficiency%'] = AtBatEfficiencyPercent
        pitching_stats['Whiff%'] = WhiffPercent
        pitching_stats['CSW%'] = CSWPercent
        pitching_stats['IZWhiff%'] = IZWhiffPercent
        pitching_stats['Chase%'] = ChasePercent

        # Velocity Stats
        FastballAvgVelo = pitching_stats['FastballAvgVelo']
        FastballMaxVelo = pitching_stats['FastballMaxVelo']
        FastballMinVelo = pitching_stats['FastballMinVelo']
        CutterAvgVelo = pitching_stats['CutterAvgVelo']
        CutterMaxVelo = pitching_stats['CutterMaxVelo']
        CutterMinVelo = pitching_stats['CutterMinVelo']
        SinkerAvgVelo = pitching_stats['SinkerAvgVelo']
        SinkerMaxVelo = pitching_stats['SinkerMaxVelo']
        SinkerMinVelo = pitching_stats['SinkerMinVelo']
        SliderAvgVelo = pitching_stats['SliderAvgVelo']
        SliderMaxVelo = pitching_stats['SliderMaxVelo']
        SliderMinVelo = pitching_stats['SliderMinVelo']

        # Induced Vertical Break Stats
        FastballAvgIVB = pitching_stats['FastballAvgIVB']
        FastballMaxIVB = pitching_stats['FastballMaxIVB']
        FastballMinIVB = pitching_stats['FastballMinIVB']
        CutterAvgIVB = pitching_stats['CutterAvgIVB']
        CutterMaxIVB = pitching_stats['CutterMaxIVB']
        CutterMinIVB = pitching_stats['CutterMinIVB']
        SinkerAvgIVB = pitching_stats['SinkerAvgIVB']
        SinkerMaxIVB = pitching_stats['SinkerMaxIVB']
        SinkerMinIVB = pitching_stats['SinkerMinIVB']
        SliderAvgIVB = pitching_stats['SliderAvgIVB']
        SliderMaxIVB = pitching_stats['SliderMaxIVB']
        SliderMinIVB = pitching_stats['SliderMinIVB']

        # Horizontal Break Stats
        FastballAvgHB = pitching_stats['FastballAvgHB']
        FastballMaxHB = pitching_stats['FastballMaxHB']
        FastballMinHB = pitching_stats['FastballMinHB']
        CutterAvgHB = pitching_stats['CutterAvgHB']
        CutterMaxHB = pitching_stats['CutterMaxHB']
        CutterMinHB = pitching_stats['CutterMinHB']
        SinkerAvgHB = pitching_stats['SinkerAvgHB']
        SinkerMaxHB = pitching_stats['SinkerMaxHB']
        SinkerMinHB = pitching_stats['SinkerMinHB']
        SliderAvgHB = pitching_stats['SliderAvgHB']
        SliderMaxHB = pitching_stats['SliderMaxHB']
        SliderMinHB = pitching_stats['SliderMinHB']

        # Spin Rate Stats
        FastballAvgSpin = pitching_stats['FastballAvgSpin']
        FastballMaxSpin = pitching_stats['FastballMaxSpin']
        FastballMinSpin = pitching_stats['FastballMinSpin']
        CutterAvgSpin = pitching_stats['CutterAvgSpin']
        CutterMaxSpin = pitching_stats['CutterMaxSpin']
        CutterMinSpin = pitching_stats['CutterMinSpin']
        SinkerAvgSpin = pitching_stats['SinkerAvgSpin']
        SinkerMaxSpin = pitching_stats['SinkerMaxSpin']
        SinkerMinSpin = pitching_stats['SinkerMinSpin']
        SliderAvgSpin = pitching_stats['SliderAvgSpin']
        SliderMaxSpin = pitching_stats['SliderMaxSpin']
        SliderMinSpin = pitching_stats['SliderMinSpin']

        # In-Zone Percentage Stats
        FastballIZ = pitching_stats['FastballIZ']
        FastballIZPercent = pitching_stats['FastballIZ%']
        CutterIZ = pitching_stats['CutterIZ']
        CutterIZPercent = pitching_stats['CutterIZ%']
        SinkerIZ = pitching_stats['SinkerIZ']
        SinkerIZPercent = pitching_stats['SinkerIZ%']
        SliderIZ = pitching_stats['SliderIZ']
        SliderIZPercent = pitching_stats['SliderIZ%']

        # Release Height Stats
        FastballAvgReleaseHeight = pitching_stats['FastballAvgReleaseHeight']
        CutterAvgReleaseHeight = pitching_stats['CutterAvgReleaseHeight']
        SinkerAvgReleaseHeight = pitching_stats['SinkerAvgReleaseHeight']
        SliderAvgReleaseHeight = pitching_stats['SliderAvgReleaseHeight']

        # Extension Stats
        FastballAvgExtension = pitching_stats['FastballAvgExtension']
        CutterAvgExtension = pitching_stats['CutterAvgExtension']
        SinkerAvgExtension = pitching_stats['SinkerAvgExtension']
        SliderAvgExtension = pitching_stats['SliderAvgExtension']


        # --------------- Display Pitching Stats --------------- #

        print(f"~~~~~~~~~~ Pitcher: {pitcher_name} ~~~~~~~~~~")
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
        print(f"FB nVAA: {FBnVAA:.2f}, FB VAA Upper: {FBVAAUpper:.2f}, FB VAA Mid: {FBVAAMid:.2f}, FB VAA Lower: {FBVAALower:.2f}")
        # Fastball Stats
        print(f"*********************")
        print(f"Fastballs: {Fastballs}")
        print(f"Avg Velo: {FastballAvgVelo:.2f}, Max Velo: {FastballMaxVelo:.2f}, Min Velo: {FastballMinVelo:.2f}")
        print(f"Avg IVB: {FastballAvgIVB:.2f}, Max IVB: {FastballMaxIVB:.2f}, Min IVB: {FastballMinIVB:.2f}")
        print(f"Avg HB: {FastballAvgHB:.2f}, Max HB: {FastballMaxHB:.2f}, Min HB: {FastballMinHB:.2f}")
        print(f"Avg Spin: {FastballAvgSpin:.2f}, Max Spin: {FastballMaxSpin:.2f}, Min Spin: {FastballMinSpin:.2f}")
        print(f"In-Zone: {FastballIZ}, In-Zone%: {FastballIZPercent:.2f}%")
        print(f"Avg Release Height: {FastballAvgReleaseHeight:.2f}, Avg Extension: {FastballAvgExtension:.2f}")
        print(f"*********************")
        # Cutter Stats
        print(f"Cutters: {Cutters}")
        print(f"Avg Velo: {CutterAvgVelo:.2f}, Max Velo: {CutterMaxVelo:.2f}, Min Velo: {CutterMinVelo:.2f}")
        print(f"Avg IVB: {CutterAvgIVB:.2f}, Max IVB: {CutterMaxIVB:.2f}, Min IVB: {CutterMinIVB:.2f}")
        print(f"Avg HB: {CutterAvgHB:.2f}, Max HB: {CutterMaxHB:.2f}, Min HB: {CutterMinHB:.2f}")
        print(f"Avg Spin: {CutterAvgSpin:.2f}, Max Spin: {CutterMaxSpin:.2f}, Min Spin: {CutterMinSpin:.2f}")
        print(f"In-Zone: {CutterIZ}, In-Zone%: {CutterIZPercent:.2f}%")
        print(f"Avg Release Height: {CutterAvgReleaseHeight:.2f}, Avg Extension: {CutterAvgExtension:.2f}")
        print(f"*********************")
        #Sinker Stats
        print(f"Sinkers: {Sinkers}")
        print(f"Avg Velo: {SinkerAvgVelo:.2f}, Max Velo: {SinkerMaxVelo:.2f}, Min Velo: {SinkerMinVelo:.2f}")
        print(f"Avg IVB: {SinkerAvgIVB:.2f}, Max IVB: {SinkerMaxIVB:.2f}, Min IVB: {SinkerMinIVB:.2f}")
        print(f"Avg HB: {SinkerAvgHB:.2f}, Max HB: {SinkerMaxHB:.2f}, Min HB: {SinkerMinHB:.2f}")
        print(f"Avg Spin: {SinkerAvgSpin:.2f}, Max Spin: {SinkerMaxSpin:.2f}, Min Spin: {SinkerMinSpin:.2f}")
        print(f"In-Zone: {SinkerIZ}, In-Zone%: {SinkerIZPercent:.2f}%")
        print(f"Avg Release Height: {SinkerAvgReleaseHeight:.2f}, Avg Extension: {SinkerAvgExtension:.2f}")
        print(f"*********************")
        # Slider Stats
        print(f"Sliders: {Sliders}")
        print(f"Avg Velo: {SliderAvgVelo:.2f}, Max Velo: {SliderMaxVelo:.2f}, Min Velo: {SliderMinVelo:.2f}")
        print(f"Avg IVB: {SliderAvgIVB:.2f}, Max IVB: {SliderMaxIVB:.2f}, Min IVB: {SliderMinIVB:.2f}")
        print(f"Avg HB: {SliderAvgHB:.2f}, Max HB: {SliderMaxHB:.2f}, Min HB: {SliderMinHB:.2f}")
        print(f"Avg Spin: {SliderAvgSpin:.2f}, Max Spin: {SliderMaxSpin:.2f}, Min Spin: {SliderMinSpin:.2f}")
        print(f"In-Zone: {SliderIZ}, In-Zone%: {SliderIZPercent:.2f}%")
        print(f"Avg Release Height: {SliderAvgReleaseHeight:.2f}, Avg Extension: {SliderAvgExtension:.2f}")
        print()

# Function to calculate hitting stats
def calculate_hitting_stats(data, players):
    plate_appearances = set()

    # Iterate through the data
    for row in data: 
        game_id = row['GameID']
        batter_name = row['Batter']
        play_result = row['PlayResult']
        hit_type = row['TaggedHitType']
        korbb = row['KorBB']
        pitch_call = row['PitchCall']
        runs_scored = int(row['RunsScored']) if 'RunsScored' in row else 0
        outs_on_play = int(row['OutsOnPlay']) if 'OutsOnPlay' in row else 0
        pa_of_inning = row['PAofInning']
        inning = row['Inning']
        inning_half = row['Top/Bottom']

        # Safely convert exit speed and launch angle to float
        try:
            exit_speed = float(row['ExitSpeed']) if 'ExitSpeed' in row else 0
        except ValueError:
            exit_speed = 0

        try:
            launch_angle = float(row['Angle']) if 'Angle' in row else 0
        except ValueError:
            launch_angle = 0

        # Initialize stats for each batter in players
        if batter_name not in players:
            players[batter_name] = {"PitchingStats": {}, "BattingStats": {}}

        # Initialize stats for each batter in players
        if "BattingStats" not in players[batter_name] or not players[batter_name]["BattingStats"]:
            players[batter_name]["BattingStats"] = {
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
                'AvgExitVelocity': 0,
                'AvgLaunchAngle': 0
            }
        
        if "PitchingStats" not in players[batter_name] or not players[batter_name]["PitchingStats"]:
            players[batter_name]["PitchingStats"] = {
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
                'FBVertApprAngles': [],
                'FBnVAA': 0,
                'UpperZonePitches': 0,
                'MidZonePitches': 0,
                'LowerZonePitches': 0,
                'FBVAAUpper': 0,
                'FBVAAMid': 0,
                'FBVAALower': 0,
                # Fastball
                'Fastballs': 0,
                'FastballIZ': 0,
                'FastballIZ%': 0,
                'FastballVelo': [],
                'FastballAvgVelo': 0,
                'FastballMaxVelo': 0,
                'FastballMinVelo': 0,
                'FastballIVB': [],
                'FastballAvgIVB': 0,
                'FastballMaxIVB': 0,
                'FastballMinIVB': 0,
                'FastballHB': [],
                'FastballAvgHB': 0,
                'FastballMaxHB': 0,
                'FastballMinHB': 0,
                'FastballSpin': [],
                'FastballAvgSpin': 0,
                'FastballMaxSpin': 0,
                'FastballMinSpin': 0,
                'FastballReleaseHeight': [],
                'FastballAvgReleaseHeight': 0,
                'FastballExtension': [],
                'FastballAvgExtension': 0,
                # Cutter
                'Cutters': 0,
                'CutterIZ': 0,
                'CutterIZ%': 0,
                'CutterVelo': [],
                'CutterAvgVelo': 0,
                'CutterMaxVelo': 0,
                'CutterMinVelo': 0,
                'CutterIVB': [],
                'CutterAvgIVB': 0,
                'CutterMaxIVB': 0,
                'CutterMinIVB': 0,
                'CutterHB': [],
                'CutterAvgHB': 0,
                'CutterMaxHB': 0,
                'CutterMinHB': 0,
                'CutterSpin': [],
                'CutterAvgSpin': 0,
                'CutterMaxSpin': 0,
                'CutterMinSpin': 0,
                'CutterReleaseHeight': [],
                'CutterAvgReleaseHeight': 0,
                'CutterExtension': [],
                'CutterAvgExtension': 0,
                # Sinker
                'Sinkers': 0,
                'SinkerIZ': 0,
                'SinkerIZ%': 0,
                'SinkerVelo': [],
                'SinkerAvgVelo': 0,
                'SinkerMaxVelo': 0,
                'SinkerMinVelo': 0,
                'SinkerIVB': [],
                'SinkerAvgIVB': 0,
                'SinkerMaxIVB': 0,
                'SinkerMinIVB': 0,
                'SinkerHB': [],
                'SinkerAvgHB': 0,
                'SinkerMaxHB': 0,
                'SinkerMinHB': 0,
                'SinkerSpin': [],
                'SinkerAvgSpin': 0,
                'SinkerMaxSpin': 0,
                'SinkerMinSpin': 0,
                'SinkerReleaseHeight': [],
                'SinkAvgReleaseHeight': 0,
                'SinkerExtension': [],
                'SinkerAvgExtension': 0,
                # Slider
                'Sliders': 0,
                'SliderIZ': 0,
                'SliderIZ%': 0,
                'SliderVelo': [],
                'SliderAvgVelo': 0,
                'SliderMaxVelo': 0,
                'SliderMinVelo': 0,
                'SliderIVB': [],
                'SliderAvgIVB': 0,
                'SliderMaxIVB': 0,
                'SliderMinIVB': 0,
                'SliderHB': [],
                'SliderAvgHB': 0,
                'SliderMaxHB': 0,
                'SliderMinHB': 0,
                'SliderSpin': [],
                'SliderAvgSpin': 0,
                'SliderMaxSpin': 0,
                'SliderMinSpin': 0,
                'SliderReleaseHeight': [],
                'SliderAvgReleaseHeight': 0,
                'SliderExtension': [],
                'SliderAvgExtension': 0
            }

        batting_stats = players[batter_name]["BattingStats"]

        # Append exit speed and launch angle to the batter's list to get avgs.
        if exit_speed != 0:
            batting_stats['ExitSpeeds'].append(exit_speed)
        if launch_angle != 0:
            batting_stats['Angles'].append(launch_angle)

        # Create a unique identifier for each batter's plate appearance
        pa_identifier = (game_id, batter_name, inning, inning_half, pa_of_inning)

        # Check if this is a new plate appearance
        if pa_identifier not in plate_appearances:
            plate_appearances.add(pa_identifier)
            batting_stats['PA'] += 1

        # Plays and correlated stats
        if play_result == 'Single':
            batting_stats['1B'] += 1 # Single
            batting_stats['H'] += 1 # Hit
            batting_stats['TB'] += 1 # Total Bases
        elif play_result == 'Double':
            batting_stats['2B'] += 1 # Double
            batting_stats['H'] += 1
            batting_stats['TB'] += 2
        elif play_result == 'Triple':
            batting_stats['3B'] += 1 # Triple
            batting_stats['H'] += 1
            batting_stats['TB'] += 3
        elif play_result == 'HomeRun':
            batting_stats['HR'] += 1 # Home Run
            batting_stats['H'] += 1 
            batting_stats['TB'] += 4 
        elif play_result == 'Sacrifice':
            if hit_type == 'Bunt':
                batting_stats['SH'] += 1
            elif hit_type in ['FlyBall', 'Popup']: 
                batting_stats['SF'] += 1

        if korbb == 'Strikeout':
            batting_stats['K'] += 1 # Strikeout
            batting_stats['AB'] += 1 # Strikeout counts as AB
        elif korbb == 'Walk':
            batting_stats['BB'] += 1 # Walk

        if pitch_call == 'HitByPitch':
            batting_stats['HBP'] += 1 # Hit By Pitch
        
        # Increment AB based on definition
        # AB = Batter reaches base via fielder's choice, hit, or error,
        # or non-sacrifice out.
        if play_result in ['Single', 'Double', 'Triple', 'HomeRun', 'Error',
                     'FieldersChoice', 'Out'] and play_result != 'Sacrifice':
            batting_stats['AB'] += 1

        # Increment RBI based on the definition
        # RBI = Result of PA is run scored, excluding errors and ground double plays
        if play_result not in ['Error', 'FieldersChoice'] and not (play_result == 'Out' and hit_type == 'GroundBall' and outs_on_play == 2):
            batting_stats['RBI'] += runs_scored
        elif play_result == 'Sacrifice':
            batting_stats['RBI'] += runs_scored # Sacrifice fly or hit
        if korbb == 'Walk' and runs_scored > 0:
            batting_stats['RBI'] += runs_scored # Bases-loaded walk
        if pitch_call == 'HitByPitch' and runs_scored > 0:
            batting_stats['RBI'] += runs_scored # Bases-loaded hit by pitch

        # Check for Ground into Double Play (GDP)
        if play_result == 'Out' and hit_type == 'GroundBall' and outs_on_play == 2:
            batting_stats['GDP'] += 1 # Ground into Double Play

        # Calculate Average Exit Velocity and Average Launch Angle for each batter
        for batter_name, stats in players.items():
            batting_stats = stats["BattingStats"]

            exit_speeds = batting_stats['ExitSpeeds']
            angles = batting_stats['Angles']
            
            avg_exit_velocity = sum(exit_speeds) / len(exit_speeds) if exit_speeds else 0
            avg_launch_angle = sum(angles) / len(angles) if angles else 0
            
            batting_stats['AvgExitVelocity'] = avg_exit_velocity
            batting_stats['AvgLaunchAngle'] = avg_launch_angle

    return players

# Function that prints pitching stats
def print_hitting_stats(players):
    for batter_name, stats in players.items():
        batting_stats = stats["BattingStats"]

        # ---------- Simple Hitting Stats ---------- #
        PA = batting_stats['PA'] # Plate Appearances
        AB = batting_stats['AB'] # At Bats
        H = batting_stats['H'] # Hits
        K = batting_stats['K'] # Strikeouts
        BB = batting_stats['BB'] # Walks
        HBP = batting_stats['HBP'] # Hit By Pitch
        SH = batting_stats['SH'] # Sacrifice Hits
        SF = batting_stats['SF'] # Sacrifice Flies
        TB = batting_stats['TB'] # Total Bases
        oneB = batting_stats['1B'] # Singles
        twoB = batting_stats['2B'] # Doubles
        threeB = batting_stats['3B'] # Triples
        HR = batting_stats['HR'] # Home Runs
        RBI = batting_stats['RBI'] # Runs Batted In
        GDP = batting_stats['GDP'] # Ground into Double Play
        
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
        
        # Store calculated stats in BattingStats dictionary
        batting_stats['AVG'] = AVG
        batting_stats['BB%'] = BBpercent
        batting_stats['K%'] = Kpercent
        batting_stats['OBP'] = OBP
        batting_stats['SLG'] = SLG
        batting_stats['OPS'] = OPS
        batting_stats['ISO'] = ISO
        batting_stats['BABIP'] = BABIP
        batting_stats['wOBA'] = wOBA

        # --------------- Display Hitting Stats ---------------#
        print(f"Batter: {batter_name}")
        print(f"PA: {PA}, AB: {AB}, H: {H}, TB: {TB}")
        print(f"1B: {oneB}, 2B: {twoB}, 3B: {threeB}, HR: {HR}")
        print(f"RBI: {RBI}, BB: {BB}, K: {K}, HBP: {HBP}, SF: {SF}, SH: {SH}, GDP: {GDP}")
        print(f"AVG: {AVG:.2f}, BB%: {BBpercent:.2f}%, K%: {Kpercent:.2f}%")
        print(f"OBP: {OBP:.2f}, SLG: {SLG:.2f}, OPS: {OPS:.2f}, ISO: {ISO:.2f}, BABIP: {BABIP:.2f}, wOBA: {wOBA:.2f}")
        print(f"Avg Exit Velocity: {batting_stats['AvgExitVelocity']:.2f} MPH, Avg Launch Angle: {batting_stats['AvgLaunchAngle']:.2f} degrees")
        print()

# Function that generates a CSV file with the players' stats
def generate_csv(players, output_file):
    # Define specific headers for pitching and batting stats
    headers = [
        "PlayerName",  # Player's name
        # Pitching Stats
        "W-L", "EarnedRuns", "InningsPitched", "TBF", "ERA", "TotalPitches",
        "Strikes", "Balls", "FoulsAfter2Strikes", "HitBatters", "Strike%", "Ball%",
        "FirstPitchStrikes", "FirstPitchBalls", "FirstPitchStrike%", "FirstPitchBall%",
        "First2of3StrikesOrInPlay", "AtBatEfficiency", "AtBatEfficiency%", "Strikeouts",
        "Walks", "HomeRuns", "Strikeout%", "Walk%", "FIP", "Swings", "Whiffs", "Whiff%",
        "CalledStrikes", "CSW%", "InZoneSwings", "InZoneWhiffs", "IZWhiff%", "OutZoneSwings",
        "OutZonePitches", "Chase%", "FBnVAA", "FBVAAUpper", "FBVAAMid", "FBVAALower",
        # Fastball Stats
        "Fastballs", "FastballAvgVelo", "FastballMaxVelo", "FastballMinVelo", "FastballAvgIVB",
        "FastballMaxIVB", "FastballMinIVB", "FastballAvgHB", "FastballMaxHB", "FastballMinHB",
        "FastballAvgSpin", "FastballMaxSpin", "FastballMinSpin", "FastballInZone", "FastballInZone%",
        "FastballAvgReleaseHeight", "FastballAvgExtension", 
        # Cutter Stats
        "Cutters", "CutterAvgVelo", "CutterMaxVelo", "CutterMinVelo", "CutterAvgIVB",
        "CutterMaxIVB", "CutterMinIVB", "CutterAvgHB", "CutterMaxHB", "CutterMinHB",
        "CutterAvgSpin", "CutterMaxSpin", "CutterMinSpin", "CutterInZone", "CutterInZone%",
        "CutterAvgReleaseHeight", "CutterAvgExtension",
        # Sinker Stats
        "Sinkers", "SinkerAvgVelo", "SinkerMaxVelo", "SinkerMinVelo", "SinkerAvgIVB",
        "SinkerMaxIVB", "SinkerMinIVB", "SinkerAvgHB", "SinkerMaxHB", "SinkerMinHB",
        "SinkerAvgSpin", "SinkerMaxSpin", "SinkerMinSpin", "SinkerInZone", "SinkerInZone%",
        "SinkerAvgReleaseHeight", "SinkerAvgExtension",
        # Slider Stats
        "Sliders", "SliderAvgVelo", "SliderMaxVelo", "SliderMinVelo", "SliderAvgIVB",
        "SliderMaxIVB", "SliderMinIVB", "SliderAvgHB", "SliderMaxHB", "SliderMinHB",
        "SliderAvgSpin", "SliderMaxSpin", "SliderMinSpin", "SliderInZone", "SliderInZone%",
        "SliderAvgReleaseHeight", "SliderAvgExtension",
        # Batting Stats
        "PA", "AB", "H", "TB", "1B", "2B", "3B", "HR", "RBI", "BB", "K", "HBP",
        "SF", "SH", "GDP", "AVG", "BB%", "K%", "OBP", "SLG", "OPS", "ISO", "BABIP", "wOBA",
        "AvgExitVelocity", "AvgLaunchAngle"
    ]

    # Write the data to the CSV file
    with open(output_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()  # Write the header row

        for player_name, stats in players.items():
            row = {"PlayerName": player_name}

            # Add pitching stats
            pitching_stats = stats["PitchingStats"]
            row.update({
                "W-L": f"{pitching_stats.get('Wins', 0)}-{pitching_stats.get('Losses', 0)}",
                "EarnedRuns": pitching_stats.get("EarnedRuns", 0),
                "InningsPitched": pitching_stats.get("InningsPitched", 0),
                "TBF": pitching_stats.get("TotalBattersFaced", 0),
                "ERA": pitching_stats.get("ERA", 0),
                "TotalPitches": pitching_stats.get("TotalPitches", 0),
                "Strikes": pitching_stats.get("Strikes", 0),
                "Balls": pitching_stats.get("Balls", 0),
                "FoulsAfter2Strikes": pitching_stats.get("FoulsAfter2Strikes", 0),
                "HitBatters": pitching_stats.get("HitBatters", 0),
                "Strike%": pitching_stats.get("Strike%", 0),
                "Ball%": pitching_stats.get("Ball%", 0),
                "FirstPitchStrikes": pitching_stats.get("FirstPitchStrikes", 0),
                "FirstPitchBalls": pitching_stats.get("FirstPitchBalls", 0),
                "FirstPitchStrike%": pitching_stats.get("FirstPitchStrike%", 0),
                "FirstPitchBall%": pitching_stats.get("FirstPitchBall%", 0),
                "First2of3StrikesOrInPlay": pitching_stats.get("First2of3StrikesOrInPlay", 0),
                "AtBatEfficiency": pitching_stats.get("AtBatEfficiency", 0),
                "AtBatEfficiency%": pitching_stats.get("AtBatEfficiency%", 0),
                "Strikeouts": pitching_stats.get("Strikeouts", 0),
                "Walks": pitching_stats.get("Walks", 0),
                "HomeRuns": pitching_stats.get("HomeRuns", 0),
                "Strikeout%": pitching_stats.get("Strikeout%", 0),
                "Walk%": pitching_stats.get("Walk%", 0),
                "FIP": pitching_stats.get("FIP", 0),
                "Swings": pitching_stats.get("Swings", 0),
                "Whiffs": pitching_stats.get("Whiffs", 0),
                "Whiff%": pitching_stats.get("Whiff%", 0),
                "CalledStrikes": pitching_stats.get("CalledStrikes", 0),
                "CSW%": pitching_stats.get("CSW%", 0),
                "InZoneSwings": pitching_stats.get("IZSwings", 0),
                "InZoneWhiffs": pitching_stats.get("IZWhiffs", 0),
                "IZWhiff%": pitching_stats.get("IZWhiff%", 0),
                "OutZoneSwings": pitching_stats.get("OZSwings", 0),
                "OutZonePitches": pitching_stats.get("OZPitches", 0),
                "Chase%": pitching_stats.get("Chase%", 0),
                "FBnVAA": pitching_stats.get("FBnVAA", 0),
                "FBVAAUpper": pitching_stats.get("FBVAAUpper", 0),
                "FBVAAMid": pitching_stats.get("FBVAAMid", 0),
                "FBVAALower": pitching_stats.get("FBVAALower", 0),
                "Fastballs": pitching_stats.get("Fastballs", 0),
                "FastballAvgVelo": pitching_stats.get("FastballAvgVelo", 0),
                "FastballMaxVelo": pitching_stats.get("FastballMaxVelo", 0),
                "FastballMinVelo": pitching_stats.get("FastballMinVelo", 0),
                "FastballAvgIVB": pitching_stats.get("FastballAvgIVB", 0),
                "FastballMaxIVB": pitching_stats.get("FastballMaxIVB", 0),
                "FastballMinIVB": pitching_stats.get("FastballMinIVB", 0),
                "FastballAvgHB": pitching_stats.get("FastballAvgHB", 0),
                "FastballMaxHB": pitching_stats.get("FastballMaxHB", 0),
                "FastballMinHB": pitching_stats.get("FastballMinHB", 0),
                "FastballAvgSpin": pitching_stats.get("FastballAvgSpin", 0),
                "FastballMaxSpin": pitching_stats.get("FastballMaxSpin", 0),
                "FastballMinSpin": pitching_stats.get("FastballMinSpin", 0),
                "FastballInZone": pitching_stats.get("FastballIZ", 0),
                "FastballInZone%": pitching_stats.get("FastballIZ%", 0),
                "FastballAvgReleaseHeight": pitching_stats.get("FastballAvgReleaseHeight", 0),
                "FastballAvgExtension": pitching_stats.get("FastballAvgExtension", 0),
                "Cutters": pitching_stats.get("Cutters", 0),
                "CutterAvgVelo": pitching_stats.get("CutterAvgVelo", 0),
                "CutterMaxVelo": pitching_stats.get("CutterMaxVelo", 0),
                "CutterMinVelo": pitching_stats.get("CutterMinVelo", 0),
                "CutterAvgIVB": pitching_stats.get("CutterAvgIVB", 0),
                "CutterMaxIVB": pitching_stats.get("CutterMaxIVB", 0),
                "CutterMinIVB": pitching_stats.get("CutterMinIVB", 0),
                "CutterAvgHB": pitching_stats.get("CutterAvgHB", 0),
                "CutterMaxHB": pitching_stats.get("CutterMaxHB", 0),
                "CutterMinHB": pitching_stats.get("CutterMinHB", 0),
                "CutterAvgSpin": pitching_stats.get("CutterAvgSpin", 0),
                "CutterMaxSpin": pitching_stats.get("CutterMaxSpin", 0),
                "CutterMinSpin": pitching_stats.get("CutterMinSpin", 0),
                "CutterInZone": pitching_stats.get("CutterIZ", 0),
                "CutterInZone%": pitching_stats.get("CutterIZ%", 0),
                "CutterAvgReleaseHeight": pitching_stats.get("CutterAvgReleaseHeight", 0),
                "CutterAvgExtension": pitching_stats.get("CutterAvgExtension", 0),
                "Sinkers": pitching_stats.get("Sinkers", 0),
                "SinkerAvgVelo": pitching_stats.get("SinkerAvgVelo", 0),
                "SinkerMaxVelo": pitching_stats.get("SinkerMaxVelo", 0),
                "SinkerMinVelo": pitching_stats.get("SinkerMinVelo", 0),
                "SinkerAvgIVB": pitching_stats.get("SinkerAvgIVB", 0),
                "SinkerMaxIVB": pitching_stats.get("SinkerMaxIVB", 0),
                "SinkerMinIVB": pitching_stats.get("SinkerMinIVB", 0),
                "SinkerAvgHB": pitching_stats.get("SinkerAvgHB", 0),
                "SinkerMaxHB": pitching_stats.get("SinkerMaxHB", 0),
                "SinkerMinHB": pitching_stats.get("SinkerMinHB", 0),
                "SinkerAvgSpin": pitching_stats.get("SinkerAvgSpin", 0),
                "SinkerMaxSpin": pitching_stats.get("SinkerMaxSpin", 0),
                "SinkerMinSpin": pitching_stats.get("SinkerMinSpin", 0),
                "SinkerInZone": pitching_stats.get("SinkerIZ", 0),
                "SinkerInZone%": pitching_stats.get("SinkerIZ%", 0),
                "SinkerAvgReleaseHeight": pitching_stats.get("SinkerAvgReleaseHeight", 0),
                "SinkerAvgExtension": pitching_stats.get("SinkerAvgExtension", 0),
                "Sliders": pitching_stats.get("Sliders", 0),
                "SliderAvgVelo": pitching_stats.get("SliderAvgVelo", 0),
                "SliderMaxVelo": pitching_stats.get("SliderMaxVelo", 0),
                "SliderMinVelo": pitching_stats.get("SliderMinVelo", 0),
                "SliderAvgIVB": pitching_stats.get("SliderAvgIVB", 0),
                "SliderMaxIVB": pitching_stats.get("SliderMaxIVB", 0),
                "SliderMinIVB": pitching_stats.get("SliderMinIVB", 0),
                "SliderAvgHB": pitching_stats.get("SliderAvgHB", 0),
                "SliderMaxHB": pitching_stats.get("SliderMaxHB", 0),
                "SliderMinHB": pitching_stats.get("SliderMinHB", 0),
                "SliderAvgSpin": pitching_stats.get("SliderAvgSpin", 0),
                "SliderMaxSpin": pitching_stats.get("SliderMaxSpin", 0),
                "SliderMinSpin": pitching_stats.get("SliderMinSpin", 0),
                "SliderInZone": pitching_stats.get("SliderIZ", 0),
                "SliderInZone%": pitching_stats.get("SliderIZ%", 0),
                "SliderAvgReleaseHeight": pitching_stats.get("SliderAvgReleaseHeight", 0),
                "SliderAvgExtension": pitching_stats.get("SliderAvgExtension", 0),
            })

            # Add batting stats
            batting_stats = stats["BattingStats"]
            row.update({
                "PA": batting_stats.get("PA", 0),
                "AB": batting_stats.get("AB", 0),
                "H": batting_stats.get("H", 0),
                "TB": batting_stats.get("TB", 0),
                "1B": batting_stats.get("1B", 0),
                "2B": batting_stats.get("2B", 0),
                "3B": batting_stats.get("3B", 0),
                "HR": batting_stats.get("HR", 0),
                "RBI": batting_stats.get("RBI", 0),
                "BB": batting_stats.get("BB", 0),
                "K": batting_stats.get("K", 0),
                "HBP": batting_stats.get("HBP", 0),
                "SF": batting_stats.get("SF", 0),
                "SH": batting_stats.get("SH", 0),
                "GDP": batting_stats.get("GDP", 0),
                "AVG": batting_stats.get("AVG", 0),
                "BB%": batting_stats.get("BB%", 0),
                "K%": batting_stats.get("K%", 0),
                "OBP": batting_stats.get("OBP", 0),
                "SLG": batting_stats.get("SLG", 0),
                "OPS": batting_stats.get("OPS", 0),
                "ISO": batting_stats.get("ISO", 0),
                "BABIP": batting_stats.get("BABIP", 0),
                "wOBA": batting_stats.get("wOBA", 0),
                "AvgExitVelocity": batting_stats.get("AvgExitVelocity", 0),
                "AvgLaunchAngle": batting_stats.get("AvgLaunchAngle", 0),
            })

            writer.writerow(row)

    print(f"CSV file '{output_file}' generated successfully!")
# -------------------- MAIN FUNCTION -------------------- #
if __name__ == "__main__":
    file_path = input("Enter the path to the CSV file: ")
    
    # Read the CSV file and process the data
    data = read_csv(file_path)
    if data is not None:
        print()
        print("File found successfully! Opening now...")
        print()

        # Extract GameID from first row of dataset
        game_id = data[0]['GameID'] if 'GameID' in data[0] else "unknown_game"
        output_file = f"{game_id}_player_stats.csv" # Use GameID to name output file

        # ----- PITCHING STATS ----- #

        # Calculate pitching stats
        players, team_runs, pitcher_teams = calculate_pitching_stats(data, players)
        # DEBUG
        #print("Players after calculate_pitching_stats:")
        #for player, stats in players.items():
            #print(f"{player}: {stats}")

        # Assign wins and losses
        assign_wins_losses(players, team_runs, pitcher_teams)
        # Print pitching stats
        print_pitching_stats(players)

        # ----- HITTING STATS ----- #

        # Calculate hitting stats
        players = calculate_hitting_stats(data, players)
        # DEBUG
        #print("Players after calculate_hitting_stats:")
        #for player, stats in players.items():
            #print(f"{player}: {stats}")

        # Print hitting stats
        print_hitting_stats(players)

        # ----- GENERATE CSV ----- #
        generate_csv(players, output_file)
        
    else:
        print("Failed to read the CSV file.")
    
