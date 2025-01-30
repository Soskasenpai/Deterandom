import random
import uuid
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from mpl_toolkits.mplot3d import Axes3D
from collections import defaultdict
from matplotlib.widgets import Button


class Track:
    def __init__(self, name, weight=1):
        self.id = uuid.uuid4()  # Уникальный идентификатор трека
        self.name = name
        self.weight = weight

    def __repr__(self):
        return f"Track(id={self.id}, name={self.name}, weight={self.weight})"


class Playlist:
    def __init__(self, tracks):
        self.tracks = tracks

    def choose_track(self):
        total_weight = sum(track.weight for track in self.tracks)
        rand = random.uniform(0, total_weight)
        cumulative_weight = 0
        for track in self.tracks:
            cumulative_weight += track.weight
            if rand < cumulative_weight:
                track.weight += 2
                return track

    def choose_multiple_tracks(self, num_tracks):
        return [self.choose_track() for _ in range(num_tracks)]

    def __repr__(self):
        return "\n".join(str(track) for track in self.tracks)


def export_graph_to_obj(G, pos, file_name="graph_3d.obj"):
    """
    Экспортирует граф с 3D-позициями узлов в формат .obj.
    """
    with open(file_name, "w") as obj_file:
        obj_file.write("# 3D Граф узлов и рёбер\n")
        node_indices = {}

        # Экспорт узлов (vertex)
        for i, (node, coords) in enumerate(pos.items(), 1):
            node_indices[node] = i
            x, y, z = coords
            obj_file.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")  # Запись вершины

        # Экспорт рёбер (lines)
        obj_file.write("\n# Рёбра\n")
        for edge in G.edges:
            node1, node2 = edge
            obj_file.write(f"l {node_indices[node1]} {node_indices[node2]}\n")  # Запись линии


def plot_combined_graphs(tracks, track_selection_history, connections, num_cycles):
    fig = plt.figure(figsize=(24, 18))  # Увеличенное окно
    plt.subplots_adjust(bottom=0.25, wspace=0.4)  # Пространство снизу для кнопок

    # График 1: Тепловая карта выбора треков
    ax1 = fig.add_subplot(131)
    track_names = list(track_selection_history.keys())
    heatmap_data = [history for history in track_selection_history.values()]
    sns.heatmap(heatmap_data, ax=ax1, cmap="YlGnBu", cbar=True)
    ax1.set_title("Тепловая карта выбора треков", fontsize=16)
    ax1.set_xlabel("Циклы", fontsize=14)
    ax1.set_ylabel("Треки", fontsize=14)
    ax1.set_yticks(range(len(track_names)))
    ax1.set_yticklabels(track_names, fontsize=12)
    ax1.tick_params(axis="x", labelsize=12)

    # График 2: 3D-гистограмма распределения весов треков
    ax2 = fig.add_subplot(132, projection='3d')
    x = [track.name for track in tracks]
    y = list(range(1, len(tracks) + 1))
    z = [0] * len(tracks)
    dx = [0.8] * len(tracks)
    dy = [0.8] * len(tracks)
    dz = [track.weight for track in tracks]
    ax2.bar3d(y, z, z, dx, dy, dz, shade=True, color='red')
    ax2.set_xlabel("Трек ID", fontsize=14)
    ax2.set_ylabel("Z", fontsize=14)
    ax2.set_zlabel("Вес", fontsize=14)
    ax2.set_title(f"Распределение весов треков\n(после {num_cycles} циклов)", fontsize=16)

    # График 3: 3D граф связей
    ax3 = fig.add_subplot(133, projection="3d")
    G = nx.Graph()
    for track in tracks:
        G.add_node(track.name, weight=track.weight)
    threshold = 1
    for (track1, track2), weight in connections.items():
        if weight >= threshold:
            G.add_edge(track1, track2, weight=weight)

    pos = nx.spring_layout(G, seed=42, dim=3)  # Используем 3D раскладку

    # Переменные для скрытия/показа узлов и рёбер
    show_nodes = True
    show_edge_labels = True

    # Функция для отрисовки графика
    def draw_graph():
        ax3.clear()
        ax3.set_title("3D Граф связей треков", fontsize=16)
        if show_nodes:
            for node, (x, y, z) in pos.items():
                ax3.scatter(x, y, z, s=G.nodes[node]["weight"] * 50, color="lightblue", alpha=0.8)
                if show_edge_labels:
                    ax3.text(x, y, z, node, fontsize=10, ha='center', va='center')
        for edge in G.edges:
            x1, y1, z1 = pos[edge[0]]
            x2, y2, z2 = pos[edge[1]]
            ax3.plot([x1, x2], [y1, y2], [z1, z2], color="gray", alpha=0.5)

        ax3.figure.canvas.draw_idle()

    draw_graph()

    # Функция для скрытия/показа узлов
    def toggle_nodes(event):
        nonlocal show_nodes
        show_nodes = not show_nodes
        draw_graph()

    # Функция для скрытия/показа имён треков
    def toggle_edge_labels(event):
        nonlocal show_edge_labels
        show_edge_labels = not show_edge_labels
        draw_graph()

    # Функция для экспорта графа
    def export_graph(event):
        export_graph_to_obj(G, pos, file_name="graph_3d.obj")
        print("Граф экспортирован в 'graph_3d.obj'.")

    # Добавление кнопок
    button_ax1 = plt.axes([0.1, 0.01, 0.25, 0.06])
    button_nodes = Button(button_ax1, "Показать/Скрыть Узлы")
    button_nodes.on_clicked(toggle_nodes)

    button_ax2 = plt.axes([0.4, 0.01, 0.25, 0.06])
    button_edge_labels = Button(button_ax2, "Показать/Скрыть Имена")
    button_edge_labels.on_clicked(toggle_edge_labels)

    button_ax3 = plt.axes([0.7, 0.01, 0.25, 0.06])
    export_button = Button(button_ax3, "Экспортировать в .obj")
    export_button.on_clicked(export_graph)

    plt.show()


def run_simulation(num_tracks, num_cycles, tracks_per_cycle):
    tracks = [Track(f"Track {i + 1}") for i in range(num_tracks)]
    playlist = Playlist(tracks)
    track_selection_history = defaultdict(list)
    connections = defaultdict(int)
    previous_track = None

    for _ in range(num_cycles):
        chosen_tracks = playlist.choose_multiple_tracks(tracks_per_cycle)
        for i in range(len(chosen_tracks)):
            for j in range(i + 1, len(chosen_tracks)):
                connections[(chosen_tracks[i].name, chosen_tracks[j].name)] += 1
        if tracks_per_cycle == 1 and previous_track:
            connections[(previous_track.name, chosen_tracks[0].name)] += 1
        previous_track = chosen_tracks[0] if tracks_per_cycle == 1 else None
        for track in tracks:
            track_selection_history[track.name].append(1 if track in chosen_tracks else 0)

    plot_combined_graphs(tracks, track_selection_history, connections, num_cycles)


# Основные параметры симуляции
num_tracks = 100  # Количество треков
num_cycles = 1000  # Количество циклов
tracks_per_cycle = 1  # Количество треков, выбираемых за цикл

run_simulation(num_tracks, num_cycles, tracks_per_cycle)
