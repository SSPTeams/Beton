# simulation.py

import copy
import random
from datetime import timedelta, datetime

import numpy as np

from classes import Plant, Vehicle, Customer, Order, Trip


class Scheduler:
    def __init__(self, plants, vehicles, customers, travel_times):
        self.travel_times = copy.deepcopy(travel_times)
        self.customer_delivery_queue = []

        self.plants = {}
        for plant in plants:
            self.plants[plant.id] = plant

        self.vehicles = {}
        for vehicle in vehicles:
            self.vehicles[vehicle.id] = vehicle

        self.vehicles_end_time = max(vehicle.work_time_end for vehicle in vehicles)

        self.orders = {}
        self.customers = {}
        for customer in customers:
            self.customers[customer.id] = customer
            for order in customer.orders:
                self.orders[order.id] = copy.deepcopy(order)

        for order in self.orders.values():
            self.customer_delivery_queue.append(Trip(
                order_id=order.id,
                plant_id=None,
                factory_id=None,
                delivery_address_id=order.delivery_address_id,
                vehicle_id=None,
                confirm=False,
                total=None,
                start_at=None,
                load_at=None,
                arrive_at=order.first_order_datetime_delivery,
                unload_at=None,
                return_at=None,
                status="new",
                return_plant_id=None,
                return_factory_id=None,
                plan_date_start=None,
                plan_date_object=None,
                plan_date_done=None
            ))

        self.assigned_trips = []
        self.failed_trips = []
        self.metrics = None

    def get_trip_distance(self, trip):
        return self.travel_times[(trip.plant_id, trip.delivery_address_id)] + self.travel_times[(trip.return_plant_id, trip.delivery_address_id)]

    def simulate(self):
        def get_first_trip(trips):
            # get index of the trip with the earliest arrive_at
            first_trip = None
            res_index = None
            for i, trip in enumerate(trips):
                if not first_trip or trip.arrive_at < first_trip.arrive_at:
                    first_trip = trip
                    res_index = i
            return res_index

        while self.customer_delivery_queue:
            trip_ = self.customer_delivery_queue.pop(get_first_trip(self.customer_delivery_queue))
            new_trip, err = self.assign_trip(trip_)
            if not new_trip:
                self.failed_trips.append((new_trip, err))
                trip_.arrive_at = trip_.arrive_at + timedelta(minutes=10)
                if trip_.arrive_at < self.vehicles_end_time:
                    self.customer_delivery_queue.append(trip_)
                continue
            else:
                self.assigned_trips.append(new_trip)
                order = self.orders[new_trip.order_id]
                vehicle = self.vehicles[new_trip.vehicle_id]
                self.orders[new_trip.order_id].total -= new_trip.total
                if self.orders[new_trip.order_id].total == 0:
                    self.orders[new_trip.order_id].status = "done"
                else:
                    delivery_interval = order.time_interval_client if order.type_delivery == "withInterval" else order.time_unloading
                    self.customer_delivery_queue.append(Trip(
                        order_id=order.id,
                        plant_id=None,
                        factory_id=None,
                        delivery_address_id=order.delivery_address_id,
                        vehicle_id=None,
                        confirm=False,
                        total=None,
                        start_at=None,
                        load_at=None,
                        arrive_at=new_trip.arrive_at + delivery_interval,
                        unload_at=None,
                        return_at=None,
                        status="new",
                        return_plant_id=None,
                        return_factory_id=None,
                        plan_date_start=None,
                        plan_date_object=None,
                        plan_date_done=None

                    ))

        self.calculate_metrics()
        return self.assigned_trips, self.failed_trips

    def get_travel_time(self, start, end):
        return self.travel_times[(start, end)]

    def get_best_trip(self, trips):
        travel_times = [self.get_trip_distance(trip) for trip in trips]
        # randomly choose one of the best trips based on the minimum travel time (using probs)
        probs = [1 / (tt.total_seconds() / 60)**0.5 for tt in travel_times]
        best_trip = random.choices(trips, weights=probs)[0]
        return best_trip

    def assign_trip(self, trip):
        suitable_trips = []

        trip_variant = copy.deepcopy(trip)
        for v_id, vehicle in self.vehicles.items():
            for pto_id, plant_from in self.plants.items():
                for pfrom_id, plant_to in self.plants.items():
                    trip_variant.plant_id = plant_from.id
                    trip_variant.factory_id = plant_from.factory_id
                    trip_variant.arrive_at = trip.arrive_at
                    trip_variant.vehicle_id = vehicle.id
                    trip_variant.return_plant_id = plant_to.id
                    trip_variant.return_factory_id = plant_to.factory_id
                    trip_variant.total = min(vehicle.volume, self.orders[trip.order_id].total)

                    trip_variant.load_at = trip_variant.arrive_at - self.get_travel_time(start=plant_from.id, end=self.orders[trip.order_id].delivery_address_id)
                    trip_variant.start_at = trip_variant.load_at - self.plants[plant_from.id].loading_time
                    trip_variant.unload_at = trip_variant.arrive_at + self.orders[trip.order_id].time_unloading
                    trip_variant.return_at = trip_variant.unload_at + self.get_travel_time(end=self.orders[trip.order_id].delivery_address_id, start=plant_to.id)
                    trip_variant.plan_date_object = trip_variant.arrive_at

                    plant_slot_variant = plant_from.get_first_available_slot(trip_variant.start_at)
                    if plant_slot_variant is None:
                        continue

                    time_shift = plant_slot_variant - trip_variant.start_at
                    trip_variant.shift(time_shift)

                    if vehicle.is_available(trip_variant):
                        suitable_trips.append(copy.deepcopy(trip_variant))

        if not suitable_trips:
            return None, "No suitable trips"

        best_trip = self.get_best_trip(suitable_trips)

        self.plants[best_trip.plant_id].reserve_loading_slot(best_trip)
        self.vehicles[best_trip.vehicle_id].assign_trip(best_trip)

        return best_trip, None

    def compute_plants_utilization(self, trips):
        plant_utilization = {}
        for plant in self.plants.values():
            plant_utilization[plant.id] = 0
        for trip in trips:
            plant_utilization[trip.plant_id] += (trip.load_at - trip.start_at).total_seconds() / 60

        for plant in self.plants.values():
            plant_utilization[plant.id] = plant_utilization[plant.id] / ((plant.work_time_end - plant.work_time_start).total_seconds() / 60)
        return np.mean(list(plant_utilization.values()))

    def compute_vehicle_utilization(self, trips):
        vehicle_utilization = {}
        for vehicle in self.vehicles.values():
            vehicle_utilization[vehicle.id] = 0
        for trip in trips:
            vehicle_utilization[trip.vehicle_id] += (trip.return_at - trip.start_at).total_seconds() / 60

        for vehicle in self.vehicles.values():
            vehicle_utilization[vehicle.id] = vehicle_utilization[vehicle.id] / ((vehicle.work_time_end - vehicle.work_time_start).total_seconds() / 60)
        return np.mean(list(vehicle_utilization.values()))

    def calculate_metrics(self):
        self.metrics = {
            "Undelivered Volume": sum([order.total for order in self.orders.values()]),
            "Plan time delta": sum(
                                    abs((trip.arrive_at - trip.plan_date_object).total_seconds()) / 60
                                    for trip in self.assigned_trips
                                    if trip.arrive_at and trip.plan_date_object
                                ),
            "Plants utilization": self.compute_plants_utilization(self.assigned_trips),
            "Vehicles utilization": self.compute_vehicle_utilization(self.assigned_trips)
        }
        return self.metrics

    def score(self):
        return -self.metrics["Undelivered Volume"], -self.metrics["Plan time delta"]




