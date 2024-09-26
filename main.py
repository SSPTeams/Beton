# main.py
import copy
import json
from datetime import datetime, timedelta
from classes import Plant, Vehicle, Customer, Order
from simulation import Scheduler
import cProfile


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
            factories=vehicle['factories'],
            factory_start=vehicle['factory_start']
        )
        vehicles.append(v)
    return vehicles


def create_customers(customers_data):
    customers = []
    for customer in customers_data:
        new_customer = Customer(
            id=customer['id'],
            delivery_address_id=customer['delivery_address_id']
        )
        for order in customer.get('orders', []):
            customer_id = order['delivery_address_id']
            o = Order(
                id=order['id'],
                status="new",
                total=order['total'],
                date_shipment=order['date_shipment'],  # Уже преобразовано в дату в классе
                first_order_time_delivery=order['first_order_time_delivery'],  # Уже преобразовано в время в классе
                time_unloading=order['time_unloading'],
                type_delivery=order['type_delivery'],
                time_interval_client=order['time_interval_client'],
                axle=order['axle'],
                gidrolotok=order['gidrolotok'],
                plants=order['plants'],
                delivery_address_id=order['delivery_address_id']
            )
            new_customer.add_order(o)
        customers.append(new_customer)
    return customers


def create_travel_times(travel_times_data):
    travel_times = {}
    for entry in travel_times_data:
        key = (entry['plant_id'], entry['customer_id'])
        travel_times[key] = timedelta(minutes=entry['travel_time_minutes'])
    return travel_times


def main():
    case_name = input("Введите название кейса: ")
    #case_name = 'case_2_2_2'
    path = f'data/{case_name}'
    # Пути к JSON-файлам
    plants_file = f'{path}/plants.json'
    vehicles_file = f'{path}/vehicles.json'
    customers_file = f'{path}/customers.json'
    travel_times_file = f'{path}/travel_times.json'

    # Загрузка данных из JSON
    plants_data = load_json_data(plants_file)
    vehicles_data = load_json_data(vehicles_file)
    customers_data = load_json_data(customers_file)
    travel_times_data = load_json_data(travel_times_file)

    # Создание объектов
    plants = create_plants(plants_data)
    vehicles = create_vehicles(vehicles_data)
    customers = create_customers(customers_data)
    travel_times = create_travel_times(travel_times_data)

    best_metric = None
    best_result = None
    for _ in range(5):
        # Создание объекта Scheduler и запуск симуляции
        scheduler = Scheduler(plants=plants, vehicles=vehicles, customers=customers, travel_times=travel_times)
        scheduler.simulate()

        if best_metric is None or scheduler.score() > best_metric:
            best_metric = scheduler.score()
            best_result = copy.deepcopy(scheduler)

    with open(f'data/{case_name}/results.json', 'w', encoding='utf-8') as f:
        obj_to_dump = {
            "assigned_trips": [trip.to_dict() for trip in best_result.assigned_trips],
            "failed_trips": best_result.failed_trips,
            "metrics": best_result.metrics
        }
        json.dump(obj_to_dump, f, ensure_ascii=False, indent=4)

    # Вывод метрик симуляции
    print("\nSimulation Metrics:")
    for k, v in best_result.metrics.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    main()

    profiler.disable()  # Остановка профилирования
    #profiler.print_stats(sort='time')  # Вывод результатов
