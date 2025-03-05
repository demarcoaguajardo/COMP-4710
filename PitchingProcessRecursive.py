'''
pitchingStatsConverter.py

Python script that converts the stats from multiple CSV files in a directory
and all its subdirectories into meaningful pitcher stats and outputs the 
results to a new CSV file.

Author: Demarco Guajardo
Modified: William Bingham
'''

# Imports
import csv
import os
import glob
from collections import defaultdict
# Define the names of the team constants
# Currently organized in old conference alignments
team_names = {
    #ACC
    'LOU_CAR' : 'Louisville',
    'NOT_IRI' : 'Notre Dame',
    'WAK_DEA' : 'Wake Forest',
    'FLO_SEM' : 'Florida State',
    'NOR_WOL' : 'NC State',
    'CLE_TIG' : 'Clemson',
    'BOC_EAG' : 'Boston College',
    'MIA_HUR' : 'Miami (FL)',
    'VIR_TEC' : 'Virginia Tech',
    'VIR_CAV' : 'Virginia',
    'NOR_TAR' : 'North Carolina',
    'GIT_YEL' : 'Georgia Tech',
    'PIT_PAN' : 'Pittsburgh',
    'DUK_BLU' : 'Duke',

    #Big12
    'TCU_HFG' : 'TCU',
    'OKL_COW' : 'Oklahoma State',
    'OKL_SOO' : 'Oklahoma',
    'TEX_RAI' : 'Texas Tech',
    'TEX_LON' : 'Texas',
    'WES_MOU' : 'West Virginia',
    'KAN_WIL' : 'Kansas State',
    'BAY_BEA' : 'Baylor',
    'KAN_JAY' : 'Kansas',

    #Big10
    'MAR_TER' : 'Maryland',
    'RUT_SCA' : 'Rutgers',
    'IOW_HAW' : 'Iowa',
    'ILL_ILL' : 'Illinois',
    'MIC_WOL' : 'Michigan',
    'PEN_NIT' : 'Penn State',
    'PUR_BOI' : 'Purdue',
    'NOR_CAT' : 'Northwestern',
    'IU' : 'Indiana',
    'NEB' : 'Nebraska',
    'OSU_BUC' : 'Ohio State',
    'MIC_SPA' : 'Michigan State',
    'MIN_GOL' : 'Minnesota',

    #PAC-12
    'STA_CAR' : 'Stanford',
    'OSU_BEA' : 'Oregon State',
    'UCLA' : 'UCLA',
    'ORE_DUC' : 'Oregon',
    'ARI_WIL' : 'Arizona',
    'WAS_HUS' : 'Washington',
    'CAL_BEA' : 'California',
    'ARI_SUN' : 'Arizona State',
    'WAS_COU' : 'Washington State',
    'UTA_UTE' : 'Utah',
    'SOU_TRO' : 'Southern California',

    #SEC
    'TEN_VOL' : 'Tennessee',
    'FLA_GAT' : 'Florida',
    'GEO_BUL' : 'Georgia',
    'VAN_COM' : 'Vanderbilt',
    'SOU_GAM' : 'South Carolina',
    'KEN_WIL' : 'Kentucky',
    'MIZ_TIG' : 'Missouri',
    'TEX_AGG' : 'Texas A&M',
    'ARK_RAZ' : 'Arkansas',
    'LSU_TIG' : 'LSU',
    'AUB_TIG' : 'Auburn',
    'OLE_REB' : 'Ole Miss',
    'ALA_CRI' : 'Alabama',
    'MSU_BDG' : 'Mississippi State',

    #AAC
    'UCF_KNI' : 'UCF',
    'CIN_BEA' : 'Cincinnati',
    'ECU_PIR' : 'East Carolina',
    'HOU_COU' : 'Houston',
    'MEM_TIG' : 'Memphis',
    'USF_BUL' : 'USF',
    'TUL_GRE' : 'Tulane',
    'WIC_SHO' : 'Wichita State',

    #Big South
    'CAM_CAM' : 'Campbell',
    'USC_UPS' : 'USC Upstate',
    'NCA_BUL' : 'UNC Asheville',
    'HIG_PAN' : 'High Point',
    'CHA_BUC' : 'Charleston Southern',
    'GAR_RUN' : 'Gardner-Webb',
    'WIN_EAG' : 'Winthrop',
    'LON_LAN' : 'Longwood',
    'PRE_BLH' : 'Presbyterian',
    'RAD_HIG' : 'Radford',
    'NOR_AGG' : 'N.C. A&T',

    # Coastal Athletic Association
    'COL_CHA' : 'College of Charleston',
    'HOF_PRI' : 'Hofstra',
    'UNC_SEA' : 'UNCW',
    'WM_TRI' : 'William & Mary',
    'MON_HAW' : 'Monmouth',
    'NOR_HUS' : 'Northeastern',
    'ELO_PHO' : 'Elon',
    'DEL_BLU' : 'Delaware',
    'SBU_SEA' : 'Stony Brook',
    'TOW_TIG' : 'Towson',

    # Conference USA
    'LOU_BUL' : 'Lousiana Tech',
    'UTS_ROA' : 'UTSA',
    'CHA_FOR' : 'Charlotte',
    'MTSU_BLU' : 'Middle Tennessee',
    'UAB_BLA' : 'UAB',
    'Rice' : 'RIC_OWL',
    'FLO_PAN' : 'FIU',
    'DAL_PAT' : 'DBU',
    'WES_HIL' : 'Western Kentucky',

    # American East Conference
    'UMASS_RIV' : 'UMass Lowell',
    'ALB_GRE' : 'UAlbany',
    'NJI_HIG' : 'NJIT',
    'BIN_BEA' : 'Binghamton',
    'UMBC_RET' : 'UMBC',
    'BRY_BUL' : 'Bryant',

    # Atlantic Sun Conference
    'LIB_FLA' : 'Liberty',
    'KEN_OWL' : 'Kennesaw State',
    'FGCU' : 'FGCU',
    'JUD' : 'Jacksonville',
    'STE_HAT' : 'Stetson',
    'EKU_COL' : 'Eastern Kentucky',
    'LIP_BIS' : 'Lipscomb',
    'JAC_GAM' : 'Jacksonville State',
    'CEN_BEA' : 'Central Arkansas',
    'BEL_KNI' : 'Bellarmine',
    'ALA_LIO' : 'North Alabama',
    'QUN_RYL' : 'Queens',

    # Atlantic 10 Conference
    'DAV_WIL' : 'Davidson',
    'VCU_RAM' : 'VCU',
    'RHO_RAM' : 'Rhode Island',
    'GEO_PAT' : 'George Mason',
    'STJ_HAW' : 'Saint Josephs',
    'RIC_SPI' : 'Richmond',
    'DAY_FLY' : 'Dayton',
    'GEO_COL' : 'George Washington',
    'FOR_RAM' : 'Fordham',
    'UMA_AMH' : 'Massachusetts',
    'STB_BON' : 'St. Bonaventure',

    # Big East
    'CRE_BLU' : 'Creighton',
    'XAV_MUS' : 'Xavier',
    'GEO_HOY' : 'Georgetown',
    'VIL_WIL' : 'Villanova',
    'STJ_RED' : 'St. Johns (NY)',
    'SET_PIR' : 'Seton Hall',
    'BUT_BUL' : 'Butler',

    # Big West
    'SAN_GAU' : 'UC Santa Barbara',
    'CAL_MUS' : 'Cal Poly',
    'HAW_WAR' : 'Hawaii',
    'CAL_MAT' : 'CSUN',
    'LON_DIR' : 'Long Beach State',
    'CAL_ANT' : 'UC Irvine',
    'CAL_FUL' : 'Cal State Fullerton',
    'CSU_BAK' : 'CSU Bakersfield',
    'CAL_AGO' : 'UC Davis',
    'CAL_HIG' : 'UC Riverside',

    # Horizon League
    'WRI_RAI' : 'Wright State',
    'OAK_GOL' : 'Oakland',
    'PUR_FOR' : 'Purdue Fort Wayne',
    'YSU_PEN' : 'Youngstown State',
    'NOK_NOR' : 'Northern Kentucky',

    # The Ivy League
    'PEN_QUA' : 'Penn',
    'COL_LION' : 'Columbia',
    'DAR_GRE' : 'Dartmouth',
    'YAL_BUL' : 'Yale',
    'BRO_BEA' : 'Brown',
    'COR_BRE' : 'Cornell',
    'PRI_TIG' : 'Princeton',

    # Metro Atlantic Athletic Conference
    'FAI_STA' : 'Fairfield',
    'MAR_RED' : 'Marist',
    'MSM_MTN' : 'Mount St. Marys',
    'CAN_GRI' : 'Canisius',
    'NIA_EAG' : 'Niagara',
    'RID_BRO' : 'Ridger',
    'MAN_JAS' : 'Manhattan',
    'QUI_BOB' : 'Quinnipiac',
    'SIE_SAI' : 'Siena',
    'SPU_PEA' : 'Saint Peters',
    'ION_GAE' : 'Iona',

    # Mid-American Conference
    'BAL_CAR' : 'Ball State',
    'CEN_MIC' : 'Central Michigan',
    'TOL_ROC' : 'Toledo',
    'OHI_BOB' : 'Ohio',
    'MIA_RED' : 'Miami (OH)',
    'EMU_EAG' : 'Eastern Michigan',
    'WMI_BRO' : 'Western Michigan',
    'BGS_FAL' : 'Bowling Green',
    'NIU_HUS' : 'Northern Illinois',
    'AKR_ZIP' : 'Akron'

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
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return None

def calculate_pitching_stats(data):
    pitchers = defaultdict(lambda: defaultdict(int))

    team_runs = defaultdict(int) # Tracks runs scored by each team
    pitcher_teams = defaultdict(str) # Tracks team of each pitcher
    current_batter = defaultdict(str) # Tracks unique batters faced by each pitcher
    first_three_pitches = defaultdict(lambda: defaultdict(list)) # Tracks first three pitches of each PA
    pitches_in_at_bat = defaultdict(lambda: defaultdict(int)) # Tracks pitches thrown in each at-bat

    # Iterate through the data
    for row in data:
        # Safely get values from row with defaults if keys don't exist
        game_id = row.get('GameID', '')
        pitcher_name = row.get('Pitcher', '')
        batter_name = row.get('Batter', '')
        runs_scored = int(row.get('RunsScored', 0)) if row.get('RunsScored', '') else 0
        outs_on_play = int(row.get('OutsOnPlay', 0)) if row.get('OutsOnPlay', '') else 0
        korbb = row.get('KorBB', '')
        pitcher_team = row.get('PitcherTeam', '')
        batter_team = row.get('BatterTeam', '')
        pitch_of_pa = int(row.get('PitchofPA', 0)) if row.get('PitchofPA', '') else 0
        pitch_call = row.get('PitchCall', '')
        strikes = int(row.get('Strikes', 0)) if row.get('Strikes', '') else 0
        balls = int(row.get('Balls', 0)) if row.get('Balls', '') else 0
        tagged_hit_type = row.get('TaggedHitType', '')
        play_result = row.get('PlayResult', '')

        # Skip rows without pitcher or batter information
        if not pitcher_name or not batter_name:
            continue

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
                'FIP': 0
            }

        # Track earned runs for pitchers 
        # Note: Can not track inherited runners or passed balls so this only accounts for runs excluding errors
        if play_result != 'Error':
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

        # Track total pitches thrown
        pitchers[pitcher_name]['TotalPitches'] += 1

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

