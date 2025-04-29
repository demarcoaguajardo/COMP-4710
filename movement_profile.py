'''
movement_profile.py

Python script that reads CSV files containing pitch data from a folder and generates:
  - A composite heatmap showing optimal xRV areas (based on a simple linear xRV formula)
    for each pitch type. The heatmap does not plot individual pitch markers;
    it instead shows binned average xRV values with a dashed grid overlay,
    with the optimal area (lowest average xRV) highlighted.
  - A pitch summary panel including standard stats and the average xRV for each pitch type.
Each pitcher gets their own separate PDF report.

Author: Sam Chitty'
'''

import csv
import statistics
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np
import os
import glob
from matplotlib.backends.backend_pdf import PdfPages

# --------------- CONFIG --------------- #
# Default strike zone boundaries (used as a starting grid)
STRIKE_ZONE = {
    'side_min': -0.7085,
    'side_max': 0.7085,
    'height_min': 1.7,
    'height_max': 3.4
}

# Approximate d1-average velocities by pitch type (customize as needed)
d1_AVG_VELOCITY = {
    'Fastball': 83.6,
    'FourSeamFastBall': 84.7,
    'TwoSeamFastBall': 83.0,
    'Sinker': 83.6,
    'Cutter': 80.0,
    'Slider': 81.0,
    'ChangeUp': 79.0,
    'Curveball': 80.0
}

# Color mapping for pitch types
PITCH_COLORS = {
    'Fastball': 'red',
    'FourSeamFastBall': 'red',
    'TwoSeamFastBall': 'darkred',
    'Sinker': 'gold',
    'ChangeUp': 'green',
    'Slider': 'orange',
    'Cutter': 'blue',
    'Curveball': 'purple',
    'Unknown': 'gray'
}

# Set bin count for the heatmap (lower value = larger bins)
BIN_COUNT = 14

#########################################
#         Data Reading Functions        #
#########################################

def read_csv(file_path):
    """Reads the CSV file and returns a list of row dictionaries."""
    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

#########################################
#         Data Aggregation              #
#########################################

def calculate_pitch_stats(data):
    """
    Gathers pitching stats and additional metrics (velocity, spin rate, break, release info,
    and actual plate location) grouped by pitcher and pitch type, but only for pitchers
    from 'AUB_TIG' team.
    """
    pitchers = defaultdict(lambda: {
        'TotalPitches': 0,
        'PitchTypeData': defaultdict(list)
    })

    for row in data:
        # Check if PitcherTeam is 'AUB_TIG'
        if row.get('PitcherTeam') != 'AUB_TIG':
            continue

        pitcher_name = row.get('Pitcher', 'Unknown')
        pitch_type = row.get('TaggedPitchType', 'Unknown')

        release_speed = float(row['RelSpeed']) if row.get('RelSpeed') else 0.0
        spin_rate = float(row['SpinRate']) if row.get('SpinRate') else 0.0
        horz_break = float(row['HorzBreak']) if row.get('HorzBreak') else 0.0
        vert_break = float(row['VertBreak']) if row.get('VertBreak') else 0.0
        release_height = float(row['RelHeight']) if row.get('RelHeight') else 0.0
        release_side = float(row['RelSide']) if row.get('RelSide') else 0.0

        plate_loc_side = float(row['PlateLocSide']) if row.get('PlateLocSide') else 0.0
        plate_loc_height = float(row['PlateLocHeight']) if row.get('PlateLocHeight') else 0.0

        pitch_call = row.get('PitchCall', 'Unknown')

        pitchers[pitcher_name]['TotalPitches'] += 1
        pitchers[pitcher_name]['PitchTypeData'][pitch_type].append({
            'velocity': release_speed,
            'spin_rate': spin_rate,
            'h_break': horz_break,
            'v_break': vert_break,
            'release_height': release_height,
            'release_side': release_side,
            'plate_side': plate_loc_side,
            'plate_height': plate_loc_height,
            'pitch_call': pitch_call
        })

    return pitchers


#########################################
#      Outcome Metric Calculation       #
#########################################

def compute_xRV_for_pitch(pitch):
    """
    Computes an xRV Stuff value for a given pitch using a simple linear model:
       xRV = 0.1 * RelSpeed + 0.05 * VertBreak + 0.03 * HorzBreak + 0.02 * RelHeight - 1.0
    It uses the values stored under the keys:
       'velocity', 'v_break', 'h_break', and 'release_height'
    """
    try:
        velocity = float(pitch.get('velocity', 0))
        vert_break = float(pitch.get('v_break', 0))
        horz_break = float(pitch.get('h_break', 0))
        rel_height = float(pitch.get('release_height', 0))
    except Exception:
        return float('nan')
    xrv = 0.1 * velocity + 0.05 * vert_break + 0.03 * horz_break + 0.02 * rel_height - 1.0
    return xrv

