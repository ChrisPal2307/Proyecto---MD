import pygame
import math
import sys
import random


# --- Configuración ---
WIDTH, HEIGHT = 900, 700
FPS = 60
NODE_RADIUS = 10  # Radio de los nodos para dibujar
PLAYER_SPEED = 2
ENEMY_SPEED = 1.5
pygame.init()


screen = pygame.display.set_mode((WIDTH, HEIGHT))  # <-- Aquí se crea 'screen'
background_img = pygame.image.load("mapita.png").convert()  # convert() para optimizar
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))  # escalar al tamaño de la pantalla

player_image = pygame.image.load("carrito.png").convert_alpha()
# Ajustar tamaño al radio del nodo
player_image = pygame.transform.scale(player_image, (NODE_RADIUS*4, NODE_RADIUS*3))

bot = pygame.image.load("paco.png").convert_alpha()
# Ajustar tamaño al radio del nodo
bot = pygame.transform.scale(bot, (NODE_RADIUS*7, NODE_RADIUS*6))

# --- Colores ---
BG_COLOR = (245, 245, 245)
NODE_COLOR = (30, 144, 255)
EDGE_COLOR = (70, 70, 70)
PLAYER_COLOR = (0, 180, 0)
ENEMY_COLOR = (255, 69, 0)

# --- Grafo ---
nodes = {
    0: (154, 8),
    1: (205, 82),
    2: (308, 209),
    3: (324, 144),
    4: (262, 365),
    5: (339, 403),
    6: (236, 461),
    7: (316, 510),
    8: (343, 9),
    9: (391, 167),
    10: (126, 144),
    11: (14, 11),
    12: (65, 325),
    13: (6, 283),
    14: (148, 390),
    15: (203, 245),
    16: (372, 268),
    17: (526, 80),
    18: (616, 180),
    19: (542, 278),
    20: (714, 53),
    21: (493, 343),
    22: (397, 480),
    23: (458, 567),
    24: (292, 649),
    25: (216, 555),
    26: (580, 451),
    27: (661, 369),
    28: (708, 299),
    29: (739, 183),
    30: (847, 278),
    31: (837, 419),
    32: (727, 460),
    33: (748, 573),
    34: (649, 545),
    35: (517, 654)
}


edges = {
    0: [1],
    1: [0, 2,10],
    2: [1, 3, 4, 16],
    3: [2,8,9],
    4: [5, 6, 2],
    5: [4, 7, 22, 16],
    6: [4, 7, 14, 25],
    7: [5, 6, 24],
    8: [3],
    9: [3, 16,17, 19],
    10: [1,11,12, 15],
    11: [10],
    12: [10,13,14],
    13: [12],
    14: [12,6,10, 15],
    15: [10,14],
    16: [9,2,21, 5],
    17: [9,18],
    18: [17,20, 19],
    19: [18,21, 9, 27],
    20: [18, 29],
    21: [16,19,22, 26],
    22: [5, 21, 23],
    23: [22,24,26,35],
    24: [25,23, 7],
    25: [6,24],
    26: [21,23,34,27],
    27: [26, 19, 32, 28],
    28: [27, 30,29],
    29: [28, 20],
    30: [28, 31],
    31: [30, 32],
    32: [31, 27,33],
    33: [32,34],
    34: [26, 35, 33],
    35: [23, 34]
}

# --- Floyd-Warshall ---
def floyd_warshall(nodes, edges):
    n = len(nodes)
    dist = [[math.inf]*n for _ in range(n)]
    next_hop = [[-1]*n for _ in range(n)]
    for u in nodes:
        dist[u][u] = 0
        next_hop[u][u] = u
        for v in edges.get(u, []):
            dist[u][v] = math.dist(nodes[u], nodes[v])
            next_hop[u][v] = v
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k]+dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k]+dist[k][j]
                    next_hop[i][j] = next_hop[i][k]
    return dist, next_hop

dist_matrix, next_hop = floyd_warshall(nodes, edges)

def shortest_path(u, v):
    if next_hop[u][v] == -1:
        return []
    path = [u]
    while u != v:
        u = next_hop[u][v]
        path.append(u)
    return path

# --- Función para verificar clic sobre arista ---
def point_line_distance(px, py, x1, y1, x2, y2):
    A = px - x1
    B = py - y1
    C = x2 - x1
    D = y2 - y1
    dot = A*C + B*D
    len_sq = C*C + D*D
    param = dot / len_sq if len_sq != 0 else -1
    if param < 0:
        xx, yy = x1, y1
    elif param > 1:
        xx, yy = x2, y2
    else:
        xx, yy = x1 + param*C, y1 + param*D
    dx, dy = px - xx, py - yy
    return math.hypot(dx, dy)

def get_edge_clicked(mx, my, current_node):
    for neighbor in edges[current_node]:
        x1, y1 = nodes[current_node]
        x2, y2 = nodes[neighbor]
        if point_line_distance(mx, my, x1, y1, x2, y2) < 10:
            return neighbor
    return None

