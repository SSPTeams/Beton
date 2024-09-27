# classes.py

from datetime import datetime, timedelta
from collections import defaultdict

from datetime import datetime, timedelta


class Plant:
    def __init__(self, id, factory_id, latitude, longitude, work_time_start, work_time_end, loading_capacity=2,
                 loading_time=15, loading_schedule=None):
        self.id = id
        self.factory_id = factory_id
        self.latitude = latitude
        self.longitude = longitude
        self.work_time_start = datetime.combine(datetime.today(), datetime.strptime(work_time_start, '%H:%M:%S').time())
        self.work_time_end = datetime.combine(datetime.today(), datetime.strptime(work_time_end, '%H:%M:%S').time())
        self.loading_capacity = loading_capacity
        self.loading_time = timedelta(minutes=loading_time)  # Время загрузки одной машины
        self.loading_schedule = loading_schedule if loading_schedule is not None else {}

    def get_first_available_slot(self, time_from=None):
        time_from = max(time_from, self.work_time_start) or self.work_time_start
        # Сортируем слоты по времени начала
        slots = sorted(self.loading_schedule.values(), key=lambda x: x['start'])
        possible_starts = [time_from] + [slot['end'] for slot in slots if slot['end'] >= time_from]
        slots_starts = [slot['start'] for slot in slots if slot['end'] >= time_from] + [self.work_time_end]

        for i in range(len(possible_starts)):
            proposed_start = possible_starts[i]
            proposed_end = proposed_start + self.loading_time

            # Проверяем, что proposed_end не превышает начало следующего слота
            if proposed_end <= slots_starts[i]:
                # Проверяем, находится ли слот в рабочее время
                if self.work_time_start <= proposed_start and proposed_end <= self.work_time_end:
                    return proposed_start
        return None

    def reserve_loading_slot(self, trip):
        start = trip.plant_arrive_at
        end = start + self.loading_time
        self.loading_schedule[trip.id] = {'start': start, 'end': end}


class Vehicle:
    def __init__(self, id, number, volume, rent, gidrolotok, axes, work_time_start, work_time_end, factories, factory_start, travel_times, schedule=None):
        self.id = id
        self.number = number
        self.volume = volume
        self.rent = rent
        self.gidrolotok = gidrolotok
        self.axes = axes
        self.work_time_start = datetime.combine(datetime.today(), datetime.strptime(work_time_start, '%H:%M:%S').time())
        self.work_time_end = datetime.combine(datetime.today(), datetime.strptime(work_time_end, '%H:%M:%S').time())
        self.factories = factories
        self.schedule = schedule if schedule is not None else []
        self.factory_start = factory_start
        self.travel_times = travel_times

    def is_available(self, trip):
        """
        Проверяет доступность транспортного средства на весь период поездки.
        """
        # Проверка рабочих часов
        if not (self.work_time_start <= trip.plant_arrive_at <= self.work_time_end and
                self.work_time_start <= trip.unload_at <= self.work_time_end):
            return False

        # Проверка, что водитель может загрузиться на заводе
        if trip.plant.factory_id not in self.factories:
            return False

        intervals = []
        customer_intervals = []
        if len(self.schedule) == 0:
            intervals = [(self.work_time_start, self.work_time_end)]
            customer_intervals = [(None, None)]
        else:
            for i, tr in enumerate(self.schedule):
                if i == 0:
                    intervals.append((self.work_time_start, tr.customer_start_at))
                    customer_intervals.append((None, self.schedule[i].delivery_start_id))
                else:
                    intervals.append((self.schedule[i - 1].unload_at, tr.customer_start_at))
                    customer_intervals.append((self.schedule[i - 1].order.delivery_address_id, self.schedule[i].delivery_start_id))
            intervals.append((self.schedule[-1].unload_at, self.work_time_end))
            customer_intervals.append((self.schedule[-1].order.delivery_address_id, None))

        def equal_deliveries(pl1, pl2):
            if pl1 is None or pl2 is None:
                return True
            return pl1 == pl2

        for i, interval in enumerate(intervals):
            start, end = interval
            plant_start, plant_end = customer_intervals[i]

            if (start <= trip.customer_start_at) and (trip.unload_at <= end) and (equal_deliveries(plant_start, trip.delivery_start_id) and equal_deliveries(trip.order.delivery_address_id, plant_end)):
                return True

        return False

    def assign_trip(self, trip):
        self.schedule.append(trip)


class Customer:
    def __init__(self, id, delivery_address_id):
        self.id = id
        self.delivery_address_id = delivery_address_id
        self.orders = []

    def add_order(self, order):
        self.orders.append(order)


class Order:
    def __init__(self, id, status, total,
                 date_shipment, first_order_time_delivery, time_unloading,
                 type_delivery, time_interval_client, axle, gidrolotok,
                 plants, delivery_address_id):
        self.id = id
        self.status = status
        self.total = total
        self.first_order_datetime_delivery = datetime.strptime(f"{date_shipment} {first_order_time_delivery}",
                                                               '%Y-%m-%d %H:%M:%S')
        self.time_unloading = timedelta(minutes=time_unloading)
        self.type_delivery = type_delivery
        self.time_interval_client = timedelta(minutes=time_interval_client)
        self.axle = axle
        self.gidrolotok = gidrolotok
        self.plants = plants
        self.delivery_address_id = delivery_address_id
        self.assigned_trips = []  # Список назначенных поездок
        self.failure_reasons = []  # Список причин, по которым доставка не была выполнена


class Trip:
    def __init__(self, order, plant, vehicle, confirm, total,
                 customer_start_at, plant_arrive_at, load_at, arrive_at, unload_at, status, delivery_start_id,
                 plan_date_object):
        self.id = f"{order.id}_{arrive_at}"
        self.order = order
        self.plant = plant
        self.vehicle = vehicle
        self.confirm = confirm
        self.total = total
        self.customer_start_at = customer_start_at
        self.plant_arrive_at = plant_arrive_at
        self.load_at = load_at
        self.arrive_at = arrive_at
        self.unload_at = unload_at
        self.delivery_start_id = delivery_start_id
        self.status = status
        self.plan_date_object = plan_date_object


    def shift(self, time_shift):
        if self.customer_start_at:
            self.customer_start_at += time_shift
        if self.plant_arrive_at:
            self.plant_arrive_at += time_shift
        if self.load_at:
            self.load_at += time_shift
        if self.arrive_at:
            self.arrive_at += time_shift
        if self.unload_at:
            self.unload_at += time_shift


    #make JSON serializable
    def to_dict(self):
        return {
            "id": self.id,
            "order": self.order.id,
            "plant": self.plant.id,
            "vehicle": self.vehicle.id,
            "confirm": self.confirm,
            "total": self.total,
            "customer_start_at": self.customer_start_at.strftime('%Y-%m-%d %H:%M:%S'),
            "plant_arrive_at": self.plant_arrive_at.strftime('%Y-%m-%d %H:%M:%S'),
            "load_at": self.load_at.strftime('%Y-%m-%d %H:%M:%S'),
            "arrive_at": self.arrive_at.strftime('%Y-%m-%d %H:%M:%S'),
            "unload_at": self.unload_at.strftime('%Y-%m-%d %H:%M:%S'),
            "status": self.status,
            "delivery_start_id": self.delivery_start_id,
            "plan_date_object": self.plan_date_object.strftime('%Y-%m-%d %H:%M:%S')
        }
