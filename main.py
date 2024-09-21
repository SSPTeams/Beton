# main.py

import json
from datetime import datetime, timedelta
from classes import Plant, Vehicle, Customer, Order
from simulation import Scheduler

def load_json_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_plants(plants_data):
    plants = []
    for plant in plants_data:
        p = Plant(
            id=plant['id'],
            factory_id=plant['factory_id'],
            latitude=plant['latitude'],
            longitude=plant['longitude'],
            work_time_start=plant['work_time_start'],
            work_time_end=plant['work_time_end']
        )
        plants.append(p)
    return plants

def create_vehicles(vehicles_data):
    vehicles = []
    for vehicle in vehicles_data:
        v = Vehicle(
            id=vehicle['id'],
            number=vehicle['number'],
            volume=vehicle['volume'],
            rent=vehicle['rent'],
            gidrolotok=vehicle['gidrolotok'],
            axes=vehicle['axes'],
            work_time_start=vehicle['work_time_start'],
            work_time_end=vehicle['work_time_end'],
            mixers=vehicle['mixers']
        )
        vehicles.append(v)
    return vehicles

def create_customers(orders_data):
    customers = {}
    for order in orders_data:
        customer_id = order['delivery_address_id']
        if customer_id not in customers:
            customers[customer_id] = Customer(id=customer_id, delivery_address_id=order['delivery_address_id'])
        o = Order(
            id=order['id'],
            good_id=order['good_id'],
            good_mix_time=order['good_mix_time'],
            status=order['status'],
            total=order['total'],
            work=order['work'],
            wait=order['wait'],
            date_shipment=order['date_shipment'],  # Уже преобразовано в дату в классе
            first_order_time_delivery=order['first_order_time_delivery'],  # Уже преобразовано в время в классе
            time_unloading=order['time_unloading'],
            type_delivery=order['type_delivery'],
            time_interval_client=order['time_interval_client'],
            axle=order['axle'],
            gidrolotok=order['gidrolotok'],
            mixers=order['mixers'],
            vehicles=order['vehicles'],
            delivery_address_id=order['delivery_address_id']
        )
        customers[customer_id].add_order(o)
    return list(customers.values())

def create_travel_times(travel_times_data):
    travel_times = {}
    for entry in travel_times_data:
        key = (entry['plant_id'], entry['customer_id'])
        travel_times[key] = timedelta(minutes=entry['travel_time_minutes'])
    return travel_times

def main():
    # Пути к JSON-файлам
    plants_file = 'data/plants.json'
    vehicles_file = 'data/vehicles.json'
    customer_orders_file = 'data/customer_orders.json'
    travel_times_file = 'data/travel_times.json'

    # Загрузка данных из JSON
    plants_data = load_json_data(plants_file)
    vehicles_data = load_json_data(vehicles_file)
    customer_orders_data = load_json_data(customer_orders_file)
    travel_times_data = load_json_data(travel_times_file)

    # Создание объектов
    plants = create_plants(plants_data)
    vehicles = create_vehicles(vehicles_data)
    customers = create_customers(customer_orders_data)
    travel_times = create_travel_times(travel_times_data)

    # Создание объекта Scheduler и запуск симуляции
    scheduler = Scheduler(plants=plants, vehicles=vehicles, customers=customers, travel_times=travel_times)
    simulation_result = scheduler.simulate()

    # Сохранение отгрузок в deliveries.json
    with open('data/deliveries.json', 'w', encoding='utf-8') as f:
        json.dump(simulation_result['deliveries'], f, ensure_ascii=False, indent=4)

    # Вывод метрик симуляции
    print("\nSimulation Metrics:")
    print(f"Average Time Deviation: {simulation_result['metrics']['average_time_deviation']}")
    print(f"Driver Utilization: {simulation_result['metrics']['driver_utilization']:.2f}%")
    print(f"Undelivered Volume: {simulation_result['metrics']['undelivered_volume']} m³")

if __name__ == "__main__":
    main()