#########################################
#    Compute Heatmap Data for a Pitch Type   #
#########################################

def compute_heatmap_data(pitch_list, bins=BIN_COUNT):
    """
    Given a list of pitches for one pitch type, bins the pitch locations (PlateLocSide, PlateLocHeight)
    and computes the average xRV (using compute_xRV_for_pitch) in each bin.
    Returns: the 2D array of average xRV, the xedges, and the yedges.
    """
    locations = []
    outcomes = []
    for pitch in pitch_list:
        try:
            ps = float(pitch.get('plate_side', 0))
            ph = float(pitch.get('plate_height', 0))
        except Exception:
            continue
        if not (STRIKE_ZONE['side_min'] <= ps <= STRIKE_ZONE['side_max'] and
                STRIKE_ZONE['height_min'] <= ph <= STRIKE_ZONE['height_max']):
            continue
        locations.append([ps, ph])
        outcomes.append(compute_xRV_for_pitch(pitch))
    if not locations:
        return None, None, None
    locations = np.array(locations)
    outcomes = np.array(outcomes)
    xedges = np.linspace(STRIKE_ZONE['side_min'], STRIKE_ZONE['side_max'], bins+1)
    yedges = np.linspace(STRIKE_ZONE['height_min'], STRIKE_ZONE['height_max'], bins+1)
    H_count, _, _ = np.histogram2d(locations[:,0], locations[:,1], bins=[xedges, yedges])
    H_weight, _, _ = np.histogram2d(locations[:,0], locations[:,1], bins=[xedges, yedges],
                                    weights=outcomes)
    with np.errstate(divide='ignore', invalid='ignore'):
        avg_xRV = np.divide(H_weight, H_count, out=np.full_like(H_weight, np.nan), where=H_count>0)
    return avg_xRV, xedges, yedges

#########################################
#    Plot Composite Heatmap per Pitcher  #
#########################################

def plot_optimal_areas_for_pitcher(pitchers, pitcher_name, bins=BIN_COUNT):
    """
    For the given pitcher, create a composite heatmap figure.
    For each pitch type, compute a 2D heatmap of average xRV values (using PlateLocSide and PlateLocHeight)
    and display the heatmap as a subplot.
    No individual pitch markers are shown; instead, the heatmap (with a shared color scale) is displayed.
    A dashed grid overlay (3×3 sub-zones) is drawn, and the cell with the lowest average xRV is outlined
    and labeled as the "Optimal" area.
    """
    if pitcher_name not in pitchers:
        print(f"No data found for pitcher: {pitcher_name}")
        return None

    pitch_types = list(pitchers[pitcher_name]['PitchTypeData'].keys())
    n = len(pitch_types)
    cols = 2
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(12, rows * 4))
    axes = axes.flatten()

    # Compute a global color scale from all pitch types:
    global_vals = []
    heatmap_dict = {}
    for p_type in pitch_types:
        pitch_list = pitchers[pitcher_name]['PitchTypeData'][p_type]
        avg_xRV, xedges, yedges = compute_heatmap_data(pitch_list, bins=bins)
        if avg_xRV is not None:
            heatmap_dict[p_type] = (avg_xRV, xedges, yedges)
            valid_vals = avg_xRV[~np.isnan(avg_xRV)]
            if valid_vals.size > 0:
                global_vals.extend(valid_vals.flatten())
    if not global_vals:
        print("No valid xRV values for heatmap computation.")
        return None
    vmin = min(global_vals)
    vmax = max(global_vals)

    # For each pitch type, plot the heatmap.
    for i, p_type in enumerate(pitch_types):
        ax = axes[i]
        if p_type not in heatmap_dict:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center")
            ax.axis('off')
            continue
        avg_xRV, xedges, yedges = heatmap_dict[p_type]
        im = ax.imshow(avg_xRV.T, extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
                       origin='lower', aspect='auto', cmap='viridis',
                       vmin=vmin, vmax=vmax)
        ax.set_title(p_type, fontsize=12)
        ax.set_xlabel("PlateLocSide")
        ax.set_ylabel("PlateLocHeight")
        ax.set_xlim([xedges[0], xedges[-1]])
        ax.set_ylim([yedges[0], yedges[-1]])
        ax.grid(False)

        # Draw dashed grid overlay (creating 3x3 sub-zones)
        num_grid = 4  # 4 lines create 3 cells in each dimension.
        for x in np.linspace(xedges[0], xedges[-1], num_grid):
            ax.axvline(x, linestyle='--', color='black', linewidth=0.75)
        for y in np.linspace(yedges[0], yedges[-1], num_grid):
            ax.axhline(y, linestyle='--', color='black', linewidth=0.75)

        # Identify the optimal cell (lowest average xRV)
        if not np.all(np.isnan(avg_xRV)):
            optimal_index = np.nanargmin(avg_xRV)
            optimal_cell = np.unravel_index(optimal_index, avg_xRV.shape)
            optimal_x_center = (xedges[optimal_cell[0]] + xedges[optimal_cell[0]+1]) / 2
            optimal_y_center = (yedges[optimal_cell[1]] + yedges[optimal_cell[1]+1]) / 2
            cell_width = xedges[1] - xedges[0]
            cell_height = yedges[1] - yedges[0]
            rect = Rectangle((optimal_x_center - cell_width/2, optimal_y_center - cell_height/2),
                             cell_width, cell_height, edgecolor='red', facecolor='none', lw=2)
            ax.add_patch(rect)
            ax.text(optimal_x_center, optimal_y_center, "Optimal", color='red', fontsize=10,
                    ha='center', va='center')
        else:
            ax.text(0.5, 0.5, "No valid xRV", transform=ax.transAxes, ha="center")
    # Hide extra axes if necessary.
    for j in range(i+1, len(axes)):
        axes[j].axis('off')

    fig.suptitle(f"Optimal xRV Areas for {pitcher_name}", fontsize=16)
    fig.tight_layout(rect=[0,0,1,0.95])
    return fig