# Function to calculate derived pitching stats
def calculate_derived_stats(pitchers):
    for pitcher, stats in pitchers.items():
        outs_recorded = stats['OutsRecorded'] # Outs Recorded
        earned_runs = stats['EarnedRuns'] # Earned Runs
        innings_pitched = outs_recorded / 3 # Innings Pitched
        tbf = stats['TotalBattersFaced'] # Total Batters Faced
        tp = stats['TotalPitches'] # Total Pitches
        
        # Calculate innings pitched
        stats['InningsPitched'] = innings_pitched
        
        # Calculate ERA
        stats['ERA'] = (9 * earned_runs / innings_pitched) if innings_pitched > 0 else 0
        
        # Calculate FIP
        home_runs = stats['HomeRuns']
        walks = stats['Walks']
        hit_by_pitches = stats['HitBatters']
        strikeouts = stats['Strikeouts']
        inn_pitched = stats['InningsPitched']
        FIP_constant = 3.17 # This is a constant used from the 2024 MLB season
        
        if inn_pitched > 0:
            stats['FIP'] = ((13 * home_runs) + (3 * (walks + hit_by_pitches)) - (2 * strikeouts)) / inn_pitched + FIP_constant
        else:
            stats['FIP'] = 0
            
        # Calculate percentages
        stats['KPercent'] = stats['Strikeouts'] / tbf * 100 if tbf > 0 else 0
        stats['BBPercent'] = stats['Walks'] / tbf * 100 if tbf > 0 else 0
        stats['FirstPitchStrikePercent'] = stats['FirstPitchStrikes'] / tbf * 100 if tbf > 0 else 0
        stats['FirstPitchBallPercent'] = stats['FirstPitchBalls'] / tbf * 100 if tbf > 0 else 0
        stats['StrikePercent'] = stats['Strikes'] / tp * 100 if tp > 0 else 0
        stats['BallPercent'] = stats['Balls'] / tp * 100 if tp > 0 else 0
        stats['AtBatEfficiencyPercent'] = stats['AtBatEfficiency'] / tbf * 100 if tbf > 0 else 0

