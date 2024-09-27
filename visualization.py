import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import dates as mdates
from datetime import datetime, timedelta
from collections import defaultdict


def visualize_assigned_trips(assigned_trips):
    """
    Визуализирует данные о назначенных поездках в виде диаграммы Ганта.

    Параметры:
    - assigned_trips: список словарей с информацией о поездках.
    """
    # Организуем поездки по транспортным средствам
    vehicles_schedule = defaultdict(list)
    for trip in assigned_trips:
        vehicle_id = trip['vehicle']
        vehicles_schedule[vehicle_id].append(trip)

    # Получаем отсортированный список идентификаторов транспортных средств
    vehicle_ids = sorted(vehicles_schedule.keys())

    # Настройка графика
    fig, ax = plt.subplots(figsize=(15, 8))

    # Настройка оси Y
    y_ticks = range(len(vehicle_ids))
    y_labels = [f"Vehicle {vehicle_id}" for vehicle_id in vehicle_ids]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.invert_yaxis()  # Инвертируем ось Y, чтобы первый водитель был сверху

    # Настройка оси X
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    # Определяем базовую дату для построения
    if assigned_trips:
        base_date = datetime.strptime(assigned_trips[0]['load_at'], '%Y-%m-%d %H:%M:%S').date()
    else:
        base_date = datetime.today().date()

    # Определяем цвета для разных фаз
    phase_colors = {
        'Travel to Plant': 'lightblue',
        'Loading': 'skyblue',
        'Travel to Customer': 'lightgreen',
        'Unloading': 'salmon',
        'Idle': 'grey'  # Фаза ожидания или простоя
    }

    # Построение поездок
    for i, vehicle_id in enumerate(vehicle_ids):
        trips = vehicles_schedule[vehicle_id]
        for trip in trips:
            # Разбор временных меток
            # Обработка возможных отсутствующих значений
            try:
                customer_start_at = datetime.strptime(trip['customer_start_at'], '%Y-%m-%d %H:%M:%S') if trip[
                    'customer_start_at'] else None
                plant_arrive_at = datetime.strptime(trip['plant_arrive_at'], '%Y-%m-%d %H:%M:%S') if trip[
                    'plant_arrive_at'] else None
                load_at = datetime.strptime(trip['load_at'], '%Y-%m-%d %H:%M:%S')
                arrive_at = datetime.strptime(trip['arrive_at'], '%Y-%m-%d %H:%M:%S')
                unload_at = datetime.strptime(trip['unload_at'], '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                print(f"Error parsing dates for trip {trip['id']}: {e}")
                continue  # Пропускаем эту поездку в случае ошибки

            # Определение фаз
            phases = []
            if customer_start_at and plant_arrive_at:
                phases.append(('Travel to Plant', customer_start_at, plant_arrive_at))
            elif plant_arrive_at:
                # Если нет customer_start_at, но есть plant_arrive_at
                phases.append(('Travel to Plant', plant_arrive_at - timedelta(minutes=15), plant_arrive_at))
            else:
                # Если нет plant_arrive_at, используем load_at
                phases.append(('Travel to Plant', load_at - timedelta(minutes=15), load_at))

            if plant_arrive_at and load_at:
                phases.append(('Loading', plant_arrive_at, load_at))
            elif load_at:
                phases.append(('Loading', load_at - timedelta(minutes=15), load_at))

            if load_at and arrive_at:
                phases.append(('Travel to Customer', load_at, arrive_at))

            if arrive_at and unload_at:
                phases.append(('Unloading', arrive_at, unload_at))

            # Построение каждой фазы
            for phase, start_time, end_time in phases:
                start_num = mdates.date2num(start_time)
                end_num = mdates.date2num(end_time)
                duration = end_num - start_num

                ax.barh(
                    i,
                    duration,
                    left=start_num,
                    height=0.4,
                    color=phase_colors.get(phase, 'grey'),
                    edgecolor='black'
                )

                # Добавление аннотаций для фаз Loading и Unloading
                if phase in ['Loading', 'Unloading']:
                    mid_time = start_time + (end_time - start_time) / 2
                    annotation = f"{phase}\n"
                    if phase == 'Loading':
                        annotation += f"Plant {trip['plant']}"
                    else:
                        annotation += f"Order {trip['order']}"
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

    # Установка подписей и заголовка
    ax.set_xlabel('Time')
    ax.set_title('Assigned Trips Gantt Chart')
    ax.grid(True, which='both', axis='x', linestyle='--', alpha=0.5)

    # Настройка границ оси X
    if assigned_trips:
        earliest_start = min(
            datetime.strptime(trip['customer_start_at'], '%Y-%m-%d %H:%M:%S') if trip[
                'customer_start_at'] else datetime.strptime(trip['plant_arrive_at'], '%Y-%m-%d %H:%M:%S') - timedelta(
                minutes=15)
            for trip in assigned_trips
        )
        latest_end = max(datetime.strptime(trip['unload_at'], '%Y-%m-%d %H:%M:%S') for trip in assigned_trips)
        ax.set_xlim(
            mdates.date2num(earliest_start) - 0.01,
            mdates.date2num(latest_end) + 0.01
        )

    plt.tight_layout()
    plt.show()


# Example usage
if __name__ == "__main__":
    case_name = input("Введите название кейса: ")
    with open(f'data/{case_name}/results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)

    visualize_assigned_trips(results['assigned_trips'])
