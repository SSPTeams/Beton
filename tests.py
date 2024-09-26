import json
from datetime import datetime
from collections import defaultdict


def parse_datetime(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')


def check_driver_schedule(assigned_trips):
    """
    Checks each driver's schedule for overlapping trips.
    """
    driver_violations = defaultdict(list)
    driver_schedules = defaultdict(list)

    # Organize trips by driver
    for trip in assigned_trips:
        vehicle_id = trip['vehicle_id']
        # Parse the start and end times of the trip (from loading start to return to plant)
        trip_start = parse_datetime(trip['start_at'])
        trip_end = parse_datetime(trip['return_at'])
        driver_schedules[vehicle_id].append((trip_start, trip_end, trip['id']))

    # Check for overlaps in each driver's schedule
    for driver, trips in driver_schedules.items():
        # Sort trips by start time
        trips.sort(key=lambda x: x[0])
        for i in range(len(trips) - 1):
            current_trip = trips[i]
            next_trip = trips[i + 1]
            current_end = current_trip[1]
            next_start = next_trip[0]
            # Check for overlap
            if current_end > next_start:
                driver_violations[driver].append({
                    'trip1_id': current_trip[2],
                    'trip2_id': next_trip[2],
                    'trip1_end': current_end.strftime('%Y-%m-%d %H:%M:%S'),
                    'trip2_start': next_start.strftime('%Y-%m-%d %H:%M:%S')
                })

    return driver_violations


def check_customer_unloadings(assigned_trips, order_to_customer_map):
    """
    Checks for overlapping unloadings at each customer's location.
    """
    customer_violations = defaultdict(list)
    customer_unloads = defaultdict(list)

    # Map trips to customers
    for trip in assigned_trips:
        order_id = trip['order_id']
        customer_id = order_to_customer_map.get(order_id)
        if customer_id is None:
            continue  # Skip if customer_id is not found
        # Parse the start and end times of unloading
        unload_start = parse_datetime(trip['arrive_at'])
        unload_end = parse_datetime(trip['unload_at'])
        customer_unloads[customer_id].append((unload_start, unload_end, trip['id']))

    # Check for overlaps at each customer's location
    for customer, unloads in customer_unloads.items():
        # Sort unloads by start time
        unloads.sort(key=lambda x: x[0])
        for i in range(len(unloads) - 1):
            current_unload = unloads[i]
            next_unload = unloads[i + 1]
            current_end = current_unload[1]
            next_start = next_unload[0]
            # Check for overlap
            if current_end > next_start:
                customer_violations[customer].append({
                    'trip1_id': current_unload[2],
                    'trip2_id': next_unload[2],
                    'unload1_end': current_end.strftime('%Y-%m-%d %H:%M:%S'),
                    'unload2_start': next_start.strftime('%Y-%m-%d %H:%M:%S')
                })

    return customer_violations

def main():
    # Load assigned_trips data
    with open('assigned_trips.json', 'r', encoding='utf-8') as f:
        assigned_trips = json.load(f)

    # Load customer_orders data to map order_id to customer_id
    with open('customer_orders.json', 'r', encoding='utf-8') as f:
        customer_orders = json.load(f)

    # Build a mapping from order_id to customer_id (delivery_address_id)
    order_to_customer_map = {}
    for order in customer_orders:
        order_id = order['id']
        customer_id = order['delivery_address_id']
        order_to_customer_map[order_id] = customer_id

    # Check driver's schedules
    driver_violations = check_driver_schedule(assigned_trips)
    if driver_violations:
        print("Driver Schedule Violations:")
        for driver, violations in driver_violations.items():
            print(f"\nDriver {driver}:")
            for violation in violations:
                print(f"  Trips {violation['trip1_id']} and {violation['trip2_id']} overlap.")
                print(f"    Trip {violation['trip1_id']} ends at {violation['trip1_end']}")
                print(f"    Trip {violation['trip2_id']} starts at {violation['trip2_start']}")
    else:
        print("No driver schedule violations found.")

    # Check customer unloadings
    customer_violations = check_customer_unloadings(assigned_trips, order_to_customer_map)
    if customer_violations:
        print("\nCustomer Unloading Violations:")
        for customer, violations in customer_violations.items():
            print(f"\nCustomer {customer}:")
            for violation in violations:
                print(f"  Trips {violation['trip1_id']} and {violation['trip2_id']} overlap during unloading.")
                print(f"    Trip {violation['trip1_id']} unloads until {violation['unload1_end']}")
                print(f"    Trip {violation['trip2_id']} starts unloading at {violation['unload2_start']}")
    else:
        print("\nNo customer unloading violations found.")


if __name__ == "__main__":
    main()
