# visualization.py

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import dates as mdates
from datetime import datetime
from collections import defaultdict

def load_json_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_id_name_mapping(data, id_key, name_key):
    """
    Создаёт словарь для сопоставления ID с именами или адресами.
    """
    mapping = {}
    for item in data:
        mapping[item[id_key]] = item.get(name_key, f"ID {item[id_key]}")
    return mapping

def visualize_schedule(deliveries_file, plants_file, customer_orders_file):
    """
    Визуализация расписания отгрузок на основе файла deliveries.json.
    Отображается диаграмма Ганта с фазами каждой поездки, а также
    информация о заводе и заказчике.
    """
    # Загрузка данных
    deliveries = load_json_data(deliveries_file)
    plants = load_json_data(plants_file)
    customer_orders = load_json_data(customer_orders_file)

    # Создание сопоставлений ID с именами/адресами
    plant_id_to_name = create_id_name_mapping(plants, 'id', 'factory_id')
    customer_id_to_name = create_id_name_mapping(customer_orders, 'delivery_address_id', 'delivery_address_id')

    # Организация данных по транспортным средствам
    vehicles_schedule = defaultdict(list)
    for delivery in deliveries:
        vehicle_id = delivery['vehicle_id']
        vehicles_schedule[vehicle_id].append(delivery)

    # Получение списка всех транспортных средств
    vehicle_ids = sorted(vehicles_schedule.keys())

    # Настройка фигуры и осей
    fig, ax = plt.subplots(figsize=(20, 10))

    # Настройка оси Y
    y_ticks = range(len(vehicle_ids))
    y_labels = [f"Vehicle {vehicle_id}" for vehicle_id in vehicle_ids]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.invert_yaxis()  # Водители сверху

    # Настройка оси X
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    # Определение начальной даты для корректного отображения времени
    if deliveries:
        base_date = datetime.strptime(deliveries[0]['start_at'], '%Y-%m-%d %H:%M:%S').date()
    else:
        base_date = datetime.today().date()

    # Определение цветовой схемы для фаз поездки
    phase_colors = {
        'Loading': 'skyblue',
        'Travel to Customer': 'lightgreen',
        'Unloading': 'salmon',
        'Return to Plant': 'lightsalmon'
    }

    # Добавление задач на график
    for i, vehicle_id in enumerate(vehicle_ids):
        for trip in vehicles_schedule[vehicle_id]:
            # Извлечение фаз поездки
            loading_start = datetime.strptime(trip['start_at'], '%Y-%m-%d %H:%M:%S')
            loading_end = datetime.strptime(trip['load_at'], '%Y-%m-%d %H:%M:%S')
            arrive_at = datetime.strptime(trip['arrive_at'], '%Y-%m-%d %H:%M:%S')
            unload_at = datetime.strptime(trip['unload_at'], '%Y-%m-%d %H:%M:%S')
            return_at = datetime.strptime(trip['return_at'], '%Y-%m-%d %H:%M:%S')

            # Фазы поездки
            phases = [
                ('Loading', loading_start, loading_end),
                ('Travel to Customer', loading_end, arrive_at),
                ('Unloading', arrive_at, unload_at),
                ('Return to Plant', unload_at, return_at)
            ]

            # Информация о заводе и заказчике
            plant_id = trip['plant_id']
            plant_name = f"Plant {plant_id_to_name.get(plant_id, plant_id)}"
            mix_order_group_id = trip['mix_order_group_id']

            for phase, start, end in phases:
                duration = (end - start).total_seconds() / 3600  # Часы
                ax.barh(
                    i,
                    duration,
                    left=mdates.date2num(start),
                    height=0.4,
                    color=phase_colors.get(phase, 'grey'),
                    edgecolor='black'
                )

                # Добавление аннотаций
                mid_time = start + (end - start) / 2
                annotation = f"{phase}\n{plant_name}" if phase == 'Loading' else (
                    f"{phase}\n{mix_order_group_id}" if phase == 'Unloading' else ""
                )
                if annotation:
                    ax.text(
                        mdates.date2num(mid_time),
                        i,
                        annotation,
                        va='center',
                        ha='center',
                        fontsize=8,
                        color='black'
                    )

    # Создание легенды
    patches = [mpatches.Patch(color=color, label=phase) for phase, color in phase_colors.items()]
    ax.legend(handles=patches, loc='upper right')

    # Настройка границ и сетки
    ax.set_xlabel('Time of Day')
    ax.set_title('Driver Schedules Gantt Chart')
    ax.grid(True, which='both', axis='x', linestyle='--', alpha=0.5)

    # Ограничение оси X по времени симуляции
    if deliveries:
        earliest_start = min(datetime.strptime(d['start_at'], '%Y-%m-%d %H:%M:%S') for d in deliveries)
        latest_end = max(datetime.strptime(d['return_at'], '%Y-%m-%d %H:%M:%S') for d in deliveries)
        start_datetime = datetime.combine(base_date, earliest_start.time())
        end_datetime = datetime.combine(base_date, latest_end.time())
        ax.set_xlim(mdates.date2num(start_datetime) - 0.01, mdates.date2num(end_datetime) + 0.01)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Пути к JSON-файлам
    deliveries_file = 'data/deliveries.json'
    plants_file = 'data/plants.json'
    customer_orders_file = 'data/customer_orders.json'

    visualize_schedule(deliveries_file, plants_file, customer_orders_file)
