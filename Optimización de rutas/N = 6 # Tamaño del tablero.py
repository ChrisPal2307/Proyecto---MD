import pygame
import math
import sys

# --- Configuración ---
WIDTH, HEIGHT = 700, 500
FPS = 60
NODE_RADIUS = 2  # Radio lógico, se escala con el zoom
CAR_SPEED = 0.2  # Velocidad en unidades lógicas por frame

# --- Plano lógico ---
MAP_WIDTH_LOGICAL = 100
MAP_HEIGHT_LOGICAL = 100

# --- Estado de vista ---
zoom = 5.0  # Cuántos píxeles por unidad lógica (ajustable)
offset_x, offset_y = 0, 0
dragging = False
last_mouse_pos = (0, 0)
ZOOM_STEP = 0.1

# --- Colores ---
BG_COLOR = (245, 245, 245)
GRID_COLOR = (220, 220, 220)
NODE_COLOR = (30, 144, 255)
EDGE_COLOR = (70, 70, 70)
ROUTE_COLOR = (255, 69, 0)
CAR_COLOR = (0, 180, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Floyd-Warshall con zoom, arrastre y plano cartesiano")
clock = pygame.time.Clock()

# --- Funciones de transformación ---
def logical_to_screen(x, y):
    return int(x * zoom + offset_x), int(y * zoom + offset_y)

def screen_to_logical(sx, sy):
    return (sx - offset_x) / zoom, (sy - offset_y) / zoom

# --- Nodos (coordenadas lógicas de 0 a 100) ---
nodos = {
    1: (10.85, 5.8),
    2: (26.7, 7.4),
    3: (36.57, 5.0),
    4: (46.28, 5.2),
    5: (11.42, 23.2),
    6: (23.7, 24.4),
    7: (36.7, 24.4),
    8: (51.4, 37.2),
    9: (10.57, 41.4),
    10: (23.57, 41.4),
    11: (34.57, 48.4),
    12: (49.1, 57.8),
    13: (58.4, 6.2),
}

# --- Aristas ---
aristas = [
    (1, 2), (2, 3), (3, 4),
    (1, 5), (3, 7),
    (5, 6), (6, 7), (7, 8),
    (5, 9), (6, 10), (7, 11), (8, 12),
    (9, 10), (10, 11), (11, 12), (13, 4), (13, 8)
]

# --- Tráfico ---
trafico = {
    (1, 2): 0, (2, 3): 5, (3, 4): 0,
    (1, 5): 200, (3, 7): 77,
    (5, 6): 45, (6, 7): 10, (7, 8): 0,
    (5, 9): 0, (6, 10): 0, (7, 11): 0, (8, 12): 0,
    (9, 10): 0, (10, 11): 0, (11, 12): 0
}
for (u, v), val in list(trafico.items()):
    trafico[(v, u)] = val

# --- Floyd-Warshall ---
INF = float('inf')
n = len(nodos)
dist = [[INF]*(n+1) for _ in range(n+1)]
next_node = [[None]*(n+1) for _ in range(n+1)]

for i in range(1, n+1):
    dist[i][i] = 0
for u, v in aristas:
    x1, y1 = nodos[u]
    x2, y2 = nodos[v]
    base = math.hypot(x1 - x2, y1 - y2)
    extra = trafico.get((u, v), 0)
    peso = base + extra / 100  # escala el tráfico
    dist[u][v] = peso
    dist[v][u] = peso
    next_node[u][v] = v
    next_node[v][u] = u

for k in range(1, n+1):
    for i in range(1, n+1):
        for j in range(1, n+1):
            if dist[i][k] + dist[k][j] < dist[i][j]:
                dist[i][j] = dist[i][k] + dist[k][j]
                next_node[i][j] = next_node[i][k]

# --- Reconstrucción de ruta ---
def reconstruir_ruta(u, v):
    if next_node[u][v] is None:
        return []
    ruta = [u]
    while u != v:
        u = next_node[u][v]
        ruta.append(u)
    return ruta

# --- Carrito ---
class Carrito:
    def __init__(self, path, nodes):
        self.path = path
        self.nodes = nodes
        self.current_index = 0
        self.pos = nodes[path[0]]
        self.target_pos = nodes[path[1]] if len(path) > 1 else nodes[path[0]]
        self.moving = len(path) > 1

    def update(self):
        if not self.moving:
            return
        x, y = self.pos
        tx, ty = self.target_pos
        dx = tx - x
        dy = ty - y
        dist_ = math.hypot(dx, dy)
        if dist_ < CAR_SPEED:
            self.pos = self.target_pos
            self.current_index += 1
            if self.current_index >= len(self.path) - 1:
                self.moving = False
            else:
                self.target_pos = self.nodes[self.path[self.current_index + 1]]
        else:
            x += CAR_SPEED * dx / dist_
            y += CAR_SPEED * dy / dist_
            self.pos = (x, y)

    def draw(self, surface):
        pygame.draw.circle(surface, CAR_COLOR, logical_to_screen(*self.pos), int(NODE_RADIUS * zoom))

# --- Inicializar ruta ---
origen = 1
destino = 12
ruta = reconstruir_ruta(origen, destino)
if not ruta:
    print(f"No hay ruta entre {origen} y {destino}")
    sys.exit()
carrito = Carrito(ruta, nodos)

font = pygame.font.SysFont(None, 20)

# --- Bucle principal ---
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                dragging = True
                last_mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            mx, my = event.pos
            lx, ly = last_mouse_pos
            offset_x += mx - lx
            offset_y += my - ly
            last_mouse_pos = (mx, my)
        elif event.type == pygame.MOUSEWHEEL:
            zoom += ZOOM_STEP * event.y
            zoom = max(0.5, min(10, zoom))

    carrito.update()

    # Dibujar fondo tipo plano cartesiano
    screen.fill(BG_COLOR)
    grid_spacing = 5
    x = 0
    while x <= MAP_WIDTH_LOGICAL:
        pygame.draw.line(screen, GRID_COLOR, logical_to_screen(x, 0), logical_to_screen(x, MAP_HEIGHT_LOGICAL), 1)
        x += grid_spacing
    y = 0
    while y <= MAP_HEIGHT_LOGICAL:
        pygame.draw.line(screen, GRID_COLOR, logical_to_screen(0, y), logical_to_screen(MAP_WIDTH_LOGICAL, y), 1)
        y += grid_spacing

    # Dibujar calles
    for u, v in aristas:
        pygame.draw.line(screen, EDGE_COLOR, logical_to_screen(*nodos[u]), logical_to_screen(*nodos[v]), 2)

    # Dibujar ruta más corta
    for i in range(len(ruta) - 1):
        pygame.draw.line(screen, ROUTE_COLOR, logical_to_screen(*nodos[ruta[i]]), logical_to_screen(*nodos[ruta[i + 1]]), 4)

    # Dibujar nodos
    for node_id, (x, y) in nodos.items():
        pygame.draw.circle(screen, NODE_COLOR, logical_to_screen(x, y), int(NODE_RADIUS * zoom))
        img = font.render(str(node_id), True, (0, 0, 0))
        screen.blit(img, logical_to_screen(x - 1.2, y - 1.2))

    # Dibujar carrito
    carrito.draw(screen)

    # Mostrar coordenadas lógicas del mouse
    mouse_pos = pygame.mouse.get_pos()
    logical_mouse = screen_to_logical(*mouse_pos)
    mouse_text = font.render(f"x: {logical_mouse[0]:.2f}, y: {logical_mouse[1]:.2f}", True, (0, 0, 0))
    screen.blit(mouse_text, (10, 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