# Function to write pitching stats to CSV
# Function to write pitching stats to CSV
def write_stats_to_csv(pitchers, output_file):
    with open(output_file, mode='w', newline='') as file:
        # Define column headers
        fieldnames = [
            'Pitcher', 'Team', 'W', 'L', 'EarnedRuns', 'InningsPitched', 'ERA', 
            'TotalBattersFaced', 'TotalPitches', 'Strikes', 'Balls', 'StrikePercent', 'BallPercent',
            'FirstPitchStrikes', 'FirstPitchBalls', 'FirstPitchStrikePercent', 'FirstPitchBallPercent',
            'Strikeouts', 'Walks', 'KPercent', 'BBPercent', 'HitBatters', 'HomeRuns',
            'FoulsAfter2Strikes', 'First2of3StrikesOrInPlay', 'AtBatEfficiency', 'AtBatEfficiencyPercent', 'FIP'
        ]
      
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write data for each pitcher
        for pitcher, stats in pitchers.items():
            team_code = stats.get('Team', 'Unknown')
            # Translate team code to full team name using the team_names dictionary
            team_name = team_names.get(team_code, team_code)  # Use code as fallback if not found
            
            row = {
                'Pitcher': pitcher,
                'Team': team_name,  # Use translated team name instead of code
                'W': stats['Wins'],
                'L': stats['Losses'],
                'EarnedRuns': stats['EarnedRuns'],
                'InningsPitched': round(stats['InningsPitched'], 2),
                'ERA': round(stats['ERA'], 2),
                'TotalBattersFaced': stats['TotalBattersFaced'],
                'TotalPitches': stats['TotalPitches'],
                'Strikes': stats['Strikes'],
                'Balls': stats['Balls'],
                'StrikePercent': round(stats['StrikePercent'], 2),
                'BallPercent': round(stats['BallPercent'], 2),
                'FirstPitchStrikes': stats['FirstPitchStrikes'],
                'FirstPitchBalls': stats['FirstPitchBalls'],
                'FirstPitchStrikePercent': round(stats['FirstPitchStrikePercent'], 2),
                'FirstPitchBallPercent': round(stats['FirstPitchBallPercent'], 2),
                'Strikeouts': stats['Strikeouts'],
                'Walks': stats['Walks'],
                'KPercent': round(stats['KPercent'], 2),
                'BBPercent': round(stats['BBPercent'], 2),
                'HitBatters': stats['HitBatters'],
                'HomeRuns': stats['HomeRuns'],
                'FoulsAfter2Strikes': stats['FoulsAfter2Strikes'],
                'First2of3StrikesOrInPlay': stats['First2of3StrikesOrInPlay'],
                'AtBatEfficiency': stats['AtBatEfficiency'],
                'AtBatEfficiencyPercent': round(stats['AtBatEfficiencyPercent'], 2),
                'FIP': round(stats['FIP'], 2)
            }
            writer.writerow(row)

