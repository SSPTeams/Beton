import json

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import dates as mdates
from datetime import datetime
from collections import defaultdict


def visualize_assigned_trips(assigned_trips):
    """
    Visualizes assigned trips data as a Gantt chart.

    Parameters:
    - assigned_trips: list of dictionaries containing trip information
    """
    # Organize trips by vehicle
    vehicles_schedule = defaultdict(list)
    for trip in assigned_trips:
        vehicle_id = trip['vehicle_id']
        vehicles_schedule[vehicle_id].append(trip)

    # Get sorted list of vehicle IDs
    vehicle_ids = sorted(vehicles_schedule.keys())

    # Set up the plot
    fig, ax = plt.subplots(figsize=(15, 8))

    # Configure Y-axis
    y_ticks = range(len(vehicle_ids))
    y_labels = [f"Vehicle {vehicle_id}" for vehicle_id in vehicle_ids]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.invert_yaxis()  # Invert Y-axis so the first vehicle is at the top

    # Configure X-axis
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    # Determine base date for plotting
    if assigned_trips:
        base_date = datetime.strptime(assigned_trips[0]['start_at'], '%Y-%m-%d %H:%M:%S').date()
    else:
        base_date = datetime.today().date()

    # Define colors for different phases
    phase_colors = {
        'Loading': 'skyblue',
        'Travel to Customer': 'lightgreen',
        'Unloading': 'salmon',
        'Return to Plant': 'lightsalmon'
    }

    # Plot each trip
    for i, vehicle_id in enumerate(vehicle_ids):
        trips = vehicles_schedule[vehicle_id]
        for trip in trips:
            # Parse times
            start_at = datetime.strptime(trip['start_at'], '%Y-%m-%d %H:%M:%S')
            load_at = datetime.strptime(trip['load_at'], '%Y-%m-%d %H:%M:%S')
            arrive_at = datetime.strptime(trip['arrive_at'], '%Y-%m-%d %H:%M:%S')
            unload_at = datetime.strptime(trip['unload_at'], '%Y-%m-%d %H:%M:%S')
            return_at = datetime.strptime(trip['return_at'], '%Y-%m-%d %H:%M:%S')

            # Define phases
            phases = [
                ('Loading', start_at, load_at),
                ('Travel to Customer', load_at, arrive_at),
                ('Unloading', arrive_at, unload_at),
                ('Return to Plant', unload_at, return_at)
            ]

            # Plot each phase
            for phase, start_time, end_time in phases:
                start_num = mdates.date2num(start_time)
                end_num = mdates.date2num(end_time)
                duration = end_num - start_num

                ax.barh(
                    i,
                    duration,
                    left=start_num,
                    height=0.4,
                    color=phase_colors.get(phase, 'grey'),
                    edgecolor='black'
                )

                # Add annotations for Loading and Unloading phases
                if phase in ['Loading', 'Unloading']:
                    mid_time = start_time + (end_time - start_time) / 2
                    annotation = f"{phase}\n"
                    if phase == 'Loading':
                        annotation += f"Plant {trip['plant_id']}"
                    else:
                        annotation += f"Order {trip['order_id']}"
                    ax.text(
                        mdates.date2num(mid_time),
                        i,
                        annotation,
                        va='center',
                        ha='center',
                        fontsize=8,
                        color='black'
                    )

    # Create legend
    patches = [mpatches.Patch(color=color, label=phase) for phase, color in phase_colors.items()]
    ax.legend(handles=patches, loc='upper right')

    # Set labels and title
    ax.set_xlabel('Time')
    ax.set_title('Assigned Trips Gantt Chart')
    ax.grid(True, which='both', axis='x', linestyle='--', alpha=0.5)

    # Adjust x-axis limits
    if assigned_trips:
        earliest_start = min(datetime.strptime(trip['start_at'], '%Y-%m-%d %H:%M:%S') for trip in assigned_trips)
        latest_end = max(datetime.strptime(trip['return_at'], '%Y-%m-%d %H:%M:%S') for trip in assigned_trips)
        ax.set_xlim(
            mdates.date2num(earliest_start) - 0.01,
            mdates.date2num(latest_end) + 0.01
        )

    plt.tight_layout()
    plt.show()


# Example usage
if __name__ == "__main__":
    case_name = input("Введите название кейса: ")
    with open(f'data/{case_name}/results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)

    visualize_assigned_trips(results['assigned_trips'])
