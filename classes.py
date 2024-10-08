# classes.py

from datetime import datetime, timedelta
from collections import defaultdict

from datetime import datetime, timedelta


class Plant:
    def __init__(self, id, latitude, longitude, work_time_start, work_time_end, loading_capacity=2,
                 loading_time=15, loading_schedule=None):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.work_time_start = datetime.combine(datetime.today(), datetime.strptime(work_time_start, '%H:%M:%S').time())
        self.work_time_end = datetime.combine(datetime.today(), datetime.strptime(work_time_end, '%H:%M:%S').time())
        self.loading_capacity = loading_capacity
        self.loading_time = timedelta(minutes=loading_time)  # Время загрузки одной машины
        self.loading_schedule = loading_schedule if loading_schedule is not None else {}

    def is_loading_slot_available(self, loading_start, loading_end):
        for order_id, slot in self.loading_schedule.items():
            if not (loading_start >= slot['end'] or loading_end <= slot['start']):
                return False
        return True

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
        start = trip.start_at
        end = start + self.loading_time
        self.loading_schedule[trip.id] = {'start': start, 'end': end}


class Vehicle:
    def __init__(self, id, number, volume, rent, gidrolotok, axes, work_time_start, work_time_end, plants, plant_start, schedule=None):
        self.id = id
        self.number = number
        self.volume = volume
        self.rent = rent
        self.gidrolotok = gidrolotok
        self.axes = axes
        self.work_time_start = datetime.combine(datetime.today(), datetime.strptime(work_time_start, '%H:%M:%S').time())
        self.work_time_end = datetime.combine(datetime.today(), datetime.strptime(work_time_end, '%H:%M:%S').time())
        self.plants = plants
        self.schedule = schedule if schedule is not None else []
        self.plant_start = plant_start

    def is_available(self, trip):
        """
        Проверяет доступность транспортного средства на весь период поездки.
        """
        # Проверка рабочих часов
        if not (self.work_time_start <= trip.start_at <= self.work_time_end and
                self.work_time_start <= trip.unload_at <= self.work_time_end):
            return False

        # Проверка, что водитель может загрузиться на заводе
        if trip.plant_id not in self.plants:
            return False

        intervals = []
        plant_intervals = []
        if len(self.schedule) == 0:
            intervals = [(self.work_time_start, self.work_time_end)]
            plant_intervals = [(self.plant_start, None)]
        else:
            for i, tr in enumerate(self.schedule):
                if i == 0:
                    intervals.append((self.work_time_start, tr.start_at))
                    plant_intervals.append((self.plant_start, self.schedule[i].plant_id))
                else:
                    intervals.append((self.schedule[i - 1].return_at, tr.start_at))
                    plant_intervals.append((self.schedule[i - 1].return_plant_id, self.schedule[i].plant_id))
            intervals.append((self.schedule[-1].return_at, self.work_time_end))
            plant_intervals.append((self.schedule[-1].return_plant_id, None))

        def equal_plants(pl1, pl2):
            if pl1 is None or pl2 is None:
                return True
            return pl1 == pl2

        for i, interval in enumerate(intervals):
            start, end = interval
            plant_start, plant_end = plant_intervals[i]

            if (start <= trip.start_at) and (trip.return_at <= end) and (equal_plants(plant_start, trip.plant_id) and equal_plants(trip.return_plant_id, plant_end)):
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
    def __init__(self, order_id, plant_id, delivery_address_id, vehicle_id,
                 confirm, total, start_at, load_at, arrive_at, unload_at,
                 return_at, status, return_plant_id, plan_date_start,
                 plan_date_object, plan_date_done):
        self.id = f"{order_id}_{arrive_at}"
        self.order_id = order_id
        self.plant_id = plant_id
        self.delivery_address_id = delivery_address_id
        self.vehicle_id = vehicle_id
        self.confirm = confirm
        self.total = total
        self.start_at = start_at
        self.load_at = load_at
        self.arrive_at = arrive_at
        self.unload_at = unload_at
        self.return_at = return_at
        self.status = status
        self.return_plant_id = return_plant_id
        self.plan_date_start = plan_date_start
        self.plan_date_object = plan_date_object
        self.plan_date_done = plan_date_done

    def shift(self, time_shift):
        self.start_at += time_shift
        self.load_at += time_shift
        self.arrive_at += time_shift
        self.unload_at += time_shift
        self.return_at += time_shift


    #make JSON serializable
    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "plant_id": self.plant_id,
            "vehicle_id": self.vehicle_id,
            "confirm": self.confirm,
            "total": self.total,
            "start_at": self.start_at.strftime('%Y-%m-%d %H:%M:%S'),
            "load_at": self.load_at.strftime('%Y-%m-%d %H:%M:%S'),
            "arrive_at": self.arrive_at.strftime('%Y-%m-%d %H:%M:%S'),
            "unload_at": self.unload_at.strftime('%Y-%m-%d %H:%M:%S'),
            "return_at": self.return_at.strftime('%Y-%m-%d %H:%M:%S'),
            "status": self.status,
            "return_plant_id": self.return_plant_id,
            "plan_date_start": self.plan_date_start,
            "plan_date_object": self.plan_date_object.strftime('%Y-%m-%d %H:%M:%S'),
            "plan_date_done": self.plan_date_done
        }
