import random
from datetime import datetime, timedelta
import copy
from collections import defaultdict
import pickle as pkl

# Определение класса Заказ
class Order:
    def __init__(self, customer, delivery_time, volume):
        self.customer = customer
        self.delivery_time = delivery_time  # Желаемое время прибытия машины к заказчику
        self.volume = volume  # Общий объем бетона для доставки
        self.remaining_volume = volume  # Остаток объема для доставки
        self.assigned_trips = []  # Список назначенных поездок для этого заказа
        self.failure_reasons = []  # Список причин, по которым доставка не была выполнена

# Определение класса Водитель
class Driver:
    def __init__(self, name, capacity, start_time, end_time):
        self.name = name
        self.capacity = capacity  # Вместимость в кубических метрах (8, 10 или 12)
        self.start_time = start_time  # Начало рабочего дня
        self.end_time = end_time  # Конец рабочего дня
        self.schedule = []  # Список назначенных поездок

    def is_available(self, time):
        """
        Проверка доступности водителя в заданное время.
        """
        for trip in self.schedule:
            if trip['loading_start'] <= time < trip['return_at']:
                return False
        return self.start_time <= time <= self.end_time

    def assign_trip(self, trip):
        """
        Назначение поездки водителю.
        """
        self.schedule.append(trip)

# Определение класса Завод
class Plant:
    def __init__(self, name, loading_capacity, loading_time, start_time, end_time):
        self.name = name
        self.loading_capacity = loading_capacity  # Количество машин, которые могут загружаться одновременно
        self.loading_time = loading_time  # Время загрузки одной машины
        self.start_time = start_time  # Время открытия завода
        self.end_time = end_time  # Время закрытия завода
        self.loading_schedule = defaultdict(int)  # Расписание загрузок: ключ = время, значение = количество занятых слотов

    def is_loading_slot_available(self, loading_start, loading_end):
        """
        Проверка доступности слота для загрузки в заданный период.
        """
        current_time = loading_start
        while current_time < loading_end:
            if self.loading_schedule[current_time] >= self.loading_capacity:
                return False
            current_time += timedelta(minutes=1)
        return True

    def reserve_loading_slot(self, loading_start, loading_end):
        """
        Резервирование слота для загрузки в заданный период.
        """
        current_time = loading_start
        while current_time < loading_end:
            self.loading_schedule[current_time] += 1
            current_time += timedelta(minutes=1)

# Определение класса Заказчик
class Customer:
    def __init__(self, name, orders):
        """
        orders: Список кортежей (время доставки, объем)
        delivery_time: Объект datetime, указывающий время прибытия машины к заказчику
        volume: Общий объем бетона для доставки в указанное время
        """
        self.name = name
        self.orders = [Order(self, delivery_time, volume) for delivery_time, volume in orders]

# Определение класса Поездка (для ясности)
class Trip:
    def __init__(self, loading_start, loading_end, plant_name, travel_time, arrival_time, unload_end, customer_name,
                 volume, scheduled_delivery_time, return_at):
        self.loading_start = loading_start
        self.loading_end = loading_end
        self.plant_name = plant_name
        self.travel_time = travel_time
        self.arrival_time = arrival_time
        self.unload_end = unload_end
        self.customer_name = customer_name
        self.volume = volume
        self.scheduled_delivery_time = scheduled_delivery_time
        self.return_at = return_at  # Время возвращения на завод