# --- Clases ---
class Player:
    def __init__(self, start_node):
        self.current_node = start_node
        self.pos = list(nodes[start_node])
        self.target_node = None
        self.t = 0
        self.start_pos = list(self.pos)
        self.end_pos = list(self.pos)
        self.last_angle = 0  # Ángulo de orientación

    def move_to(self, node):
        self.target_node = node
        self.t = 0
        self.start_pos = list(self.pos)
        self.end_pos = list(nodes[node])
        dx, dy = self.end_pos[0] - self.start_pos[0], self.end_pos[1] - self.start_pos[1]
        self.last_angle = math.degrees(math.atan2(dy, dx))  # Guardar ángulo al iniciar movimiento

    def update(self):
        if self.target_node is not None:
            dx, dy = self.end_pos[0]-self.start_pos[0], self.end_pos[1]-self.start_pos[1]
            distance = math.hypot(dx, dy)
            self.t += PLAYER_SPEED/distance if distance!=0 else 1
            if self.t >=1:
                self.pos = self.end_pos
                self.current_node = self.target_node
                self.target_node = None
                # El ángulo se mantiene en self.last_angle
            else:
                self.pos[0] = self.start_pos[0]+dx*self.t
                self.pos[1] = self.start_pos[1]+dy*self.t

    def draw(self):
        rotated_image = pygame.transform.rotate(player_image, -self.last_angle)
        rect = rotated_image.get_rect(center=(int(self.pos[0]), int(self.pos[1])))
        screen.blit(rotated_image, rect)


class Enemy:
    def __init__(self, start_node):
        self.start_node = start_node
        self.current_node = start_node
        self.pos = list(nodes[start_node])
        self.path = []
        self.target_node = None
        self.t = 0
        self.start_pos = list(self.pos)
        self.end_pos = list(self.pos)
        self.last_angle = 0  # Ángulo de orientación

    def chase(self, player):
        # Ver si el jugador está en movimiento
        if player.target_node is not None:
            # Jugador se mueve: perseguir el nodo hacia el que va
            target = player.target_node
        else:
            # Jugador está quieto: perseguir el nodo actual
            target = player.current_node

        # Solo recalcular si estamos en un nodo
        if self.target_node is None:
            self.path = shortest_path(self.current_node, target)
            if len(self.path) > 1:
                self.target_node = self.path[1]
                self.t = 0
                self.start_pos = list(self.pos)
                self.end_pos = list(nodes[self.target_node])
                dx, dy = self.end_pos[0] - self.start_pos[0], self.end_pos[1] - self.start_pos[1]
                self.last_angle = math.degrees(math.atan2(dy, dx))

    def update(self):
        if self.target_node is not None:
            dx, dy = self.end_pos[0] - self.start_pos[0], self.end_pos[1] - self.start_pos[1]
            distance = math.hypot(dx, dy)
            move_ratio = ENEMY_SPEED / distance if distance != 0 else 1
            self.t += move_ratio
            if self.t >= 1:
                self.pos = self.end_pos
                self.current_node = self.target_node
                self.target_node = None
                # Mantener el último ángulo
            else:
                # Actualizar posición
                self.pos[0] = self.start_pos[0] + dx * self.t
                self.pos[1] = self.start_pos[1] + dy * self.t
                # Ángulo durante el movimiento
                self.last_angle = math.degrees(math.atan2(dy, dx))

    def draw(self):
        # Rotar la imagen y centrar correctamente
        rotated_image = pygame.transform.rotate(bot, -self.last_angle)
        rect = rotated_image.get_rect(center=(int(self.pos[0]), int(self.pos[1])))
        screen.blit(rotated_image, rect)


# --- Crear jugador y enemigos ---
player = Player(0)
initial_enemies_nodes = [35]
enemies = [Enemy(n) for n in initial_enemies_nodes]
initial_enemies = [Enemy(n) for n in initial_enemies_nodes]

# --- Loop principal ---
clock = pygame.time.Clock()
running = True
font = pygame.font.SysFont(None, 24)

last_spawn_time = pygame.time.get_ticks()  # último spawn en ms
spawn_interval = 5000  # cada 10 segundos (10000 ms)
spawn_nodes = [24, 13, 11, 35, 24, 30, 33, 0, 17]

while running:
    screen.blit(background_img, (0, 0))

    # Eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if player.target_node is None:
                mx, my = pygame.mouse.get_pos()
                dest = get_edge_clicked(mx, my, player.current_node)
                if dest is not None:
                    player.move_to(dest)

    # Actualizar jugador
    player.update()
    player.draw()

    now = pygame.time.get_ticks()
    if now - last_spawn_time > spawn_interval:
        random_node = random.choice(spawn_nodes)  # elegir nodo aleatorio permitido
        enemies.append(Enemy(random_node))  # añadir nuevo enemigo
        last_spawn_time = now  # reiniciar temporizador

    # Actualizar enemigos
    for enemy in enemies:
        enemy.chase(player)
        enemy.update()
        enemy.draw()

        # Colisión
        if math.hypot(player.pos[0] - enemy.pos[0], player.pos[1] - enemy.pos[1]) < NODE_RADIUS:
            game_over = True
            while game_over:
                screen.fill((0, 0, 0))
                text = font.render("¡Te atraparon! Presiona R para reiniciar o Q para salir", True, (255, 0, 0))
                text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                screen.blit(text, text_rect)
                pygame.display.flip()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        game_over = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            # Reiniciar jugador
                            player.current_node = 0
                            player.pos = list(nodes[player.current_node])
                            player.target_node = None
                            player.path = []

                            enemies = [Enemy(n) for n in initial_enemies_nodes]

                            game_over = False
                        elif event.key == pygame.K_q:
                            running = False
                            game_over = False


    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
