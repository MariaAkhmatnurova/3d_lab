import pygame
import math
from random import randint
import map


WIDTH = 800
HEIGHT = 500
SCALE = 50

MAP_COLORS = ((255, 255, 255), (80, 80, 80))
EMPTY = 0
OUTFIELD = -1
MAP_SCALE = 10

PLAYER_STEP = 10
PLAYER_ANGLE = 10
PLAYER_SIZE = 8

WALL_HEIGHT = 400

BALL_STEP = 8


def decart(step, angle):
    dx = step * math.cos(math.radians(angle))
    dy = step * math.sin(math.radians(angle))
    return dx, dy


class Field:
    def __init__(self, field):
        self.w = len(field[0])
        self.h = len(field)
        self.field = [[EMPTY] * self.w for _ in range(self.h)]
        count = 1
        for x in range(self.w):
            for y in range(self.h):
                if field[y][x] == '#':
                    self.field[y][x] = count
                    count += 1

    def start(self):
        while True:
            x = randint(1, self.w - 2)
            y = randint(1, self.h - 2)
            if self.field[y][x] == EMPTY:
                return (x * SCALE + SCALE // 2, y * SCALE + SCALE // 2)

    def get_value(self, x0, y0):
        x = int(x0) // SCALE
        y = int(y0) // SCALE
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.field[y][x]
        return OUTFIELD

    def check(self, x, y):
        return self.get_value(x, y) == EMPTY

    def map_draw(self, screen, start_x, start_y):
        pygame.draw.rect(screen, (0, 0, 0),
                         (start_x, start_y, MAP_SCALE * self.w, MAP_SCALE * self.h))
        for y in range(self.h):
            for x in range(self.w):
                pygame.draw.rect(screen, MAP_COLORS[self.field[y][x] != EMPTY],
                            (start_x + x * MAP_SCALE, start_y + y * MAP_SCALE,
                             MAP_SCALE - 1, MAP_SCALE - 1))


class Object:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def make_vector(self, player, LENGTH):
        x2, y2 = self.x - player.x, self.y - player.y
        lenth = (x2 ** 2 + y2 ** 2) ** 0.5
        return x2 / lenth * LENGTH, y2 / lenth * LENGTH

    def counting_x(self, player):
        LENGTH = 1
        x1, y1 = decart(LENGTH, player.angle)
        x2, y2 = self.make_vector(player, LENGTH)
        cos_a = (x1 * x2 + y1 * y2) / (x1 ** 2 + y1 ** 2)
        sin_a = (x1 * y2 - x2 * y1) / (x1 ** 2 + y1 ** 2)
        return int(WIDTH * (1 + 2 ** 0.5 * sin_a) / 2), \
            cos_a >= 0

    def distance(self, player):
        x, y = self.x - player.x, self.y - player.y
        return (x ** 2 + y ** 2) ** 0.5

    def clear_path(self, player, field):
        STEP = 5
        dx, dy = self.make_vector(player, STEP)
        x = player.x
        y = player.y
        while field.check(x, y):
            if abs(self.x - x) < 2 * STEP and abs(self.y - y) < 2 * STEP:
                return True
            x += dx
            y += dy
        return False


class Ball(Object):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.last_player_coords = (x, y)
        self.last_vector = (0, 0)

    def act(self, player, field):
        if self.clear_path(player, field):
            dx, dy = self.make_vector(player, BALL_STEP)
            self.x -= dx
            self.y -= dy
            self.last_vector = (dx, dy)
            self.last_player_coords = (player.x, player.y)

        elif abs(self.last_player_coords[0] - self.x) >= BALL_STEP or\
             abs(self.last_player_coords[1] - self.y) >= BALL_STEP:
            self.x -= self.last_vector[0]
            self.y -= self.last_vector[1]

        if abs(player.x - self.x) < BALL_STEP and\
             abs(player.y - self.y) < BALL_STEP:
            return False

        return True

    def draw(self, screen, player, field):
        SIZE = 300
        if not self.clear_path(player, field):
            return
        x, visible = self.counting_x(player)
        if not visible:
            return
        dist = self.distance(player)
        size = int(SIZE * SCALE / dist)
        pygame.draw.circle(screen, (255, 255, 0), (x, HEIGHT // 2), size)
        y = HEIGHT // 2
        pygame.draw.circle(screen, (255, 255, 255),
                           (x - size // 2, y - size // 4),
                           size // 6, size // 14)
        pygame.draw.circle(screen, (255, 255, 255),
                           (x + size // 2, y - size // 4),
                           size // 6, size // 14)
        pi2 = math.pi / 2
        size34 = size // 4 * 3
        pygame.draw.arc(screen, (200, 0, 0),
                        (x - size34, y - size34, size34 * 2, size34 * 2),
                        -pi2 - SCALE / dist,
                        -pi2 + SCALE / dist, size // 20)

    def map_draw(self, screen, start_x, start_y):
        pygame.draw.circle(screen, (255, 255, 0),
                           (start_x + int(self.x / SCALE * MAP_SCALE),
                        start_y + int(self.y / SCALE * MAP_SCALE)), 4)


class Wall(Object):
    def __init__(self, x1, y1, x2, y2, player):
        super().__init__(0, 0)
        self.x = x1
        self.y = y1
        self.left_x, v1 = self.counting_x(player)
        self.dist1 = self.point_distance(x1, y1, player)
        self.up_y1, self.down_y1 = self.counting_y(self.dist1)

        self.x = (x1 + x2) // 2
        self.y = (y1 + y2) // 2
        self.mid_x, v2 = self.counting_x(player)
        self.dist2 = self.point_distance(self.x, self.y, player)
        self.up_y2, self.down_y2 = self.counting_y(self.dist2)

        self.x = x2
        self.y = y2
        self.right_x, v3 = self.counting_x(player)
        self.dist3 = self.point_distance(x2, y2, player)
        self.up_y3, self.down_y3 = self.counting_y(self.dist3)

        self.visible = v1 or v2 or v3

    def __lt__(self, obj):
        return self.distance() < obj.distance()

    def distance(self):
        return min(self.dist1, self.dist2)

    def point_distance(self, x, y, player):
        x1, y1 = x - player.x, y - player.y
        return (x1 ** 2 + y1 ** 2) ** 0.5

    def counting_y(self, dist):
        height = int(WALL_HEIGHT * (SCALE / dist))
        return HEIGHT // 2 - height // 2, HEIGHT // 2 + height // 2

    def draw(self, screen):
        if not self.visible:
            return

        pygame.draw.polygon(screen, (150, 150, 150),
                            ((self.left_x, self.down_y1), (self.left_x, self.up_y1),
                             (self.mid_x, self.up_y2), (self.right_x, self.up_y3),
                             (self.right_x, self.down_y3), (self.mid_x, self.down_y2)))
        pygame.draw.polygon(screen, (60, 60, 60),
                            ((self.left_x, self.down_y1), (self.left_x, self.up_y1),
                             (self.mid_x, self.up_y2), (self.right_x, self.up_y3),
                             (self.right_x, self.down_y3), (self.mid_x, self.down_y2)), 2)

class Player:
    def __init__(self, x, y):
        self.angle = 0
        self.x = x
        self.y = y

    def move(self, field, matrix):
        dx, dy = decart(PLAYER_STEP, self.angle)
        x = int(self.x + matrix[0][0] * dx * 3 + matrix[0][1] * dy * 3)
        y = int(self.y + matrix[1][0] * dx * 3 + matrix[1][1] * dy * 3)
        if field.check(x, y):
            self.x = int(self.x + matrix[0][0] * dx + matrix[0][1] * dy)
            self.y = int(self.y + matrix[1][0] * dx + matrix[1][1] * dy)

    def move_forward(self, field):
        self.move(field, ((1, 0), (0, 1)))

    def move_backward(self, field):
        self.move(field, ((-1, 0), (0, -1)))

    def move_left(self, field):
        self.move(field, ((0, 1), (-1, 0)))

    def move_right(self, field):
        self.move(field, ((0, -1), (1, 0)))

    def turn_left(self):
        self.angle -= PLAYER_ANGLE

    def turn_right(self):
        self.angle += PLAYER_ANGLE

    def map_draw(self, screen, start_x, start_y):
        rect = pygame.Rect(start_x + int(self.x / SCALE * MAP_SCALE) - PLAYER_SIZE // 2,
                           start_y + int(self.y / SCALE * MAP_SCALE) - PLAYER_SIZE // 2,
                           PLAYER_SIZE, PLAYER_SIZE)
        pygame.draw.arc(screen, (0, 0, 0), rect,
                        math.radians(-self.angle - 45),
                        math.radians(-self.angle + 45), 20)


class Game:
    def __init__(self):
        self.field = Field(map.map_1)
        self.player = Player(*self.field.start())
        self.ball = Ball(*self.field.start())
        self.start_pos = (WIDTH - MAP_SCALE * self.field.w,
                          HEIGHT - MAP_SCALE * self.field.h)
        self.game_on = True

    def ray_casting(self, screen):
        DEGREE = 0.5
        WALL_HEIGHT = 400
        RECT_WIDTH = int(WIDTH / 90 * DEGREE)
        STEP = 3

        wall_left = 0
        for angle in range(self.player.angle - 45,
                           self.player.angle + 45 + DEGREE, DEGREE):
            x = self.player.x
            y = self.player.y
            dx, dy = decart(STEP, angle)
            dist = 0
            while self.field.check(x, y):
                x += dx
                y += dy
                dist += STEP
            if not dist:
                continue
            wall_height = WALL_HEIGHT * (SCALE / dist)
            wall_up = HEIGHT // 2 - wall_height // 2
            pygame.draw.rect(screen, (150, 150, 150),
                             (wall_left, wall_up, RECT_WIDTH - 1, wall_height))
            wall_left += RECT_WIDTH

    def ray_casting2(self, screen):
        DEGREE = 1
        WALL_HEIGHT = 400
        RECT_WIDTH = int(WIDTH / 90 * DEGREE)
        STEP = 3

        last_wall = -1
        walls = []
        for angle in range(self.player.angle - 45,
                           self.player.angle + 45 + DEGREE, DEGREE):
            x = self.player.x
            y = self.player.y
            dx, dy = decart(STEP, angle)
            while self.field.check(x, y):
                x += dx
                y += dy

            lw = self.field.get_value(x, y)
            if lw == last_wall:
                continue
            else:
                last_wall = lw

            x0, y0 = int(x) // SCALE * SCALE, int(y) // SCALE * SCALE
            x1, y1 = x0 + SCALE, y0 + SCALE

            if self.player.x < x0 and self.field.check(x0 - 1, y0 + 1):
                walls.append(Wall(x0, y0, x0, y1, self.player))
            elif self.player.x > x1 and self.field.check(x1 + 1, y0 + 1):
                walls.append(Wall(x1, y0, x1, y1, self.player))

            if self.player.y < y0 and self.field.check(x0 + 1, y0 - 1):
                walls.append(Wall(x0, y0, x1, y0, self.player))
            elif self.player.y > y1 and self.field.check(x0 + 1, y1 + 1):
                walls.append(Wall(x0, y1, x1, y1, self.player))

            walls.sort(reverse=True)
            for wall in walls:
                wall.draw(screen)

    def draw_floor_ceiling(self, screen):
        color = 150
        STRIP_WIDTH = 3
        for h in range(0, HEIGHT // 2, STRIP_WIDTH):
            pygame.draw.line(screen, (0, color, color + 50), (0, h), (WIDTH, h), STRIP_WIDTH)
            pygame.draw.line(screen, (color, color, color), (0, HEIGHT - h),
                             (WIDTH, HEIGHT - h), STRIP_WIDTH)
            color -= 2
            if color < 0:
                color = 0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.player.move_forward(self.field)
        if keys[pygame.K_s]:
            self.player.move_backward(self.field)
        if keys[pygame.K_a]:
            self.player.move_left(self.field)
        if keys[pygame.K_d]:
            self.player.move_right(self.field)
        if keys[pygame.K_LEFT]:
            self.player.turn_left()
        if keys[pygame.K_RIGHT]:
            self.player.turn_right()
        if keys[pygame.K_SPACE]:
            self.player = Player(*self.field.start())
            self.ball = Ball(*self.field.start())
            self.game_on = True

        self.game_on = self.ball.act(self.player, self.field)
        return 'continue'

    def draw(self, screen):
        screen.fill((0, 0, 0))
        self.draw_floor_ceiling(screen)
        if not self.game_on:
            text = pygame.font.SysFont('Arial', 30).render('Game Over!', 1, (255, 0, 0))
            screen.blit(text, (320, HEIGHT // 2))
            return
        self.ray_casting2(screen)
        self.ball.draw(screen, self.player, self.field)
        self.field.map_draw(screen, *self.start_pos)
        self.player.map_draw(screen, *self.start_pos)
        self.ball.map_draw(screen, *self.start_pos)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    game = Game()
    while True:
        run = game.handle_events()
        if run == 'quit':
            break
        game.draw(screen)
        pygame.display.update()
        pygame.time.delay(100)
    pygame.quit()


main()