# Определение основного класса Планировщик
class Scheduler:
    def __init__(self, drivers, plants, customers, travel_times):
        self.drivers = copy.deepcopy(drivers)  # Список объектов Driver
        self.plants = copy.deepcopy(plants)  # Список объектов Plant
        self.customers = copy.deepcopy(customers)  # Список объектов Customer
        self.travel_times = copy.deepcopy(travel_times)  # Словарь времени пути между заводами и заказчиками

        # Предварительное вычисление вероятностей выбора завода на основе обратной зависимости от времени пути
        self.plant_selection_probs = self.compute_plant_selection_probabilities()

        # Расписание разгрузок для каждого заказчика
        self.customer_unload_schedule = {customer.name: defaultdict(int) for customer in self.customers}

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
                key = (plant.name, customer.name)
                if key in self.travel_times:
                    total_time += self.travel_times[key].total_seconds()
                    count += 1
            average_time = total_time / count if count > 0 else 1  # Избегаем деления на ноль
            plant_weights[plant.name] = 1 / (average_time + 1e-6)  # Обратная зависимость

        # Нормализация весов для получения вероятностей
        total_weight = sum(plant_weights.values())
        plant_probs = [plant_weights[plant.name] / total_weight for plant in self.plants]
        return plant_probs

    def choose_plant(self):
        """
        Выбор завода на основе предварительно вычисленных вероятностей.
        """
        plant_names = [plant.name for plant in self.plants]
        chosen_plant = random.choices(plant_names, weights=self.plant_selection_probs, k=1)[0]
        for plant in self.plants:
            if plant.name == chosen_plant:
                return plant
        return random.choice(self.plants)  # Резервный вариант

    def find_available_driver(self, loading_start, trip_duration):
        """
        Поиск доступного водителя на момент loading_start с учётом длительности поездки.
        """
        for driver in sorted(self.drivers, key=lambda d: d.capacity):
            # Проверка доступности водителя на весь период поездки
            available = True
            for trip in driver.schedule:
                trip_start = trip['loading_start']
                trip_end = trip['return_at']
                if not (loading_start + trip_duration <= trip_start or loading_start >= trip_end):
                    available = False
                    break
            if available and driver.is_available(loading_start):
                return driver
        return None

    def is_customer_available_for_unload(self, customer_name, unload_start, unload_end):
        """
        Проверка доступности заказчика для разгрузки в заданный период.
        """
        current_time = unload_start
        while current_time < unload_end:
            if self.customer_unload_schedule[customer_name][current_time] >= 1:
                return False
            current_time += timedelta(minutes=1)
        return True

    def reserve_customer_unload_slot(self, customer_name, unload_start, unload_end):
        """
        Резервирование времени разгрузки у заказчика.
        """
        current_time = unload_start
        while current_time < unload_end:
            self.customer_unload_schedule[customer_name][current_time] += 1
            current_time += timedelta(minutes=1)

    def schedule_trip(self, order, trip_volume):
        """
        Планирование одной поездки для данного заказа и объема.
        Возвращает True, если поездка успешно назначена, иначе False.
        """
        # Определение возможных вместимостей машин для данного объема
        possible_capacities = [cap for cap in [8, 10, 12] if cap >= trip_volume]
        if not possible_capacities:
            # Если нет машины с точной вместимостью, выбираем минимальную доступную вместимость
            possible_capacities = [8, 10, 12]

        # Предпочтение меньшей вместимости
        truck_capacity = min(possible_capacities)

        # Выбор завода на основе вероятностей
        plant = self.choose_plant()

        # Получение времени пути от завода до заказчика
        key = (plant.name, order.customer.name)
        travel_time_to_customer = self.travel_times.get(key, timedelta(minutes=30))  # По умолчанию 30 минут

        # Вычисление времени загрузки
        loading_end = order.delivery_time - travel_time_to_customer
        loading_start = loading_end - plant.loading_time

        # Проверка операционных часов завода
        if not (plant.start_time <= loading_start and loading_end <= plant.end_time):
            # Невозможно загрузить машину вне операционных часов завода
            order.failure_reasons.append("Ограничение операционных часов завода")
            return False

        # Проверка доступности слотов для загрузки
        if not plant.is_loading_slot_available(loading_start, loading_end):
            # Слот для загрузки занят, ищем ближайшее предыдущее доступное время
            earliest_loading_start = self.find_earliest_loading_time(plant, loading_start, order.delivery_time, travel_time_to_customer)
            if earliest_loading_start:
                # Обновляем времена загрузки с учетом ожидания
                loading_start = earliest_loading_start
                loading_end = loading_start + plant.loading_time
                print(f"[DEBUG] Adjusted loading time for order to {order.customer.name} at {order.delivery_time.strftime('%H:%M')} from {loading_start.strftime('%H:%M')} to {loading_end.strftime('%H:%M')}")
            else:
                # Невозможно найти доступное время загрузки
                order.failure_reasons.append("Нет доступных слотов для загрузки на заводе")
                return False

        # Вычисление предполагаемого времени прибытия и разгрузки
        arrival_time = loading_end + travel_time_to_customer
        unload_end = arrival_time + timedelta(minutes=30)  # Фиксированное время разгрузки

        # Проверка доступности заказчика для разгрузки
        if not self.is_customer_available_for_unload(order.customer.name, arrival_time, unload_end):
            # Заказчик занят разгрузкой, ищем ближайшее доступное время разгрузки
            adjusted_arrival_time = self.find_earliest_unload_time(order.customer.name, arrival_time, unload_end)
            if adjusted_arrival_time:
                # Пересчитываем время загрузки на заводе
                new_arrival_time = adjusted_arrival_time
                new_unload_end = new_arrival_time + timedelta(minutes=30)
                new_loading_end = new_arrival_time - travel_time_to_customer
                new_loading_start = new_loading_end - plant.loading_time

                # Проверка операционных часов завода после изменения
                if not (plant.start_time <= new_loading_start and new_loading_end <= plant.end_time):
                    order.failure_reasons.append("Ограничение операционных часов завода после корректировки разгрузки")
                    return False

                # Проверка доступности слотов для загрузки в новом времени
                if not plant.is_loading_slot_available(new_loading_start, new_loading_end):
                    order.failure_reasons.append("Нет доступных слотов для загрузки на заводе после корректировки разгрузки")
                    return False

                # Обновляем времена загрузки и разгрузки
                loading_start = new_loading_start
                loading_end = new_loading_end
                arrival_time = new_arrival_time
                unload_end = new_unload_end
                print(f"[DEBUG] Adjusted arrival time for order to {order.customer.name} at {order.delivery_time.strftime('%H:%M')} to {arrival_time.strftime('%H:%M')}")
            else:
                # Невозможно найти доступное время разгрузки
                order.failure_reasons.append("Заказчик занят разгрузкой и невозможно перенести время разгрузки")
                return False

        # Поиск доступного водителя на момент загрузки с учётом длительности поездки
        trip_duration = (unload_end - loading_start) + travel_time_to_customer  # Время от начала загрузки до возвращения на завод
        driver = self.find_available_driver(loading_start, trip_duration)
        if not driver:
            # Нет доступного водителя с необходимой вместимостью
            order.failure_reasons.append("Нет доступных водителей с необходимой вместимостью")
            return False

        # Резервирование слота для загрузки и разгрузки
        plant.reserve_loading_slot(loading_start, loading_end)
        self.reserve_customer_unload_slot(order.customer.name, arrival_time, unload_end)

        # Вычисление времени возвращения на завод
        travel_time_back = travel_time_to_customer  # Предполагаем, что время пути обратно такое же
        return_at = unload_end + travel_time_back

        # Создание объекта поездки
        trip = Trip(
            loading_start=loading_start,
            loading_end=loading_end,
            plant_name=plant.name,
            travel_time=travel_time_to_customer,
            arrival_time=arrival_time,
            unload_end=unload_end,
            customer_name=order.customer.name,
            volume=trip_volume,
            scheduled_delivery_time=order.delivery_time,
            return_at=return_at
        )

        # Назначение поездки водителю
        driver.assign_trip({
            'loading_start': trip.loading_start,
            'loading_end': trip.loading_end,
            'plant': trip.plant_name,
            'travel_time': trip.travel_time,
            'arrival_time': trip.arrival_time,
            'unload_end': trip.unload_end,
            'customer': trip.customer_name,
            'volume': trip.volume,
            'scheduled_delivery_time': trip.scheduled_delivery_time,
            'return_at': trip.return_at
        })

        # Назначение поездки заказу
        order.assigned_trips.append(trip)
        order.remaining_volume -= trip_volume

        print(f"[DEBUG] Assigned trip: Driver {driver.name} loaded {trip.volume} m³ at {plant.name} from {loading_start.strftime('%H:%M')} to {loading_end.strftime('%H:%M')}, "
              f"delivering to {order.customer.name} at {arrival_time.strftime('%H:%M')}, unload until {unload_end.strftime('%H:%M')}, "
              f"returning at {return_at.strftime('%H:%M')}.")

        return True

    def find_earliest_loading_time(self, plant, desired_loading_start, delivery_time, travel_time):
        """
        Поиск ближайшего предыдущего времени загрузки, которое возможно и не нарушает время доставки.
        """
        # Максимально возможное время загрузки
        latest_loading_start = desired_loading_start
        # Минимально возможное время загрузки
        earliest_loading_start = plant.start_time

        # Ищем время загрузки, начиная с желаемого и двигаясь назад
        current_time = latest_loading_start
        while current_time >= earliest_loading_start:
            loading_start = current_time
            loading_end = loading_start + plant.loading_time
            if loading_end > desired_loading_start:
                # Пропускаем, если загрузка завершится позже желаемого времени начала загрузки
                current_time -= timedelta(minutes=1)
                continue
            if plant.is_loading_slot_available(loading_start, loading_end):
                # Проверяем, что время прибытия не превышает желаемое
                arrival_time = loading_end + travel_time
                if arrival_time <= delivery_time:
                    return loading_start
            current_time -= timedelta(minutes=1)
        return None

    def find_earliest_unload_time(self, customer_name, desired_arrival_time, unload_end):
        """
        Поиск ближайшего доступного времени разгрузки для заказчика.
        """
        # Начинаем с желаемого времени разгрузки
        current_time = unload_end
        # Определяем максимально возможное время разгрузки (конец рабочего дня)
        plant_end_time = max(plant.end_time for plant in self.plants)

        while current_time <= plant_end_time:
            new_arrival_time = current_time
            new_unload_end = new_arrival_time + timedelta(minutes=30)
            if self.is_customer_available_for_unload(customer_name, new_arrival_time, new_unload_end):
                return new_arrival_time
            current_time += timedelta(minutes=1)
        return None

    def simulate(self):
        """
        Запуск одной симуляции.
        Возвращает метрики и текущее состояние водителей и заказов.
        """

        # Сортировка заказов по времени доставки
        all_orders = []
        for customer in self.customers:
            for order in customer.orders:
                all_orders.append(order)
        all_orders.sort(key=lambda x: x.delivery_time)

        # Планирование поездок для каждого заказа
        for order in all_orders:
            while order.remaining_volume > 0:
                # Планируем поездку с объемом, равным минимуму из оставшегося объема и максимальной вместимости машины
                trip_volume = min(order.remaining_volume, 12)  # Максимальная вместимость машины
                success = self.schedule_trip(order, trip_volume)
                if not success:
                    # Не удалось назначить поездку, прекращаем попытки
                    break

        # Вычисление метрик
        metrics = self.calculate_metrics(self.drivers, self.customers)

        return {
            'metrics': metrics,
            'drivers': self.drivers,
            'customers': self.customers
        }

    def calculate_metrics(self, drivers, customers):
        """
        Вычисление метрик симуляции:
        - Среднее отклонение времени доставки
        - Утилизация водителей
        - Не доставленный объем
        """
        # Среднее отклонение времени доставки
        total_time_deviation = timedelta()
        total_deliveries = 0
        undelivered_volume = 0

        for customer in customers:
            for order in customer.orders:
                if order.assigned_trips:
                    for trip in order.assigned_trips:
                        deviation = abs(trip.arrival_time - trip.scheduled_delivery_time)
                        total_time_deviation += deviation
                        total_deliveries += 1
                if order.remaining_volume > 0:
                    # Наложение штрафа за не доставленный объем
                    undelivered_volume += order.remaining_volume
                    total_deliveries += 1
                    total_time_deviation += timedelta(hours=10)  # Штрафное время

        average_time_deviation = total_time_deviation / total_deliveries if total_deliveries > 0 else timedelta()

        # Утилизация водителей
        total_driver_work_time = timedelta()
        total_driver_available_time = timedelta()

        for driver in drivers:
            work_time = timedelta()
            for trip in driver.schedule:
                trip_start = trip['loading_start']
                trip_end = trip['return_at']
                work_time += (trip_end - trip_start)
            driver_total_time = driver.end_time - driver.start_time
            total_driver_work_time += work_time
            total_driver_available_time += driver_total_time

        driver_utilization = (
            (total_driver_work_time / total_driver_available_time) * 100
            if total_driver_available_time > timedelta() else 0
        )

        # Компиляция метрик
        metrics = {
            'average_time_deviation': average_time_deviation,
            'driver_utilization': driver_utilization,
            'undelivered_volume': undelivered_volume
        }

        return metrics