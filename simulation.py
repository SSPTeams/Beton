# simulation.py

import copy
import random
from datetime import datetime, timedelta
from collections import defaultdict
from classes import Plant, Vehicle, Customer, Order, Trip


class Scheduler:
    def __init__(self, plants, vehicles, customers, travel_times):
        self.plants = copy.deepcopy(plants)  # Список объектов Plant
        self.vehicles = copy.deepcopy(vehicles)  # Список объектов Vehicle
        self.customers = copy.deepcopy(customers)  # Список объектов Customer
        self.travel_times = copy.deepcopy(travel_times)  # Словарь времени пути между заводами и заказчиками

        # Предварительное вычисление вероятностей выбора завода на основе обратной зависимости от времени пути
        self.plant_selection_probs = self.compute_plant_selection_probabilities()

        # Расписание разгрузок для каждого заказчика
        self.customer_unload_schedule = defaultdict(int)  # ключ: (customer_id, datetime), значение: количество разгрузок

    def compute_plant_selection_probabilities(self):
        """
        Вычисление нормализованных вероятностей выбора каждого завода на основе среднего времени пути.
        Ближайшие заводы имеют более высокие вероятности.
        """
        plant_weights = {}
        for plant in self.plants:
            # Вычисление среднего времени пути от завода до всех заказчиков
            total_time = 0
            count = 0
            for customer in self.customers:
                key = (plant.id, customer.delivery_address_id)
                if key in self.travel_times:
                    total_time += self.travel_times[key].total_seconds()
                    count += 1
            average_time = total_time / count if count > 0 else 1  # Избегаем деления на ноль
            plant_weights[plant.id] = 1 / (average_time + 1e-6)  # Обратная зависимость

        # Нормализация весов для получения вероятностей
        total_weight = sum(plant_weights.values())
        plant_probs = [plant_weights[plant.id] / total_weight for plant in self.plants]
        return plant_probs

    def choose_plant(self):
        """
        Выбор завода на основе предварительно вычисленных вероятностей.
        """
        plant_ids = [plant.id for plant in self.plants]
        chosen_plant_id = random.choices(plant_ids, weights=self.plant_selection_probs, k=1)[0]
        for plant in self.plants:
            if plant.id == chosen_plant_id:
                return plant
        return random.choice(self.plants)  # Резервный вариант

    def is_customer_available_for_unload(self, customer_id, arrival_time, unload_end):
        """
        Проверка доступности заказчика для разгрузки в заданный период.
        """
        # Проверяем, нет ли других разгрузок в данный момент
        current_time = arrival_time
        while current_time < unload_end:
            if self.customer_unload_schedule[(customer_id, current_time)] >= 1:
                return False
            current_time += timedelta(minutes=1)
        return True

    def reserve_customer_unload_slot(self, customer_id, arrival_time, unload_end):
        """
        Резервирование времени разгрузки у заказчика.
        """
        current_time = arrival_time
        while current_time < unload_end:
            self.customer_unload_schedule[(customer_id, current_time)] += 1
            current_time += timedelta(minutes=1)

    def schedule_trip(self, order, trip_volume):
        """
        Планирование одной поездки для данного заказа и объема.
        Возвращает объект Trip, если поездка успешно назначена, иначе None.
        """
        # Определение возможных транспортных средств для данного объема
        possible_vehicles = [v for v in self.vehicles if v.volume >= trip_volume]

        if not possible_vehicles:
            # Если нет транспортного средства с необходимой вместимостью
            order.failure_reasons.append("Нет транспортного средства с необходимой вместимостью")
            return None

        # Предпочтение транспортным средствам с минимальной вместимостью
        possible_vehicles.sort(key=lambda v: v.volume)

        for vehicle in possible_vehicles:
            # Определение заводов, с которых может грузить транспортное средство
            available_plants = [plant for plant in self.plants if plant.id in vehicle.mixers]
            for plant in available_plants:
                # Вычисление времени загрузки
                loading_start = datetime.combine(order.date_shipment, order.first_order_time_delivery)
                loading_end = loading_start + plant.loading_time

                # Проверка операционных часов завода
                if not (plant.work_time_start <= loading_start.time() <= plant.work_time_end and
                        plant.work_time_start <= loading_end.time() <= plant.work_time_end):
                    order.failure_reasons.append("Ограничение операционных часов завода")
                    continue

                # Проверка доступности слота для загрузки
                if not plant.is_loading_slot_available(loading_start, loading_end):
                    # Возможность корректировки времени загрузки
                    adjusted_loading_start = self.find_earliest_loading_time(plant, loading_start, order)
                    if adjusted_loading_start:
                        loading_start = adjusted_loading_start
                        loading_end = loading_start + plant.loading_time
                    else:
                        continue

                # Вычисление времени прибытия и окончания разгрузки
                key = (plant.id, order.delivery_address_id)
                travel_time = self.travel_times.get(key, timedelta(minutes=30))
                arrival_time = loading_end + travel_time
                unload_end = arrival_time + order.time_unloading

                # Проверка доступности заказчика для разгрузки
                if not self.is_customer_available_for_unload(order.delivery_address_id, arrival_time, unload_end):
                    # Возможность корректировки времени разгрузки
                    adjusted_arrival_time = self.find_earliest_unload_time(order.delivery_address_id, arrival_time, unload_end)
                    if adjusted_arrival_time:
                        unload_end = adjusted_arrival_time + order.time_unloading
                        arrival_time = adjusted_arrival_time
                        loading_end = arrival_time - travel_time
                        loading_start = loading_end - plant.loading_time
                        # Проверка операционных часов завода после корректировки
                        if not (plant.work_time_start <= loading_start.time() <= plant.work_time_end and
                                plant.work_time_start <= loading_end.time() <= plant.work_time_end):
                            order.failure_reasons.append("Ограничение операционных часов завода после корректировки")
                            continue
                        # Проверка доступности слота для загрузки в новом времени
                        if not plant.is_loading_slot_available(loading_start, loading_end):
                            continue
                    else:
                        continue

                # Резервирование слота для загрузки и разгрузки
                plant.reserve_loading_slot(loading_start, loading_end)
                self.reserve_customer_unload_slot(order.delivery_address_id, arrival_time, unload_end)

                # Вычисление времени возвращения на завод
                return_at = unload_end + travel_time

                # Создание объекта Trip
                trip = Trip(
                    order_id=order.id,
                    good_id=order.good_id,
                    plant_id=plant.id,  # Теперь plant_id вместо mixer_id
                    vehicle_id=vehicle.id,
                    mix_order_group_id=order.id,
                    confirm=False,
                    total=trip_volume,
                    start_at=loading_start.strftime('%Y-%m-%d %H:%M:%S'),
                    load_at=loading_end.strftime('%Y-%m-%d %H:%M:%S'),
                    arrive_at=arrival_time.strftime('%Y-%m-%d %H:%M:%S'),
                    unload_at=unload_end.strftime('%Y-%m-%d %H:%M:%S'),
                    return_at=return_at.strftime('%Y-%m-%d %H:%M:%S'),
                    status='new',
                    return_factory_id=plant.id,
                    plan_date_start=loading_start.strftime('%Y-%m-%d %H:%M:%S'),
                    plan_date_object=arrival_time.strftime('%Y-%m-%d %H:%M:%S'),
                    plan_date_done=return_at.strftime('%Y-%m-%d %H:%M:%S')
                )

                # Назначение поездки транспортному средству
                vehicle.assign_trip({
                    'loading_start': loading_start,
                    'loading_end': loading_end,
                    'plant': plant.id,
                    'travel_time': travel_time,
                    'arrival_time': arrival_time,
                    'unload_end': unload_end,
                    'customer': order.delivery_address_id,
                    'volume': trip_volume,
                    'scheduled_delivery_time': order.first_order_time_delivery,
                    'return_at': return_at
                })

                # Назначение поездки заказу
                order.assigned_trips.append(trip)
                order.wait -= trip_volume

                return trip

    def find_earliest_loading_time(self, plant, desired_loading_start, order):
        """
        Поиск ближайшего предыдущего времени загрузки, которое возможно и не нарушает время доставки.
        """
        current_time = desired_loading_start - timedelta(minutes=1)
        while current_time.time() >= plant.work_time_start:
            loading_start = current_time
            loading_end = loading_start + plant.loading_time
            if plant.is_loading_slot_available(loading_start, loading_end):
                return loading_start
            current_time -= timedelta(minutes=1)
        return None

    def find_earliest_unload_time(self, customer_id, desired_arrival_time, unload_end):
        """
        Поиск ближайшего доступного времени разгрузки для заказчика.
        """
        current_time = unload_end
        max_time = datetime.combine(desired_arrival_time.date(), datetime.strptime('23:59:59', '%H:%M:%S').time())
        while current_time <= max_time:
            if self.is_customer_available_for_unload(customer_id, current_time, current_time + self.current_order.time_unloading):
                return current_time
            current_time += timedelta(minutes=1)
        return None

    def simulate(self):
        """
        Запуск одной симуляции.
        Возвращает метрики и текущее состояние транспортных средств и заказов.
        """
        all_orders = []
        for customer in self.customers:
            for order in customer.orders:
                if order.status in ['new', 'work']:
                    all_orders.append(order)
        # Сортировка заказов по дате и времени доставки
        all_orders.sort(key=lambda x: (x.date_shipment, x.first_order_time_delivery))

        # Планирование поездок для каждого заказа
        deliveries = []
        for order in all_orders:
            self.current_order = order  # Для доступа в других методах
            while order.wait > 0:
                # Планируем поездку с объемом, равным минимуму из оставшегося объема и максимальной вместимости машины
                trip_volume = min(order.wait, 12)  # Максимальная вместимость машины
                trip = self.schedule_trip(order, trip_volume)
                if trip is None:
                    break  # Не удалось назначить поездку
                deliveries.append(trip.__dict__)

        # Вычисление метрик
        metrics = self.calculate_metrics()

        return {
            'metrics': metrics,
            'vehicles': self.vehicles,
            'customers': self.customers,
            'deliveries': deliveries
        }

    def calculate_metrics(self):
        """
        Вычисление метрик симуляции:
        - Среднее отклонение времени доставки
        - Утилизация транспортных средств
        - Не доставленный объем
        """
        total_time_deviation = timedelta()
        total_deliveries = 0
        undelivered_volume = 0

        for customer in self.customers:
            for order in customer.orders:
                if order.assigned_trips:
                    for trip in order.assigned_trips:
                        scheduled_delivery_datetime = datetime.combine(order.date_shipment, order.first_order_time_delivery)
                        actual_delivery_time = datetime.strptime(trip.arrive_at, '%Y-%m-%d %H:%M:%S')
                        deviation = abs(actual_delivery_time - scheduled_delivery_datetime)
                        total_time_deviation += deviation
                        total_deliveries += 1
                if order.wait > 0:
                    undelivered_volume += order.wait
                    total_deliveries += 1
                    total_time_deviation += timedelta(hours=10)  # Штрафное время

        average_time_deviation = total_time_deviation / total_deliveries if total_deliveries > 0 else timedelta()

        # Утилизация транспортных средств
        total_vehicle_work_time = timedelta()
        total_vehicle_available_time = timedelta()

        for vehicle in self.vehicles:
            work_time = timedelta()
            for trip in vehicle.schedule:
                trip_start = trip['loading_start']
                trip_end = trip['return_at']
                work_time += (trip_end - trip_start)
            vehicle_total_time = datetime.combine(datetime.today(), vehicle.work_time_end) - datetime.combine(datetime.today(), vehicle.work_time_start)
            total_vehicle_work_time += work_time
            total_vehicle_available_time += vehicle_total_time

        driver_utilization = (total_vehicle_work_time / total_vehicle_available_time) * 100 if total_vehicle_available_time > timedelta() else 0

        # Компиляция метрик
        metrics = {
            'average_time_deviation': average_time_deviation,
            'driver_utilization': driver_utilization,
            'undelivered_volume': undelivered_volume
        }

        return metrics
