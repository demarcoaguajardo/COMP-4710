'''
movement_profile.py

Python script that reads a CSV file containing pitch data
and generates movement profiles

Author: Sam Chitty'
'''

import csv
import statistics
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import os


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


def calculate_empirical_strike_zone(data, threshold=0.70, x_bins=20, y_bins=20):
   """
   Calculate an empirical strike zone based on pitch data.
   It divides the default strike zone into a grid and computes strike probability for each cell.
   Returns a dict with keys: 'side_min', 'side_max', 'height_min', 'height_max'
   corresponding to the boundaries where strike probability is at least the threshold.
   """
   x_min = STRIKE_ZONE['side_min']
   x_max = STRIKE_ZONE['side_max']
   y_min = STRIKE_ZONE['height_min']
   y_max = STRIKE_ZONE['height_max']
  
   x_edges = np.linspace(x_min, x_max, x_bins+1)
   y_edges = np.linspace(y_min, y_max, y_bins+1)
  
   total_grid = np.zeros((x_bins, y_bins))
   strike_grid = np.zeros((x_bins, y_bins))
  
   strike_calls = {"StrikeCalled", "StrikeSwinging", "FoulBall", "InPlay"}
  
   for row in data:
       try:
           plate_side = float(row['PlateLocSide'])
           plate_height = float(row['PlateLocHeight'])
       except (ValueError, KeyError):
           continue
      
       if plate_side < x_min or plate_side > x_max or plate_height < y_min or plate_height > y_max:
           continue
      
       i = np.digitize(plate_side, x_edges) - 1
       j = np.digitize(plate_height, y_edges) - 1
       if i < 0 or i >= x_bins or j < 0 or j >= y_bins:
           continue
      
       total_grid[i, j] += 1
       if row.get('PitchCall', '') in strike_calls:
           strike_grid[i, j] += 1
  
   strike_prob = np.divide(strike_grid, total_grid, out=np.zeros_like(strike_grid), where=total_grid>0)
   valid_cells = np.argwhere(strike_prob >= threshold)
  
   if valid_cells.size == 0:
       return STRIKE_ZONE.copy()
  
   valid_x_min = min(x_edges[cell[0]] for cell in valid_cells)
   valid_x_max = max(x_edges[cell[0] + 1] for cell in valid_cells)
   valid_y_min = min(y_edges[cell[1]] for cell in valid_cells)
   valid_y_max = max(y_edges[cell[1] + 1] for cell in valid_cells)
  
   return {
       'side_min': valid_x_min,
       'side_max': valid_x_max,
       'height_min': valid_y_min,
       'height_max': valid_y_max
   }


def calculate_pitch_stats(data):
   """
   Gathers pitching stats and additional metrics (velocity, spin rate, break, release info,
   and actual plate location) grouped by pitcher and pitch type.
   """
   pitchers = defaultdict(lambda: {
       'TotalPitches': 0,
       'PitchTypeData': defaultdict(list)
   })


   for row in data:
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


def print_additional_pitch_metrics(pitchers):
   """
   Prints aggregated metrics (average velocity, spin rate, etc.) by pitcher and pitch type.
   """
   for pitcher_name, p_data in pitchers.items():
       print(f"\nPitcher: {pitcher_name}")
       print(f"Total Pitches: {p_data['TotalPitches']}")
       for pitch_type, pitch_list in p_data['PitchTypeData'].items():
           if not pitch_list:
               continue
           velocities = [p['velocity'] for p in pitch_list]
           spin_rates = [p['spin_rate'] for p in pitch_list]
           h_breaks = [p['h_break'] for p in pitch_list]
           v_breaks = [p['v_break'] for p in pitch_list]
           release_heights = [p['release_height'] for p in pitch_list]
           release_sides = [p['release_side'] for p in pitch_list]


           avg_vel = statistics.mean(velocities) if velocities else 0
           avg_spin = statistics.mean(spin_rates) if spin_rates else 0
           avg_h_break = statistics.mean(h_breaks) if h_breaks else 0
           avg_v_break = statistics.mean(v_breaks) if v_breaks else 0
           avg_rel_height = statistics.mean(release_heights) if release_heights else 0
           avg_rel_side = statistics.mean(release_sides) if release_sides else 0


           print(f"  Pitch Type: {pitch_type}")
           print(f"    # Pitches: {len(pitch_list)}")
           print(f"    Avg Velocity: {avg_vel:.2f} mph")
           print(f"    Avg Spin Rate: {avg_spin:.0f} rpm")
           print(f"    Avg H Break: {avg_h_break:.2f} in")
           print(f"    Avg V Break: {avg_v_break:.2f} in")
           print(f"    Avg Release Height: {avg_rel_height:.2f} ft")
           print(f"    Avg Release Side: {avg_rel_side:.2f} ft")


