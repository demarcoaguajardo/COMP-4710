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
    
def safe_float(value):
    try:
        return float(value) if value.strip() else 0.0
    except (ValueError, AttributeError):
        return 0.0

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
        plate_loc_side = safe_float(row['PlateLocSide']) if 'PlateLocSide' in row else 0
        plate_loc_height = safe_float (row['PlateLocHeight']) if 'PlateLocHeight' in row else 0
        tagged_pitch_type = row['TaggedPitchType']
        vert_appr_angle = safe_float(row['VertApprAngle']) if 'VertApprAngle' in row else 0
        rel_speed = safe_float(row['RelSpeed']) if 'RelSpeed' in row else 0
        induced_vert_break = safe_float(row['InducedVertBreak']) if 'InducedVertBreak' in row else 0
        horz_break = safe_float(row['HorzBreak']) if 'HorzBreak' in row else 0
        try: # Had to make try/except block because some spin rates were empty strings
            spin_rate = safe_float(row['SpinRate']) if 'SpinRate' in row and row['SpinRate'].strip() else 0
        except ValueError:
            print(f"Invalid SpinRate value: {row['SpinRate']} in row: {row}")
            spin_rate = 0
        release_height = safe_float(row['RelHeight']) if 'RelHeight' in row else 0
        extension = safe_float(row['Extension']) if 'Extension' in row else 0

        # pitch_location_confidence = row['PitchLocationConfidence'] if 'PitchLocationConfidence' in row else 0

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
                'FastballsIZ': 0,
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
                'CuttersIZ': 0,
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
                'SinkersIZ': 0,
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
                'SlidersIZ': 0,
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

        # ---------- Track pitch types ----------


        # Fastballs
        if tagged_pitch_type in ['Fastball', 'FourSeamFastBall', 'TwoSeamFastBall']:
            pitchers[pitcher_name]['Fastballs'] += 1
            pitchers[pitcher_name]['FBVertApprAngles'].append(vert_appr_angle)
            fastball_vert_appr_anngles[pitcher_name].append(vert_appr_angle)

            # Track Velocity
            if rel_speed > 0: 
                pitchers[pitcher_name]['FastballVelo'].append(rel_speed)
            # Track Induced Vertical Break
            if induced_vert_break != 0:
                pitchers[pitcher_name]['FastballIVB'].append(induced_vert_break)
            # Track Horizontal Break
            if horz_break != 0:
                pitchers[pitcher_name]['FastballHB'].append(horz_break)
            # Track Spin Rate
            if spin_rate > 0:
                pitchers[pitcher_name]['FastballSpin'].append(spin_rate)
            # Track Release Height
            if release_height > 0:
                pitchers[pitcher_name]['FastballReleaseHeight'].append(release_height)
            # Track Extension
            if extension != 0:
                pitchers[pitcher_name]['FastballExtension'].append(extension)
            # Track In-Zone Pitches
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                pitchers[pitcher_name]['FastballsIZ'] += 1

        # Cutters
        elif tagged_pitch_type == 'Cutter':
            pitchers[pitcher_name]['Cutters'] += 1

            # Track Velocity
            if rel_speed > 0: 
                pitchers[pitcher_name]['CutterVelo'].append(rel_speed)
            # Track Induced Vertical Break
            if induced_vert_break != 0:
                pitchers[pitcher_name]['CutterIVB'].append(induced_vert_break)
            # Track Horizontal Break
            if horz_break != 0:
                pitchers[pitcher_name]['CutterHB'].append(horz_break)
            # Track Spin Rate
            if spin_rate > 0:
                pitchers[pitcher_name]['CutterSpin'].append(spin_rate)
            # Track Release Height
            if release_height > 0:
                pitchers[pitcher_name]['CutterReleaseHeight'].append(release_height)
            # Track Extension
            if extension != 0:
                pitchers[pitcher_name]['CutterExtension'].append(extension)
            # Track In-Zone Pitches
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                pitchers[pitcher_name]['CuttersIZ'] += 1

        # Sinkers
        elif tagged_pitch_type == 'Sinker':
            pitchers[pitcher_name]['Sinkers'] += 1

            # Track Velocity
            if rel_speed > 0: 
                pitchers[pitcher_name]['SinkerVelo'].append(rel_speed)
            # Track Induced Vertical Break
            if induced_vert_break != 0:
                pitchers[pitcher_name]['SinkerIVB'].append(induced_vert_break)
            # Track Horizontal Break
            if horz_break != 0:
                pitchers[pitcher_name]['SinkerHB'].append(horz_break)
            # Track Spin Rate
            if spin_rate > 0:
                pitchers[pitcher_name]['SinkerSpin'].append(spin_rate)
            # Track Release Height
            if release_height > 0:
                pitchers[pitcher_name]['SinkerReleaseHeight'].append(release_height)
            # Track Extension
            if extension != 0:
                pitchers[pitcher_name]['SinkerExtension'].append(extension)
            # Track In-Zone Pitches
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                pitchers[pitcher_name]['SinkersIZ'] += 1

        # Sliders
        elif tagged_pitch_type == 'Slider':
            pitchers[pitcher_name]['Sliders'] += 1

            # Track Velocity
            if rel_speed > 0: 
                pitchers[pitcher_name]['SliderVelo'].append(rel_speed)
            # Track Induced Vertical Break
            if induced_vert_break != 0:
                pitchers[pitcher_name]['SliderIVB'].append(induced_vert_break)
            # Track Horizontal Break
            if horz_break != 0:
                pitchers[pitcher_name]['SliderHB'].append(horz_break)
            # Track Spin Rate
            if spin_rate > 0:
                pitchers[pitcher_name]['SliderSpin'].append(spin_rate)
            # Track Release Height
            if release_height > 0:
                pitchers[pitcher_name]['SliderReleaseHeight'].append(release_height)
            # Track Extension
            if extension != 0:
                pitchers[pitcher_name]['SliderExtension'].append(extension)
            # Track In-Zone Pitches
            if (STRIKE_ZONE['side_min'] <= plate_loc_side <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= plate_loc_height <= STRIKE_ZONE['height_max']):
                pitchers[pitcher_name]['SlidersIZ'] += 1


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
        if len(fastball_vert_appr_anngles[pitcher]) >= 2:
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

        # Calculate FB VAA for different strike zone parts (using mean bc not normalized)
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
        # print(f"Pitcher: {pitcher}")
        # print(f"Upper Zone Pitches: {pitchers[pitcher]['UpperZonePitches']}, Mid Zone Pitches: {pitchers[pitcher]['MidZonePitches']}, Lower Zone Pitches: {pitchers[pitcher]['LowerZonePitches']}")
        # print(f"Upper Zone VertApprAngles: {fastball_upper_zone_angles[pitcher]}")
        # print(f"Mid Zone VertApprAngles: {fastball_mid_zone_angles[pitcher]}")
        # print(f"Lower Zone VertApprAngles: {fastball_lower_zone_angles[pitcher]}")
        # print(f"FB VAA Upper: {pitchers[pitcher]['FBVAAUpper']:.2f}, FB VAA Mid: {pitchers[pitcher]['FBVAAMid']:.2f}, FB VAA Lower: {pitchers[pitcher]['FBVAALower']:.2f}")
        # print()

        # ---------- VELOCITY ----------

        # Calculate Fastball Velocity stats
        if pitchers[pitcher]['FastballVelo']:
            velocities = pitchers[pitcher]['FastballVelo']
            pitchers[pitcher]['FastballAvgVelo'] = statistics.mean(velocities)
            pitchers[pitcher]['FastballMaxVelo'] = max(velocities)
            pitchers[pitcher]['FastballMinVelo'] = min(velocities)
        else:
            pitchers[pitcher]['FastballAvgVelo'] = 0
            pitchers[pitcher]['FastballMaxVelo'] = 0
            pitchers[pitcher]['FastballMinVelo'] = 0
        # Calculate Cutter Velocity stats
        if pitchers[pitcher]['CutterVelo']:
            velocities = pitchers[pitcher]['CutterVelo']
            pitchers[pitcher]['CutterAvgVelo'] = statistics.mean(velocities)
            pitchers[pitcher]['CutterMaxVelo'] = max(velocities)
            pitchers[pitcher]['CutterMinVelo'] = min(velocities)
        else:
            pitchers[pitcher]['CutterAvgVelo'] = 0
            pitchers[pitcher]['CutterMaxVelo'] = 0
            pitchers[pitcher]['CutterMinVelo'] = 0
        # Calculate Sinker Velocity stats
        if pitchers[pitcher]['SinkerVelo']:
            velocities = pitchers[pitcher]['SinkerVelo']
            pitchers[pitcher]['SinkerAvgVelo'] = statistics.mean(velocities)
            pitchers[pitcher]['SinkerMaxVelo'] = max(velocities)
            pitchers[pitcher]['SinkerMinVelo'] = min(velocities)
        else:
            pitchers[pitcher]['SinkerAvgVelo'] = 0
            pitchers[pitcher]['SinkerMaxVelo'] = 0
            pitchers[pitcher]['SinkerMinVelo'] = 0
        # Calculate Slider Velocity stats
        if pitchers[pitcher]['SliderVelo']:
            velocities = pitchers[pitcher]['SliderVelo']
            pitchers[pitcher]['SliderAvgVelo'] = statistics.mean(velocities)
            pitchers[pitcher]['SliderMaxVelo'] = max(velocities)
            pitchers[pitcher]['SliderMinVelo'] = min(velocities)
        else:
            pitchers[pitcher]['SliderAvgVelo'] = 0
            pitchers[pitcher]['SliderMaxVelo'] = 0
            pitchers[pitcher]['SliderMinVelo'] = 0

        # ---------- INDUCED VERTICAL BREAK ----------

        # Calculate Fastball IVB stats
        if pitchers[pitcher]['FastballIVB']:
            ivbs = pitchers[pitcher]['FastballIVB']
            pitchers[pitcher]['FastballAvgIVB'] = statistics.mean(ivbs)
            pitchers[pitcher]['FastballMaxIVB'] = max(ivbs)
            pitchers[pitcher]['FastballMinIVB'] = min(ivbs)
        else: 
            pitchers[pitcher]['FastballAvgIVB'] = 0
            pitchers[pitcher]['FastballMaxIVB'] = 0
            pitchers[pitcher]['FastballMinIVB'] = 0
        # Calculate Cutter IVB stats
        if pitchers[pitcher]['CutterIVB']:
            ivbs = pitchers[pitcher]['CutterIVB']
            pitchers[pitcher]['CutterAvgIVB'] = statistics.mean(ivbs)
            pitchers[pitcher]['CutterMaxIVB'] = max(ivbs)
            pitchers[pitcher]['CutterMinIVB'] = min(ivbs)
        else:
            pitchers[pitcher]['CutterAvgIVB'] = 0
            pitchers[pitcher]['CutterMaxIVB'] = 0
            pitchers[pitcher]['CutterMinIVB'] = 0
        # Calculate Sinker IVB stats
        if pitchers[pitcher]['SinkerIVB']:
            ivbs = pitchers[pitcher]['SinkerIVB']
            pitchers[pitcher]['SinkerAvgIVB'] = statistics.mean(ivbs)
            pitchers[pitcher]['SinkerMaxIVB'] = max(ivbs)
            pitchers[pitcher]['SinkerMinIVB'] = min(ivbs)
        else:
            pitchers[pitcher]['SinkerAvgIVB'] = 0
            pitchers[pitcher]['SinkerMaxIVB'] = 0
            pitchers[pitcher]['SinkerMinIVB'] = 0
        # Calculate Slider IVB stats
        if pitchers[pitcher]['SliderIVB']:
            ivbs = pitchers[pitcher]['SliderIVB']
            pitchers[pitcher]['SliderAvgIVB'] = statistics.mean(ivbs)
            pitchers[pitcher]['SliderMaxIVB'] = max(ivbs)
            pitchers[pitcher]['SliderMinIVB'] = min(ivbs)
        else:
            pitchers[pitcher]['SliderAvgIVB'] = 0
            pitchers[pitcher]['SliderMaxIVB'] = 0
            pitchers[pitcher]['SliderMinIVB'] = 0

        # ---------- HORIZONTAL BREAK ----------

        # Calculate Fastball HB stats
        if pitchers[pitcher]['FastballHB']:
            hbs = pitchers[pitcher]['FastballHB']
            pitchers[pitcher]['FastballAvgHB'] = statistics.mean(hbs)
            pitchers[pitcher]['FastballMaxHB'] = max(hbs)
            pitchers[pitcher]['FastballMinHB'] = min(hbs)
        else:
            pitchers[pitcher]['FastballAvgHB'] = 0
            pitchers[pitcher]['FastballMaxHB'] = 0
            pitchers[pitcher]['FastballMinHB'] = 0

        # Calculate Cutter HB stats
        if pitchers[pitcher]['CutterHB']:
            hbs = pitchers[pitcher]['CutterHB']
            pitchers[pitcher]['CutterAvgHB'] = statistics.mean(hbs)
            pitchers[pitcher]['CutterMaxHB'] = max(hbs)
            pitchers[pitcher]['CutterMinHB'] = min(hbs)
        else:
            pitchers[pitcher]['CutterAvgHB'] = 0
            pitchers[pitcher]['CutterMaxHB'] = 0   
            pitchers[pitcher]['CutterMinHB'] = 0

        # Calculate Sinker HB stats
        if pitchers[pitcher]['SinkerHB']:
            hbs = pitchers[pitcher]['SinkerHB']
            pitchers[pitcher]['SinkerAvgHB'] = statistics.mean(hbs)
            pitchers[pitcher]['SinkerMaxHB'] = max(hbs)
            pitchers[pitcher]['SinkerMinHB'] = min(hbs)
        else:
            pitchers[pitcher]['SinkerAvgHB'] = 0
            pitchers[pitcher]['SinkerMaxHB'] = 0
            pitchers[pitcher]['SinkerMinHB'] = 0

        # Calculate Slider HB stats
        if pitchers[pitcher]['SliderHB']:
            hbs = pitchers[pitcher]['SliderHB']
            pitchers[pitcher]['SliderAvgHB'] = statistics.mean(hbs)
            pitchers[pitcher]['SliderMaxHB'] = max(hbs)
            pitchers[pitcher]['SliderMinHB'] = min(hbs)
        else:
            pitchers[pitcher]['SliderAvgHB'] = 0
            pitchers[pitcher]['SliderMaxHB'] = 0
            pitchers[pitcher]['SliderMinHB'] = 0

        # ---------- SPIN RATE ----------

        # Calculate Fastball Spin stats
        if pitchers[pitcher]['FastballSpin']:
            spins = pitchers[pitcher]['FastballSpin']
            pitchers[pitcher]['FastballAvgSpin'] = statistics.mean(spins)
            pitchers[pitcher]['FastballMaxSpin'] = max(spins)
            pitchers[pitcher]['FastballMinSpin'] = min(spins)
        else:
            pitchers[pitcher]['FastballAvgSpin'] = 0
            pitchers[pitcher]['FastballMaxSpin'] = 0
            pitchers[pitcher]['FastballMinSpin'] = 0

        # Calculate Cutter Spin stats
        if pitchers[pitcher]['CutterSpin']:
            spins = pitchers[pitcher]['CutterSpin']
            pitchers[pitcher]['CutterAvgSpin'] = statistics.mean(spins)
            pitchers[pitcher]['CutterMaxSpin'] = max(spins)
            pitchers[pitcher]['CutterMinSpin'] = min(spins)
        else:
            pitchers[pitcher]['CutterAvgSpin'] = 0
            pitchers[pitcher]['CutterMaxSpin'] = 0
            pitchers[pitcher]['CutterMinSpin'] = 0

        # Calculate Sinker Spin stats
        if pitchers[pitcher]['SinkerSpin']:
            spins = pitchers[pitcher]['SinkerSpin']
            pitchers[pitcher]['SinkerAvgSpin'] = statistics.mean(spins)
            pitchers[pitcher]['SinkerMaxSpin'] = max(spins)
            pitchers[pitcher]['SinkerMinSpin'] = min(spins)
        else:
            pitchers[pitcher]['SinkerAvgSpin'] = 0
            pitchers[pitcher]['SinkerMaxSpin'] = 0
            pitchers[pitcher]['SinkerMinSpin'] = 0

        # Calculate Slider Spin stats
        if pitchers[pitcher]['SliderSpin']:
            spins = pitchers[pitcher]['SliderSpin']
            pitchers[pitcher]['SliderAvgSpin'] = statistics.mean(spins)
            pitchers[pitcher]['SliderMaxSpin'] = max(spins)
            pitchers[pitcher]['SliderMinSpin'] = min(spins)
        else:
            pitchers[pitcher]['SliderAvgSpin'] = 0
            pitchers[pitcher]['SliderMaxSpin'] = 0
            pitchers[pitcher]['SliderMinSpin'] = 0


        # ---------- IN-ZONE % ----------

        # Calculate Fastball In-Zone% stats
        if pitchers[pitcher]['FastballsIZ'] > 0:
            pitchers[pitcher]['FastballIZ%'] = (pitchers[pitcher]['FastballsIZ'] / pitchers[pitcher]['Fastballs']) * 100
        else:
            pitchers[pitcher]['FastballIZ%'] = 0

        # Calculate Cutter In-Zone% stats
        if pitchers[pitcher]['CuttersIZ'] > 0:
            pitchers[pitcher]['CutterIZ%'] = (pitchers[pitcher]['CuttersIZ'] / pitchers[pitcher]['Cutters']) * 100
        else:
            pitchers[pitcher]['CutterIZ%'] = 0

        # Calculate Sinker In-Zone% stats
        if pitchers[pitcher]['SinkersIZ'] > 0:
            pitchers[pitcher]['SinkerIZ%'] = (pitchers[pitcher]['SinkersIZ'] / pitchers[pitcher]['Sinkers']) * 100
        else:
            pitchers[pitcher]['SinkerIZ%'] = 0

        # Calculate Slider In-Zone% stats
        if pitchers[pitcher]['SlidersIZ'] > 0:
            pitchers[pitcher]['SliderIZ%'] = (pitchers[pitcher]['SlidersIZ'] / pitchers[pitcher]['Sliders']) * 100
        else:
            pitchers[pitcher]['SliderIZ%'] = 0


        # ---------- RELEASE HEIGHT ----------

        # Calculate Fastball Release Height stats
        if pitchers[pitcher]['FastballReleaseHeight']:
            release_heights = pitchers[pitcher]['FastballReleaseHeight']
            pitchers[pitcher]['FastballAvgReleaseHeight'] = statistics.mean(release_heights)
        else:
            pitchers[pitcher]['FastballAvgReleaseHeight'] = 0

        # Calculate Cutter Release Height stats
        if pitchers[pitcher]['CutterReleaseHeight']:
            release_heights = pitchers[pitcher]['CutterReleaseHeight']
            pitchers[pitcher]['CutterAvgReleaseHeight'] = statistics.mean(release_heights)
        else:
            pitchers[pitcher]['CutterAvgReleaseHeight'] = 0

        # Calculate Sinker Release Height stats
        if pitchers[pitcher]['SinkerReleaseHeight']:
            release_heights = pitchers[pitcher]['SinkerReleaseHeight']
            pitchers[pitcher]['SinkerAvgReleaseHeight'] = statistics.mean(release_heights)
        else:
            pitchers[pitcher]['SinkerAvgReleaseHeight'] = 0

        # Calculate Slider Release Height stats
        if pitchers[pitcher]['SliderReleaseHeight']:
            release_heights = pitchers[pitcher]['SliderReleaseHeight']
            pitchers[pitcher]['SliderAvgReleaseHeight'] = statistics.mean(release_heights)
        else:
            pitchers[pitcher]['SliderAvgReleaseHeight'] = 0


        # ---------- EXTENSION ----------

        # Calculate Fastball Extension stats
        if pitchers[pitcher]['FastballExtension']:
            extensions = pitchers[pitcher]['FastballExtension']
            pitchers[pitcher]['FastballAvgExtension'] = statistics.mean(extensions)
        else:
            pitchers[pitcher]['FastballAvgExtension'] = 0

        # Calculate Cutter Extension stats
        if pitchers[pitcher]['CutterExtension']:
            extensions = pitchers[pitcher]['CutterExtension']
            pitchers[pitcher]['CutterAvgExtension'] = statistics.mean(extensions)
        else:
            pitchers[pitcher]['CutterAvgExtension'] = 0

        # Calculate Sinker Extension stats
        if pitchers[pitcher]['SinkerExtension']:
            extensions = pitchers[pitcher]['SinkerExtension']
            pitchers[pitcher]['SinkerAvgExtension'] = statistics.mean(extensions)
        else:
            pitchers[pitcher]['SinkerAvgExtension'] = 0

        # Calculate Slider Extension stats
        if pitchers[pitcher]['SliderExtension']:
            extensions = pitchers[pitcher]['SliderExtension']
            pitchers[pitcher]['SliderAvgExtension'] = statistics.mean(extensions)
        else:
            pitchers[pitcher]['SliderAvgExtension'] = 0

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

        # ---------- Simple Pitching Stats ---------- #

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
        Fastballs = stats['Fastballs'] # Fastball Count
        Cutters = stats['Cutters'] # Cutter Count 
        Sinkers = stats['Sinkers'] # Sinker Count
        Sliders = stats['Sliders'] # Slider Count
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

        # Velocity Stats
        FastballAvgVelo = stats['FastballAvgVelo']
        FastballMaxVelo = stats['FastballMaxVelo']
        FastballMinVelo = stats['FastballMinVelo']
        CutterAvgVelo = stats['CutterAvgVelo']
        CutterMaxVelo = stats['CutterMaxVelo']
        CutterMinVelo = stats['CutterMinVelo']
        SinkerAvgVelo = stats['SinkerAvgVelo']
        SinkerMaxVelo = stats['SinkerMaxVelo']
        SinkerMinVelo = stats['SinkerMinVelo']
        SliderAvgVelo = stats['SliderAvgVelo']
        SliderMaxVelo = stats['SliderMaxVelo']
        SliderMinVelo = stats['SliderMinVelo']

        # Induced Vertical Break Stats
        FastballAvgIVB = stats['FastballAvgIVB']
        FastballMaxIVB = stats['FastballMaxIVB']
        FastballMinIVB = stats['FastballMinIVB']
        CutterAvgIVB = stats['CutterAvgIVB']
        CutterMaxIVB = stats['CutterMaxIVB']
        CutterMinIVB = stats['CutterMinIVB']
        SinkerAvgIVB = stats['SinkerAvgIVB']
        SinkerMaxIVB = stats['SinkerMaxIVB']
        SinkerMinIVB = stats['SinkerMinIVB']
        SliderAvgIVB = stats['SliderAvgIVB']
        SliderMaxIVB = stats['SliderMaxIVB']
        SliderMinIVB = stats['SliderMinIVB']

        # Horizontal Break Stats
        FastballAvgHB = stats['FastballAvgHB']
        FastballMaxHB = stats['FastballMaxHB']
        FastballMinHB = stats['FastballMinHB']
        CutterAvgHB = stats['CutterAvgHB']
        CutterMaxHB = stats['CutterMaxHB']
        CutterMinHB = stats['CutterMinHB']
        SinkerAvgHB = stats['SinkerAvgHB']
        SinkerMaxHB = stats['SinkerMaxHB']
        SinkerMinHB = stats['SinkerMinHB']
        SliderAvgHB = stats['SliderAvgHB']
        SliderMaxHB = stats['SliderMaxHB']
        SliderMinHB = stats['SliderMinHB']

        # Spin Rate Stats
        FastballAvgSpin = stats['FastballAvgSpin']
        FastballMaxSpin = stats['FastballMaxSpin']
        FastballMinSpin = stats['FastballMinSpin']
        CutterAvgSpin = stats['CutterAvgSpin']
        CutterMaxSpin = stats['CutterMaxSpin']
        CutterMinSpin = stats['CutterMinSpin']
        SinkerAvgSpin = stats['SinkerAvgSpin']
        SinkerMaxSpin = stats['SinkerMaxSpin']
        SinkerMinSpin = stats['SinkerMinSpin']
        SliderAvgSpin = stats['SliderAvgSpin']
        SliderMaxSpin = stats['SliderMaxSpin']
        SliderMinSpin = stats['SliderMinSpin']

        # In-Zone Percentage Stats
        FastballsIZ = stats['FastballsIZ']
        FastballIZPercent = stats['FastballIZ%']
        CuttersIZ = stats['CuttersIZ']
        CutterIZPercent = stats['CutterIZ%']
        SinkersIZ = stats['SinkersIZ']
        SinkerIZPercent = stats['SinkerIZ%']
        SlidersIZ = stats['SlidersIZ']
        SliderIZPercent = stats['SliderIZ%']

        # Release Height Stats
        FastballAvgReleaseHeight = stats['FastballAvgReleaseHeight']
        CutterAvgReleaseHeight = stats['CutterAvgReleaseHeight']
        SinkerAvgReleaseHeight = stats['SinkerAvgReleaseHeight']
        SliderAvgReleaseHeight = stats['SliderAvgReleaseHeight']

        # Extension Stats
        FastballAvgExtension = stats['FastballAvgExtension']
        CutterAvgExtension = stats['CutterAvgExtension']
        SinkerAvgExtension = stats['SinkerAvgExtension']
        SliderAvgExtension = stats['SliderAvgExtension']

        # --------------- Display Pitching Stats --------------- #

        print(f"~~~~~~~~~~ Pitcher: {pitcher} ~~~~~~~~~~")
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
        print(f"In-Zone: {FastballsIZ}, In-Zone%: {FastballIZPercent:.2f}%")
        print(f"Avg Release Height: {FastballAvgReleaseHeight:.2f}, Avg Extension: {FastballAvgExtension:.2f}")
        print(f"*********************")
        # Cutter Stats
        print(f"Cutters: {Cutters}")
        print(f"Avg Velo: {CutterAvgVelo:.2f}, Max Velo: {CutterMaxVelo:.2f}, Min Velo: {CutterMinVelo:.2f}")
        print(f"Avg IVB: {CutterAvgIVB:.2f}, Max IVB: {CutterMaxIVB:.2f}, Min IVB: {CutterMinIVB:.2f}")
        print(f"Avg HB: {CutterAvgHB:.2f}, Max HB: {CutterMaxHB:.2f}, Min HB: {CutterMinHB:.2f}")
        print(f"Avg Spin: {CutterAvgSpin:.2f}, Max Spin: {CutterMaxSpin:.2f}, Min Spin: {CutterMinSpin:.2f}")
        print(f"In-Zone: {CuttersIZ}, In-Zone%: {CutterIZPercent:.2f}%")
        print(f"Avg Release Height: {CutterAvgReleaseHeight:.2f}, Avg Extension: {CutterAvgExtension:.2f}")
        print(f"*********************")
        #Sinker Stats
        print(f"Sinkers: {Sinkers}")
        print(f"Avg Velo: {SinkerAvgVelo:.2f}, Max Velo: {SinkerMaxVelo:.2f}, Min Velo: {SinkerMinVelo:.2f}")
        print(f"Avg IVB: {SinkerAvgIVB:.2f}, Max IVB: {SinkerMaxIVB:.2f}, Min IVB: {SinkerMinIVB:.2f}")
        print(f"Avg HB: {SinkerAvgHB:.2f}, Max HB: {SinkerMaxHB:.2f}, Min HB: {SinkerMinHB:.2f}")
        print(f"Avg Spin: {SinkerAvgSpin:.2f}, Max Spin: {SinkerMaxSpin:.2f}, Min Spin: {SinkerMinSpin:.2f}")
        print(f"In-Zone: {SinkersIZ}, In-Zone%: {SinkerIZPercent:.2f}%")
        print(f"Avg Release Height: {SinkerAvgReleaseHeight:.2f}, Avg Extension: {SinkerAvgExtension:.2f}")
        print(f"*********************")
        # Slider Stats
        print(f"Sliders: {Sliders}")
        print(f"Avg Velo: {SliderAvgVelo:.2f}, Max Velo: {SliderMaxVelo:.2f}, Min Velo: {SliderMinVelo:.2f}")
        print(f"Avg IVB: {SliderAvgIVB:.2f}, Max IVB: {SliderMaxIVB:.2f}, Min IVB: {SliderMinIVB:.2f}")
        print(f"Avg HB: {SliderAvgHB:.2f}, Max HB: {SliderMaxHB:.2f}, Min HB: {SliderMinHB:.2f}")
        print(f"Avg Spin: {SliderAvgSpin:.2f}, Max Spin: {SliderMaxSpin:.2f}, Min Spin: {SliderMinSpin:.2f}")
        print(f"In-Zone: {SlidersIZ}, In-Zone%: {SliderIZPercent:.2f}%")
        print(f"Avg Release Height: {SliderAvgReleaseHeight:.2f}, Avg Extension: {SliderAvgExtension:.2f}")
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