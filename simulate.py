import random
from datetime import datetime, timedelta
import copy
from collections import defaultdict
import pickle as pkl
from entities import *


if __name__ == "__main__":
    # Параметры симуляции
    num_simulations = 100  # Количество симуляций для запуска

    # Определение даты симуляции
    sim_date = datetime.now().date()

    # Определение рабочего времени заводов
    plant_start_time = datetime.combine(sim_date, datetime.min.time()) + timedelta(hours=6)  # 6:00 AM
    plant_end_time = datetime.combine(sim_date, datetime.min.time()) + timedelta(hours=18)  # 6:00 PM

    # Определение заводов
    base_plants = [
        Plant(
            name="Plant A",
            loading_capacity=2,  # 2 машины могут загружаться одновременно
            loading_time=timedelta(minutes=15),
            start_time=plant_start_time,
            end_time=plant_end_time
        ),
        Plant(
            name="Plant B",
            loading_capacity=2,  # 2 машины могут загружаться одновременно
            loading_time=timedelta(minutes=15),
            start_time=plant_start_time,
            end_time=plant_end_time
        )
    ]

    # Определение заказчиков и их заказов
    # Каждый заказ - это кортеж: (время доставки, объем)
    customer_orders = {
        "Customer 1": [
            (datetime.combine(sim_date, datetime.min.time()) + timedelta(hours=10, minutes=0), 50),
            (datetime.combine(sim_date, datetime.min.time()) + timedelta(hours=14, minutes=0), 50)
        ],
        "Customer 2": [
            (datetime.combine(sim_date, datetime.min.time()) + timedelta(hours=11, minutes=0), 50),
            (datetime.combine(sim_date, datetime.min.time()) + timedelta(hours=15, minutes=0), 50)
        ]
    }

    base_customers = [
        Customer(name="Customer 1", orders=customer_orders["Customer 1"]),
        Customer(name="Customer 2", orders=customer_orders["Customer 2"])
    ]

    # Определение водителей (всего 15: 5 по 8, 5 по 10 и 5 по 12)
    base_drivers = []
    capacities = [8, 10, 12]
    for cap in capacities:
        for i in range(1, 6):
            driver = Driver(
                name=f"Driver {cap}-{i}",
                capacity=cap,
                start_time=plant_start_time,
                end_time=plant_end_time
            )
            base_drivers.append(driver)

    # Определение времени пути (можно считать расстоянием)
    travel_times = {
        ("Plant A", "Customer 1"): timedelta(minutes=20),
        ("Plant A", "Customer 2"): timedelta(minutes=25),
        ("Plant B", "Customer 1"): timedelta(minutes=25),
        ("Plant B", "Customer 2"): timedelta(minutes=20)
    }

    # Хранение результатов всех симуляций
    all_simulations = []

    # Запуск нескольких симуляций
    for sim in range(num_simulations):
        # Создание одной симуляции с использованием deepcopy в конструкторе
        scheduler = Scheduler(drivers=base_drivers, plants=base_plants, customers=base_customers, travel_times=travel_times)
        simulation_result = scheduler.simulate()
        all_simulations.append(simulation_result)

    # Выбор лучшей симуляции на основе метрик
    # Критерии: Низкое среднее отклонение времени доставки, высокая утилизация водителей, минимальный не доставленный объем
    best_simulation = None
    best_metrics = None

    for sim_result in all_simulations:
        metrics = sim_result['metrics']
        if best_metrics is None:
            best_metrics = metrics
            best_simulation = sim_result
        else:
            if metrics['average_time_deviation'] < best_metrics['average_time_deviation']:
                best_metrics = metrics
                best_simulation = sim_result
            elif metrics['average_time_deviation'] == best_metrics['average_time_deviation']:
                if metrics['driver_utilization'] > best_metrics['driver_utilization']:
                    best_metrics = metrics
                    best_simulation = sim_result
                elif metrics['driver_utilization'] == best_metrics['driver_utilization']:
                    if metrics['undelivered_volume'] < best_metrics['undelivered_volume']:
                        best_metrics = metrics
                        best_simulation = sim_result

    # Вывод результатов лучшей симуляции
    print(f"\nBest Simulation Metrics:")
    print(f"Average Time Deviation: {best_metrics['average_time_deviation']}")
    print(f"Driver Utilization: {best_metrics['driver_utilization']:.2f}%")
    print(f"Undelivered Volume: {best_metrics['undelivered_volume']} m³")

    # Вывод расписания для каждого водителя
    for driver in best_simulation['drivers']:
        print(f"\nSchedule for {driver.name} (Capacity: {driver.capacity} m³):")
        if not driver.schedule:
            print("  No trips assigned.")
            continue
        # Сортировка поездок по времени начала загрузки
        sorted_trips = sorted(driver.schedule, key=lambda x: x['loading_start'])
        for trip in sorted_trips:
            loading_start_time = trip['loading_start'].strftime("%H:%M")
            loading_end_time = trip['loading_end'].strftime("%H:%M")
            arrival_time = trip['arrival_time'].strftime("%H:%M")
            unload_end_time = trip['unload_end'].strftime("%H:%M")
            return_at_time = trip['return_at'].strftime("%H:%M")
            scheduled_time = trip['scheduled_delivery_time'].strftime("%H:%M")
            print(f"  Load {trip['volume']} m³ at {trip['plant']} from {loading_start_time} to {loading_end_time}, "
                  f"deliver to {trip['customer']} arriving at {arrival_time}, unload until {unload_end_time}, "
                  f"returning at {return_at_time}, scheduled for {scheduled_time}")

    # Вывод не доставленных заказов с причинами
    undelivered = []
    for customer in best_simulation['customers']:
        for order in customer.orders:
            if order.remaining_volume > 0:
                undelivered.append({
                    'customer': customer.name,
                    'delivery_time': order.delivery_time.strftime("%H:%M"),
                    'undelivered_volume': order.remaining_volume,
                    'reasons': order.failure_reasons if order.failure_reasons else ["Unknown Reason"]
                })

    if undelivered:
        print("\nUndelivered Orders with Reasons:")
        for order in undelivered:
            reasons = "; ".join(order['reasons'])
            print(f"  {order['undelivered_volume']} m³ to {order['customer']} at {order['delivery_time']} was not delivered. Reason(s): {reasons}")
    else:
        print("\nAll orders were successfully delivered.")


    with open('best_simulation.pkl', 'wb') as f:
        pkl.dump(best_simulation, f)
