# generate_test_data.py

import json
import random
from datetime import datetime, timedelta

order_counter = 0


def generate_plants(num_plants=2):
    plants = []
    for pid in range(1, num_plants+1):
        plant = {
            "id": pid,
            "latitude": round(random.uniform(55.0, 60.0), 6),
            "longitude": round(random.uniform(50.0, 60.0), 6),
            "work_time_start": "09:00:00",
            "work_time_end": "18:00:00"
        }
        plants.append(plant)
    return plants


def generate_vehicles(num_vehicles, plants):
    vehicles = []
    for i in range(1, num_vehicles + 1):
        vehicle = {
            "id": i,
            "number": f"H{random.randint(100,999)}KK{random.randint(100,999)}",
            "volume": random.choice([8, 10, 12]),
            "rent": random.choice([True, False]),
            "gidrolotok": random.choice([True, False]),
            "axes": random.choice([4, 6]),
            "work_time_start": "09:00:00",
            "work_time_end": "18:00:00",
            "plants": random.sample([plant['id'] for plant in plants], k=random.randint(1, len(plants)))
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
            "total": random.randint(50, 200),
            "date_shipment": datetime.today().strftime('%Y-%m-%d'),
            "first_order_time_delivery": random.choice(["09:00:00", "10:00:00", "11:00:00"]),
            "time_unloading": random.randint(20, 60),
            "type_delivery": "withInterval",
            "time_interval_client": random.randint(15, 60),
            "axle": random.choice([4, 6]),
            "gidrolotok": random.choice([True, False]),
            "plants": random.sample([plant["id"] for plant in plants], k=random.randint(1, len(plants))),
            "delivery_address_id": customer_id
        }
        order_counter += 1
        orders.append(order)
    return orders


def generate_customers(num_customers, plants):
    customers = []
    for i in range(1, num_customers + 1):
        customer = {
            "id": i,
            "delivery_address_id": i,
            "orders": generate_customer_orders(customer_id=i, num_orders=1, plants=plants)
        }
        customers.append(customer)
    return customers


def generate_travel_times(plants, customers):
    travel_times = []
    for plant in plants:
        for customer in customers:
            travel_time = random.randint(15, 45)
            travel_time_entry = {
                "plant_id": plant['id'],
                "customer_id": customer["id"],
                "travel_time_minutes": travel_time
            }
            travel_times.append(travel_time_entry)
    return travel_times


def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main():
    case_name = input("Введите название тестового случая: ")
    with open(f'data/{case_name}/config.json', 'r') as f:
        config = json.load(f)

    plants = generate_plants(num_plants=config['num_plants'])
    vehicles = generate_vehicles(num_vehicles=config['num_vehicles'], plants=plants)
    customers = generate_customers(num_customers=config['num_customers'], plants=plants)
    travel_times = generate_travel_times(plants, customers)


    path = f'data/{case_name}'
    # Сохранение данных в JSON-файлы
    save_json(plants, f'{path}/plants.json')
    save_json(vehicles, f'{path}/vehicles.json')
    save_json(customers, f'{path}/customers.json')
    save_json(travel_times, f'{path}/travel_times.json')

    print(f"Тестовые данные успешно сгенерированы и сохранены в папке {path}.")

if __name__ == "__main__":
    main()
