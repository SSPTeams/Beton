# classes.py

from datetime import datetime, timedelta
from collections import defaultdict


class Plant:
    def __init__(self, id, factory_id, latitude, longitude, work_time_start, work_time_end):
        self.id = id
        self.factory_id = factory_id
        self.latitude = latitude
        self.longitude = longitude
        self.work_time_start = datetime.strptime(work_time_start, '%H:%M:%S').time()
        self.work_time_end = datetime.strptime(work_time_end, '%H:%M:%S').time()
        self.loading_capacity = 2  # Предполагаемое количество машин, которые могут загружаться одновременно
        self.loading_time = timedelta(minutes=15)  # Время загрузки одной машины
        self.loading_schedule = defaultdict(int)  # Расписание загрузок: ключ = время, значение = количество занятых слотов

    def is_loading_slot_available(self, loading_start, loading_end):
        current_time = loading_start
        while current_time < loading_end:
            if self.loading_schedule[current_time] >= self.loading_capacity:
                return False
            current_time += timedelta(minutes=1)
        return True

    def reserve_loading_slot(self, loading_start, loading_end):
        current_time = loading_start
        while current_time < loading_end:
            self.loading_schedule[current_time] += 1
            current_time += timedelta(minutes=1)


# classes.py

class Vehicle:
    def __init__(self, id, number, volume, rent, gidrolotok, axes, work_time_start, work_time_end, mixers):
        self.id = id
        self.number = number
        self.volume = volume
        self.rent = rent
        self.gidrolotok = gidrolotok
        self.axes = axes
        self.work_time_start = datetime.strptime(work_time_start, '%H:%M:%S').time()
        self.work_time_end = datetime.strptime(work_time_end, '%H:%M:%S').time()
        self.mixers = mixers  # Список mixer_id, с которых может грузить
        self.schedule = []  # Список назначенных поездок

    def is_available(self, trip_start, trip_end):
        """
        Проверяет доступность транспортного средства на весь период поездки.
        """
        for trip in self.schedule:
            existing_start = trip['loading_start']
            existing_end = trip['return_at']
            # Проверка на пересечение интервалов
            if (trip_start < existing_end) and (trip_end > existing_start):
                return False
        # Проверка рабочих часов
        if not (self.work_time_start <= trip_start.time() <= self.work_time_end and
                self.work_time_start <= trip_end.time() <= self.work_time_end):
            return False
        return True

    def assign_trip(self, trip):
        self.schedule.append(trip)



class Customer:
    def __init__(self, id, delivery_address_id):
        self.id = id
        self.delivery_address_id = delivery_address_id
        self.orders = []  # Список объектов Order

    def add_order(self, order):
        self.orders.append(order)


class Order:
    def __init__(self, id, good_id, good_mix_time, status, total, work, wait,
                 date_shipment, first_order_time_delivery, time_unloading,
                 type_delivery, time_interval_client, axle, gidrolotok,
                 mixers, vehicles, delivery_address_id):
        self.id = id
        self.good_id = good_id
        self.good_mix_time = good_mix_time  # Список словарей с plant_id и mix_time
        self.status = status
        self.total = total
        self.work = work
        self.wait = wait
        self.date_shipment = datetime.strptime(date_shipment, '%Y-%m-%d').date()
        self.first_order_time_delivery = datetime.strptime(first_order_time_delivery, '%H:%M:%S').time()
        self.time_unloading = timedelta(minutes=time_unloading)
        self.type_delivery = type_delivery
        self.time_interval_client = timedelta(minutes=time_interval_client)
        self.axle = axle
        self.gidrolotok = gidrolotok
        self.mixers = mixers  # Список plant_id, с которых грузим
        self.vehicles = vehicles  # Список vehicle_id
        self.delivery_address_id = delivery_address_id
        self.assigned_trips = []  # Список назначенных поездок
        self.failure_reasons = []  # Список причин, по которым доставка не была выполнена


class Trip:
    def __init__(self, order_id, good_id, plant_id, vehicle_id, mix_order_group_id,
                 confirm, total, start_at, load_at, arrive_at, unload_at,
                 return_at, status, return_factory_id, plan_date_start,
                 plan_date_object, plan_date_done):
        self.id = order_id
        self.good_id = good_id
        self.plant_id = plant_id  # Теперь plant_id вместо mixer_id
        self.vehicle_id = vehicle_id
        self.mix_order_group_id = mix_order_group_id
        self.confirm = confirm
        self.total = total
        self.start_at = start_at
        self.load_at = load_at
        self.arrive_at = arrive_at
        self.unload_at = unload_at
        self.return_at = return_at
        self.status = status
        self.return_factory_id = return_factory_id
        self.plan_date_start = plan_date_start
        self.plan_date_object = plan_date_object
        self.plan_date_done = plan_date_done
