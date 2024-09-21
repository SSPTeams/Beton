# generate_test_data.py

import json
import random
from datetime import datetime, timedelta

def generate_plants(num_factories=2, plants_per_factory=2):
    plants = []
    plant_id = 1
    for factory_id in range(1, num_factories + 1):
        for _ in range(plants_per_factory):
            plant = {
                "id": plant_id,
                "factory_id": factory_id,
                "latitude": round(random.uniform(55.0, 60.0), 6),
                "longitude": round(random.uniform(50.0, 60.0), 6),
                "work_time_start": "09:00:00",
                "work_time_end": "18:00:00"
            }
            plants.append(plant)
            plant_id += 1
    return plants

def generate_vehicles(num_vehicles=10, mixers=None):
    if mixers is None:
        mixers = list(range(1, 5))  # Предположим, есть 4 завода
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
            "mixers": random.sample(mixers, k=random.randint(1, len(mixers)))
        }
        vehicles.append(vehicle)
    return vehicles


def generate_customer_orders(num_orders=10, num_vehicles=15, customer_ids=None):
    if customer_ids is None:
        customer_ids = list(range(1, 4))  # Предположим, есть 3 клиента
    mixers = list(range(1, 5))  # 4 завода
    orders = []
    for i in range(1, num_orders + 1):
        order = {
            "id": i,
            "good_id": random.randint(10, 20),
            "good_mix_time": [
                {
                    "mixer_id": mixer_id,
                    "mix_time": random.randint(30, 150)
                } for mixer_id in mixers
            ],
            "status": random.choice(["new", "work"]),
            "total": random.randint(50, 200),
            "work": random.randint(0, 50),
            "wait": random.randint(10, 150),
            "date_shipment": (datetime.today() + timedelta(days=random.randint(1, 10))).strftime('%Y-%m-%d'),
            "first_order_time_delivery": random.choice(["09:00:00", "10:00:00", "11:00:00"]),
            "time_unloading": random.randint(20, 60),
            "type_delivery": random.choice(["withoutInterval", "withInterval"]),
            "time_interval_client": random.randint(15, 60),
            "axle": random.choice([4, 6]),
            "gidrolotok": random.choice([True, False]),
            "mixers": random.sample(mixers, k=random.randint(1, len(mixers))),
            "vehicles": random.sample(range(1, num_vehicles + 1), k=random.randint(1, 3)),
            "delivery_address_id": random.choice(customer_ids)
        }
        orders.append(order)
    return orders

def generate_travel_times(plants, customers):
    travel_times = []
    for plant in plants:
        for customer_id in customers:
            travel_time = random.randint(15, 45)  # Время пути в минутах
            travel_time_entry = {
                "plant_id": plant['id'],
                "customer_id": customer_id,
                "travel_time_minutes": travel_time
            }
            travel_times.append(travel_time_entry)
    return travel_times

def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    # Генерация данных
    num_factories = 2
    plants_per_factory = 2
    plants = generate_plants(num_factories=num_factories, plants_per_factory=plants_per_factory)
    mixers = [plant['id'] for plant in plants]
    num_vehicles = 10
    vehicles = generate_vehicles(num_vehicles=num_vehicles, mixers=mixers)
    customer_ids = list(range(1, 4))  # 3 клиента
    num_orders = 10
    customer_orders = generate_customer_orders(num_orders=num_orders, customer_ids=customer_ids)
    travel_times = generate_travel_times(plants, customer_ids)

    # Сохранение данных в JSON-файлы
    save_json(plants, 'data/plants.json')
    save_json(vehicles, 'data/vehicles.json')
    save_json(customer_orders, 'data/customer_orders.json')
    save_json(travel_times, 'data/travel_times.json')

    print("Тестовые данные успешно сгенерированы и сохранены в папке 'data/'.")

if __name__ == "__main__":
    main()