# helper functions to plot on provided axes
def plot_movement_profile_ax(ax, pitchers, pitcher_name, all_data):
   """
   Plots the movement profile on the provided axis using PlateLocSide (x) and PlateLocHeight (y).
   Marker shape is determined by PitchCall; color is determined by pitch type.
   Also draws the empirical strike zone and places the legend above the plot.
   """
   if pitcher_name not in pitchers:
       ax.text(0.5, 0.5, f"No data for {pitcher_name}", transform=ax.transAxes)
       return
  
   p_data = pitchers[pitcher_name]
   pitch_type_data = p_data['PitchTypeData']
   all_pitches = []
   for p_type, pitch_list in pitch_type_data.items():
       for p in pitch_list:
           p['pitch_type'] = p_type
           all_pitches.append(p)
   if not all_pitches:
       ax.text(0.5, 0.5, f"No pitch data for {pitcher_name}", transform=ax.transAxes)
       return
  
   # Marker shapes for different pitch calls
   shape_mapping = {
       "StrikeCalled": "o",
       "StrikeSwinging": "^",
       "FoulBall": "s",
       "InPlay": "D",
       "BallCalled": "x",
       "HitByPitch": "*"
   }
  
   # Calculate empirical strike zone from the entire dataset
   empirical_zone = calculate_empirical_strike_zone(all_data, threshold=0.70, x_bins=20, y_bins=20)
   rect = plt.Rectangle((empirical_zone['side_min'], empirical_zone['height_min']),
                        empirical_zone['side_max'] - empirical_zone['side_min'],
                        empirical_zone['height_max'] - empirical_zone['height_min'],
                        edgecolor='gray', facecolor='none', lw=2)
   ax.add_patch(rect)
  
   for p in all_pitches:
       marker = shape_mapping.get(p.get('pitch_call', 'Unknown'), "o")
       color = PITCH_COLORS.get(p.get('pitch_type', 'Unknown'), 'black')
       ax.scatter(p['plate_side'], p['plate_height'], marker=marker, s=80,
                  color=color, edgecolor='black', alpha=0.7)
  
   ax.set_title(f"Pitch Location: {pitcher_name}")
   ax.set_xlabel("PlateLocSide")
   ax.set_ylabel("PlateLocHeight")
   ax.grid(True)
  
   # Create legend handles for pitch types (colors)
   unique_pitch_types = {}
   for p in all_pitches:
       pt = p.get('pitch_type', 'Unknown')
       if pt not in unique_pitch_types:
           unique_pitch_types[pt] = PITCH_COLORS.get(pt, 'black')
   pitch_type_handles = [Line2D([0], [0], marker='o', color='w', label=pt,
                             markerfacecolor=color, markersize=10) 
                      for pt, color in unique_pitch_types.items()]
  
   # Create legend handles for pitch calls (marker shapes)
   unique_pitch_calls = {}
   for p in all_pitches:
       call = p.get('pitch_call', 'Unknown')
       if call not in unique_pitch_calls:
           unique_pitch_calls[call] = shape_mapping.get(call, 'o')
   pitch_call_handles = [Line2D([0], [0], marker=marker, color='k', label=call,
                             linestyle='', markersize=10)
                      for call, marker in unique_pitch_calls.items()]
  
   # Place legends completely above the plot using a higher bbox_to_anchor
   leg1 = ax.legend(handles=pitch_type_handles, title="Pitch Type (color)",
                    bbox_to_anchor=(0, .85), loc='lower left')
   #ax.add_artist(leg1)
   # The second legend (pitch result) is horizontal via ncol
   leg2 = ax.legend(handles=pitch_call_handles, title="Pitch Call (shape)",
                    bbox_to_anchor=(0, 1.15), loc='lower left', ncol=len(pitch_call_handles))