# Function to find all CSV files in a directory and its subdirectories
def find_all_csv_files(directory_path):
    csv_files = []
    
    # Walk through directory and all subdirectories
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    
    return csv_files

# Function to process all CSV files in a directory and its subdirectories
# Function to check if file contains AUB_PRC as a pitching team
def contains_aub_prc(data):
    for row in data:
        pitcher_team = row.get('PitcherTeam', '')
        if pitcher_team == 'AUB_PRC':
            return True
    return False

# Function to process all CSV files in a directory and its subdirectories
def process_all_csv_files(directory_path, output_file):
    print(f"Processing all CSV files in: {directory_path} and all subdirectories")
    
    # Find all CSV files in the directory and subdirectories
    csv_files = find_all_csv_files(directory_path)
    
    if not csv_files:
        print("No CSV files found in the directory or its subdirectories.")
        return
    
    print(f"Found {len(csv_files)} CSV files.")
    
    # Initialize combined pitchers data
    all_pitchers = {}
    files_processed = 0
    files_skipped = 0
    files_excluded = 0
    
    # Process each file
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        relative_path = os.path.relpath(file_path, directory_path)
        print(f"Processing: {relative_path}")
        
        data = read_csv(file_path)
        if data is not None:
            # Check if file contains AUB_PRC as pitching team
            if contains_aub_prc(data):
                print(f"Excluded: {relative_path} (contains AUB_PRC as pitching team)")
                files_excluded += 1
                continue
                
            try:
                # Calculate stats for this file
                pitchers, team_runs, pitcher_teams = calculate_pitching_stats(data)
                assign_wins_losses(pitchers, team_runs, pitcher_teams)
                
                # Add team information to pitcher stats
                for pitcher, team in pitcher_teams.items():
                    if pitcher in pitchers:
                        pitchers[pitcher]['Team'] = team
                
                # Merge with existing data
                for pitcher, stats in pitchers.items():
                    if pitcher not in all_pitchers:
                        all_pitchers[pitcher] = stats
                    else:
                        # Update stats for existing pitchers
                        for stat, value in stats.items():
                            if stat not in ['ERA', 'FIP', 'Team']:  # Don't add these
                                all_pitchers[pitcher][stat] += value
                            elif stat == 'Team' and 'Team' not in all_pitchers[pitcher]:
                                # Only set the team if it hasn't been set yet
                                all_pitchers[pitcher]['Team'] = value
                
                files_processed += 1
            except Exception as e:
                print(f"Error processing {relative_path}: {str(e)}")
                files_skipped += 1
        else:
            print(f"Skipped: {relative_path} (failed to read file)")
            files_skipped += 1
    
    print(f"\nSummary: Processed {files_processed} files, Skipped {files_skipped} files, Excluded {files_excluded} files (AUB_PRC)")
    
    if files_processed > 0:
        # Calculate derived stats (ERA, FIP, percentages) after combining all data
        calculate_derived_stats(all_pitchers)
        
        # Write the combined stats to the output file
        write_stats_to_csv(all_pitchers, output_file)
        
        print(f"Successfully processed all files. Results saved to: {output_file}")
        
        return all_pitchers
    else:
        print("No files were successfully processed. No output file created.")
        return None