#########################################
#    Plot Pitch Summary (Stat Panel)     #
#########################################

def plot_pitch_summary_ax(ax, summary_data, title="Pitch Summary"):
    """
    Plots the pitch summary (usage, velocity, spin, break, release height, and xRV)
    on the provided axis.
    """
    num_pitches = len(summary_data)
    if num_pitches == 0:
        ax.text(0.5, 0.5, "No pitch summary data", transform=ax.transAxes)
        return

    ax.set_xlim(-0.5, num_pitches - 0.5)
    ax.set_ylim(-1.0, 1.1)  # extend lower bound to show xRV
    ax.axis('off')
    ax.set_title(title, fontsize=12, pad=10)

    for i, pitch in enumerate(summary_data):
        x_center = i
        color = pitch.get("color", "gray")
        circle = plt.Circle((x_center, 0.75), 0.15, color=color, alpha=0.8)
        ax.add_patch(circle)
        usage_str = f"{pitch['usage']}%"
        ax.text(x_center, 0.5, usage_str, ha="center", va="center", fontsize=10, fontweight="bold")
        mph_str = f"{pitch['mph']:.1f} mph"
        ax.text(x_center, 0.25, mph_str, ha="center", va="center", fontsize=9)
        avg_str = f"d1 avg: {pitch['d1_avg']:.1f}"
        ax.text(x_center, 0.05, avg_str, ha="center", va="center", fontsize=8, color="dimgray")
        xrv_str = f"xRV: {pitch['xRV']:.2f}"
        ax.text(x_center, -0.05, xrv_str, ha="center", va="center", fontsize=8, color="blue")
        rel_height_str = f"RelHt: {pitch['rel_height']:.1f} ft"
        ax.text(x_center, -0.25, rel_height_str, ha="center", va="center", fontsize=8, color="dimgray")
        spin_str = f"{pitch['spin']:.0f} rpm"
        ax.text(x_center, -0.45, spin_str, ha="center", va="center", fontsize=9)
        break_str = f"HBreak: {pitch['h_break']:.1f}\"  VBreak: {pitch['v_break']:.1f}\""
        ax.text(x_center, -0.65, break_str, ha="center", va="center", fontsize=8, color="dimgray")
        ax.text(x_center, 0.95, pitch["pitch_type"], ha="center", va="bottom", fontsize=9, fontweight="bold")

#########################################
#    Create Pitch Summary Data           #
#########################################

