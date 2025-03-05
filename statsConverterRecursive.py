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

# Function to calculate batter statistics
def calculate_hitting_stats(data):
    batters = defaultdict(lambda: defaultdict(int))
    plate_appearances = set()

    for row in data:
        # Safely access required columns (use .get() for missing columns)
        game_id = row.get('gameid', '').strip()
        batter_name = row.get('batter', '').strip()
        batter_team = row.get('batterteam', '').strip()  # Get batter team
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

        if batter_name not in batters:
            batters[batter_name] = {
                'ExitSpeeds': [], 'Angles': [], 'PA': 0, '1B': 0, '2B': 0, '3B': 0,
                'HR': 0, 'H': 0, 'TB': 0, 'K': 0, 'BB': 0, 'HBP': 0, 'SH': 0,
                'SF': 0, 'AB': 0, 'RBI': 0, 'GDP': 0, 'Team': batter_team  # Store the team name
            }

        if exit_speed:
            batters[batter_name]['ExitSpeeds'].append(exit_speed)
        if launch_angle:
            batters[batter_name]['Angles'].append(launch_angle)

        # Unique plate appearance tracking
        pa_identifier = (game_id, batter_name, inning, inning_half, pa_of_inning)
        if pa_identifier not in plate_appearances:
            plate_appearances.add(pa_identifier)
            batters[batter_name]['PA'] += 1

        # Explicitly handle play results
        if play_result == 'Single':
            batters[batter_name]['1B'] += 1
            batters[batter_name]['H'] += 1
            batters[batter_name]['TB'] += 1
        elif play_result == 'Double':
            batters[batter_name]['2B'] += 1
            batters[batter_name]['H'] += 1
            batters[batter_name]['TB'] += 2
        elif play_result == 'Triple':
            batters[batter_name]['3B'] += 1
            batters[batter_name]['H'] += 1
            batters[batter_name]['TB'] += 3
        elif play_result == 'HomeRun':
            batters[batter_name]['HR'] += 1
            batters[batter_name]['H'] += 1
            batters[batter_name]['TB'] += 4

        if play_result == 'Sacrifice':
            batters[batter_name]['SH' if hit_type == 'Bunt' else 'SF'] += 1

        if korbb == 'Strikeout':
            batters[batter_name]['K'] += 1
            batters[batter_name]['AB'] += 1
        elif korbb == 'Walk':
            batters[batter_name]['BB'] += 1

        if pitch_call == 'HitByPitch':
            batters[batter_name]['HBP'] += 1

        if play_result in ['Single', 'Double', 'Triple', 'HomeRun', 'Error', 'FieldersChoice', 'Out'] and play_result != 'Sacrifice':
            batters[batter_name]['AB'] += 1

        if play_result not in ['Error', 'FieldersChoice'] and not (play_result == 'Out' and hit_type == 'GroundBall' and outs_on_play == 2):
            batters[batter_name]['RBI'] += runs_scored
        elif play_result == 'Sacrifice':
            batters[batter_name]['RBI'] += runs_scored
        if korbb == 'Walk' and runs_scored > 0:
            batters[batter_name]['RBI'] += runs_scored
        if pitch_call == 'HitByPitch' and runs_scored > 0:
            batters[batter_name]['RBI'] += runs_scored

        if play_result == 'Out' and hit_type == 'GroundBall' and outs_on_play == 2:
            batters[batter_name]['GDP'] += 1

    # Compute missing advanced stats and averages
    for batter in batters:
        stats = batters[batter]
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

    return batters

# Function to write stats to a new CSV file
def write_stats_to_csv(batters, output_file):
    fieldnames = ['Player', 'Team', 'PA', 'AB', 'H', 'TB', '1B', '2B', '3B', 'HR', 'RBI',
                  'BB', 'K', 'HBP', 'SF', 'SH', 'GDP', 'AVG', 'BB%', 'K%',
                  'OBP', 'SLG', 'OPS', 'ISO', 'BABIP', 'wOBA', 'AvgExitVelocity', 'AvgLaunchAngle']

    with open(output_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for batter, stats in batters.items():
            # Remove unwanted fields
            cleaned_stats = {k: v for k, v in stats.items() if k not in ['ExitSpeeds', 'Angles']}
            # Format decimal values to two decimal places
            for key in ['AVG', 'BB%', 'K%', 'OBP', 'SLG', 'OPS', 'ISO', 'BABIP', 'wOBA', 'AvgExitVelocity', 'AvgLaunchAngle']:
                if key in cleaned_stats:
                    cleaned_stats[key] = f"{cleaned_stats[key]:.2f}"

            # Add "%" to BB% and K%
            if 'BB%' in cleaned_stats:
                cleaned_stats['BB%'] = f"{float(cleaned_stats['BB%']):.2f}%"
            if 'K%' in cleaned_stats:
                cleaned_stats['K%'] = f"{float(cleaned_stats['K%']):.2f}%"

            #Retrieve team name for each player, fallback to team code if team not in dictionary
            team_name = team_names.get(cleaned_stats['Team'], cleaned_stats['Team'])
            writer.writerow({'Player': batter, 'Team': team_name, **cleaned_stats})

if __name__ == "__main__":
    directory_path = input("Enter the directory path: ")
    output_file = input("Enter the output CSV file path: ")

    data = read_csv_directory(directory_path)
    if data:
        batters = calculate_hitting_stats(data)
        write_stats_to_csv(batters, output_file)
        print(f"Stats saved to {output_file}")
    else:
        print("No CSV files found.")