# Function that prints pitching stats (kept for backward compatibility)
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

        # Additional Stats
        Kpercent = K / TBF * 100 if TBF > 0 else 0 # Strikeout Percentage
        BBpercent = BB / TBF * 100 if TBF > 0 else 0 # Walk Percentage
        fStrikePercent = fStrikes / TBF * 100 if TBF > 0 else 0 # First Pitch Strike Percentage
        fBallPercent = fBalls / TBF * 100 if TBF > 0 else 0 # First Pitch Ball Percentage
        strikePercent = Strikes / TP * 100 if TP > 0 else 0 # Strike Percentage
        ballPercent = Balls / TP * 100 if TP > 0 else 0 # Ball Percentage
        AtBatEfficiencyPercent = AtBatEfficiency / TBF * 100 if TBF > 0 else 0 # At Bat Efficiency Percentage

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
        print()

# -------------------- MAIN FUNCTION -------------------- #
if __name__ == "__main__":
    print("Pitching Stats Converter")
    print("------------------------")
    print("1. Process a single CSV file")
    print("2. Process all CSV files in a directory and its subdirectories")
    choice = input("Enter your choice (1/2): ")
    
    if choice == "1":
        file_path = input("Enter the path to the CSV file: ")
        data = read_csv(file_path)
        if data is not None:
            print("\nFile found successfully! Processing now...\n")
            pitchers, team_runs, pitcher_teams = calculate_pitching_stats(data)
            assign_wins_losses(pitchers, team_runs, pitcher_teams)
            print_pitching_stats(pitchers)
            
            save_option = input("Would you like to save these stats to a CSV file? (y/n): ")
            if save_option.lower() == 'y':
                output_file = input("Enter the output file name (e.g., pitching_stats.csv): ")
                calculate_derived_stats(pitchers)
                write_stats_to_csv(pitchers, output_file)
                print(f"Stats saved to {output_file}")
        else:
            print("Failed to read the CSV file.")
    
    elif choice == "2":
        directory_path = input("Enter the directory path containing CSV files: ")
        output_file = input("Enter the output file name (e.g., combined_pitching_stats.csv): ")
        
        if os.path.isdir(directory_path):
            process_all_csv_files(directory_path, output_file)
        else:
            print("Invalid directory path.")
    
    else:
        print("Invalid choice. Please run the script again and select 1 or 2.")