def plot_pitch_summary_ax(ax, summary_data, title="Pitch Summary"):
   """
   Plots the pitch summary (usage, velocity, spin, break, and release height) on the provided axis.
   """
   num_pitches = len(summary_data)
   if num_pitches == 0:
       ax.text(0.5, 0.5, "No pitch summary data", transform=ax.transAxes)
       return
  
   ax.set_xlim(-0.5, num_pitches - 0.5)
   ax.set_ylim(-0.8, 1.1)
   ax.axis('off')
   ax.set_title(title, fontsize=12, pad=10)
  
   for i, pitch in enumerate(summary_data):
       x_center = i
       color = pitch.get("color", "gray")
       # Draw a circle patch for the pitch type color
       circle = plt.Circle((x_center, 0.75), 0.15, color=color, alpha=0.8)
       ax.add_patch(circle)
       # Usage
       usage_str = f"{pitch['usage']}%"
       ax.text(x_center, 0.5, usage_str,
               ha="center", va="center", fontsize=10, fontweight="bold")
       # Velocity
       mph_str = f"{pitch['mph']:.1f} mph"
       ax.text(x_center, 0.25, mph_str,
               ha="center", va="center", fontsize=9)
       # d1 avg velocity
       avg_str = f"d1 avg: {pitch['d1_avg']:.1f}"
       ax.text(x_center, 0.05, avg_str,
               ha="center", va="center", fontsize=8, color="dimgray")
       # Average Release Height (new line)
       rel_height_str = f"RelHt: {pitch['rel_height']:.1f} ft"
       ax.text(x_center, -0.15, rel_height_str,
               ha="center", va="center", fontsize=8, color="dimgray")
       # Spin rate
       spin_str = f"{pitch['spin']:.0f} rpm"
       ax.text(x_center, -0.35, spin_str,
               ha="center", va="center", fontsize=9)
       # Horizontal & vertical break
       break_str = f"HBreak: {pitch['h_break']:.1f}\"  VBreak: {pitch['v_break']:.1f}\""
       ax.text(x_center, -0.55, break_str,
               ha="center", va="center", fontsize=8, color="dimgray")
       # Pitch type label
       ax.text(x_center, 0.95, pitch["pitch_type"],
               ha="center", va="bottom", fontsize=9, fontweight="bold")


def create_pitch_summary_data(pitchers, pitcher_name):
   """
   Creates a list of dictionaries (pitch_data) for the given pitcher
   to use in plot_pitch_summary_ax(). Each dict includes:
     - pitch_type
     - usage (in %)
     - mph (average velocity)
     - d1_avg (d1 average velocity)
     - spin (average spin rate)
     - h_break (average horizontal break)
     - v_break (average vertical break)
     - rel_height (average release height)
     - color (for display)
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
           'color': color
       })
  
   summary_list.sort(key=lambda x: x['usage'], reverse=True)
   return summary_list


def plot_combined_profile_and_summary(pitchers, pitcher_name, all_data):
   """
   Creates a combined figure with two subplots:
     - Top: Movement Profile (actual pitch locations)
     - Bottom: Pitch Summary (usage, velocity, spin, break, and release height)
   Returns the figure object.
   """
   fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(8, 10))
   plt.subplots_adjust(hspace=0.5)
  
   plot_movement_profile_ax(ax1, pitchers, pitcher_name, all_data)
  
   summary_data = create_pitch_summary_data(pitchers, pitcher_name)
   plot_pitch_summary_ax(ax2, summary_data, title=f"Pitch Summary: {pitcher_name}")
  
   return fig


if __name__ == "__main__":
   file_path = "/content/20220218-VATech-1(in).csv"
   data = read_csv(file_path)
   if data is None:
       print("Could not read CSV data.")
   else:
       pitchers = calculate_pitch_stats(data)
      
       output_dir = "pitcher_reports6"
       os.makedirs(output_dir, exist_ok=True)
      
       for pitcher_name in pitchers.keys():
           print(f"Generating report for {pitcher_name}...")
           fig = plot_combined_profile_and_summary(pitchers, pitcher_name, data)
           filename = f"{pitcher_name.replace(',','').replace(' ', '_')}_combined.pdf"
           filepath = os.path.join(output_dir, filename)
           fig.savefig(filepath)
           plt.close(fig)
           print(f"Saved report to {filepath}")
      
       print("Reports generated for all pitchers.")