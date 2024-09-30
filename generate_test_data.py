# generate_test_data.py

import json
import random
from datetime import datetime, timedelta

order_counter = 0


def generate_plants(num_factories=2, plants_per_address=2):
    plants = []
    for factory_id in range(1, num_factories + 1):
        for pid in range(1, plants_per_address+1):
            plant = {
                "id": (factory_id-1) * plants_per_address + pid,
                "latitude": round(random.uniform(55.0, 60.0), 6),
                "longitude": round(random.uniform(50.0, 60.0), 6),
                "work_time_start": "09:00:00",
                "work_time_end": "18:00:00",
                "factory_id": factory_id,
            }
            plants.append(plant)
    return plants


def generate_vehicles(num_vehicles, plants):
    vehicles = []
    for i in range(1, num_vehicles + 1):
        factories = list(set([plant["factory_id"] for plant in plants]))
        factories_work_with = random.sample(factories, k=random.randint(1, len(factories)))
        vehicle = {
            "id": i,
            "number": f"H{random.randint(100,999)}KK{random.randint(100,999)}",
            "volume": random.choice([8, 10, 12]),
            "rent": random.choice([True, False]),
            "gidrolotok": random.choice([True, False]),
            "axes": random.choice([4, 6]),
            "work_time_start": "09:00:00",
            "work_time_end": "18:00:00",
            "factories": factories_work_with,
            "factory_start": random.choice(factories_work_with)
        }
        vehicles.append(vehicle)
    return vehicles


def generate_customer_orders(customer_id, num_orders, plants):
    global order_counter
    orders = []
    for i in range(1, num_orders + 1):
        order = {
            "id": order_counter,
            "status": "new",
            "total": 100,
            "date_shipment": datetime.today().strftime('%Y-%m-%d'),
            "first_order_time_delivery": random.choice(["09:00:00", "10:00:00", "11:00:00"]),
            "time_unloading": random.randint(20, 60),
            "type_delivery": random.choice(["withInterval", "withoutInterval"]),
            "time_interval_client": random.randint(15, 60),
            "axle": random.choice([4, 6]),
            "gidrolotok": random.choice([True, False]),
            "plants": random.sample([plant["id"] for plant in plants], k=random.randint(1, len(plants))),
            "delivery_address_id": customer_id,
            "intensity": random.randint(20, 70),
            "strategy": {
                "type": random.choice(["minimum_vehicles", "evenly", "equal_volume"]),
                "parameters": {
                }
            }
        }
        if order['strategy']['type'] == "equal_volume":
            order['strategy']['parameters']['volume'] = random.randint(8, 12)
        elif order['strategy']['type'] == "evenly":
            order['strategy']['parameters']['volume'] = random.randint(8, 12)
        order_counter += 1
        orders.append(order)
    return orders


def generate_customers(num_customers, plants, num_orders=1):
    customers = []
    for i in range(1, num_customers + 1):
        customer = {
            "id": i,
            "delivery_address_id": i,
            "orders": generate_customer_orders(customer_id=i, num_orders=num_orders, plants=plants)
        }
        customers.append(customer)
    return customers


def generate_travel_times(plants, customers):
    travel_times = []
    mem = {}
    for plant in plants:
        for customer in customers:
            travel_time = mem.get((plant['factory_id'], customer['id']), random.randint(10, 45))
            mem[(plant['factory_id'], customer['id'])] = travel_time
            travel_time_entry = {
                "plant_id": plant['id'],
                "customer_id": customer["id"],
                "travel_time_minutes": travel_time
            }
            travel_times.append(travel_time_entry)
    return travel_times


def generate_existing_trips(customers, plants, vehicles, num_trips=3):
    trips = []
    for i in range(num_trips):
        customer = random.choice(customers)
        plant = random.choice(plants)
        vehicle = random.choice(vehicles)

        start_at = datetime.today().replace(hour=random.randint(11, 15), minute=random.randint(0, 59))

        trip = {
            "order_id": random.choice(customer['orders'])['id'],
            "plant_id": plant['id'],
            "factory_id": plant['factory_id'],
            "vehicle_id": vehicle['id'],
            "start_at": start_at.strftime('%Y-%m-%d %H:%M:%S'),
            "load_at": (start_at + timedelta(minutes=random.randint(5, 15))).strftime('%Y-%m-%d %H:%M:%S'),
            "arrive_at": (start_at + timedelta(minutes=random.randint(20, 45))).strftime('%Y-%m-%d %H:%M:%S'),
            "unload_at": (start_at + timedelta(minutes=random.randint(50, 70))).strftime('%Y-%m-%d %H:%M:%S'),
            "return_at": (start_at + timedelta(minutes=random.randint(75, 90))).strftime('%Y-%m-%d %H:%M:%S'),
            "status": "reserved",
        }
        trips.append(trip)
    return trips


def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main():
    case_name = input("Введите название тестового случая: ")
    with open(f'data/{case_name}/config.json', 'r') as f:
        config = json.load(f)

    plants = generate_plants(num_factories=config['num_factories'], plants_per_address=config['plants_per_address'])
    vehicles = generate_vehicles(num_vehicles=config['num_vehicles'], plants=plants)
    customers = generate_customers(num_customers=config['num_customers'], plants=plants, num_orders=config['num_orders'])
    travel_times = generate_travel_times(plants, customers)
    trips = generate_existing_trips(customers, plants, vehicles, num_trips=config['num_trips'])


    path = f'data/{case_name}'
    # Сохранение данных в JSON-файлы
    save_json(plants, f'{path}/plants.json')
    save_json(vehicles, f'{path}/vehicles.json')
    save_json(customers, f'{path}/customers.json')
    save_json(travel_times, f'{path}/travel_times.json')
    save_json(trips, f'{path}/trips.json')

    print(f"Тестовые данные успешно сгенерированы и сохранены в папке {path}.")

if __name__ == "__main__":
    main()