def create_pitch_summary_data(pitchers, pitcher_name):
    """
    Creates a list of dictionaries (pitch_data) for the given pitcher for the pitch summary.
    Each dict includes:
      - pitch_type, usage, mph, d1_avg, spin, h_break, v_break, rel_height, xRV, and color.
    """
    if pitcher_name not in pitchers:
        return []
    p_data = pitchers[pitcher_name]
    total_pitches = p_data['TotalPitches']
    pitch_type_data = p_data['PitchTypeData']
    if total_pitches == 0:
        return []

    summary_list = []
    for p_type, pitch_list in pitch_type_data.items():
        count = len(pitch_list)
        usage = (count / total_pitches) * 100 if total_pitches > 0 else 0

        velocities = [p['velocity'] for p in pitch_list] if pitch_list else []
        spin_rates = [p['spin_rate'] for p in pitch_list] if pitch_list else []
        h_breaks = [p['h_break'] for p in pitch_list] if pitch_list else []
        v_breaks = [p['v_break'] for p in pitch_list] if pitch_list else []
        release_heights = [p['release_height'] for p in pitch_list] if pitch_list else []

        avg_vel = statistics.mean(velocities) if velocities else 0.0
        avg_spin = statistics.mean(spin_rates) if spin_rates else 0.0
        avg_h_break = statistics.mean(h_breaks) if h_breaks else 0.0
        avg_v_break = statistics.mean(v_breaks) if v_breaks else 0.0
        avg_rel_height = statistics.mean(release_heights) if release_heights else 0.0

        xRV_values = []
        for p in pitch_list:
            xrv = compute_xRV_for_pitch(p)
            if not np.isnan(xrv):
                xRV_values.append(xrv)
        avg_xRV = statistics.mean(xRV_values) if xRV_values else float('nan')

        d1_avg = d1_AVG_VELOCITY.get(p_type, 80.0)
        color = PITCH_COLORS.get(p_type, 'gray')

        summary_list.append({
            'pitch_type': p_type,
            'usage': round(usage, 1),
            'mph': round(avg_vel, 1),
            'd1_avg': d1_avg,
            'spin': round(avg_spin, 0),
            'h_break': round(avg_h_break, 1),
            'v_break': round(avg_v_break, 1),
            'rel_height': round(avg_rel_height, 1),
            'xRV': round(avg_xRV, 2),
            'color': color
        })

    summary_list.sort(key=lambda x: x['usage'], reverse=True)
    return summary_list

#########################################
#  Combined Profile and Summary Plot     #
#########################################

def plot_combined_profile_and_summary(pitchers, pitcher_name, all_data):
    """
    Creates a combined figure with two parts:
      - Top: Composite heatmaps showing optimal xRV areas (one subplot per pitch type)
      - Bottom: Pitch Summary (usage, velocity, spin, break, release height, and xRV)
    Returns a tuple of figures: (heatmap_fig, summary_fig)
    """
    heatmap_fig = plot_optimal_areas_for_pitcher(pitchers, pitcher_name, bins=BIN_COUNT)
    summary_data = create_pitch_summary_data(pitchers, pitcher_name)
    summary_fig, ax_summary = plt.subplots(figsize=(8, 3))
    plot_pitch_summary_ax(ax_summary, summary_data, title=f"Pitch Summary: {pitcher_name}")
    return heatmap_fig, summary_fig

#########################################
#               Main Code               #
#########################################

if __name__ == "__main__":
    folder = input("Enter the directory containing the CSV files: ").strip()
    data = []
    for file in glob.glob(os.path.join(folder, '**', '*.csv'), recursive=True):
      if os.path.isfile(file):
          d = read_csv(file)
          if d is not None:
              data.extend(d)

    if data:
        pitchers = calculate_pitch_stats(data)

        output_dir = "pitcher_reports14"
        os.makedirs(output_dir, exist_ok=True)

        # Create separate PDF files for each pitcher.
        for pitcher_name in pitchers.keys():
            print(f"Generating report for {pitcher_name}...")
            heatmap_fig, summary_fig = plot_combined_profile_and_summary(pitchers, pitcher_name, data)
            output_pdf = os.path.join(output_dir, f"{pitcher_name}.pdf")
            with PdfPages(output_pdf) as pdf:
                pdf.savefig(heatmap_fig)
                pdf.savefig(summary_fig)
            plt.close(heatmap_fig)
            plt.close(summary_fig)
            print(f"Saved report to {output_pdf}")
        print("Reports generated for all pitchers.")
    else:
        print("Failed to read any CSV files from the directory.")
