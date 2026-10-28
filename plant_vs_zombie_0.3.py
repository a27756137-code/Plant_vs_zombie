import pygame
import random
import math
import sys
import json
import os

# Включаем горизонтальную ориентацию для телефона / Pydroid 3
os.environ["SDL_HINT_ORIENTATIONS"] = "LandscapeLeft LandscapeRight"

pygame.init()

WIDTH, HEIGHT = 960, 600
FPS = 60

ROWS = 5
COLS = 8
CELL_SIZE = 76
GRID_X = 175
GRID_Y = 125

# Полноэкранный режим с авто-масштабированием кликов
try:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
except Exception:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Plants vs. Zombies — Ultimate Edition")
clock = pygame.time.Clock()

def get_font(size, bold=True):
    for name in ["arial", "dejavusans", "verdana", "roboto", "sans"]:
        f = pygame.font.SysFont(name, size, bold=bold)
        if f:
            return f
    return pygame.font.Font(None, size)

font_xs = get_font(12)
font_sm = get_font(14)
font_md = get_font(18)
font_lg = get_font(28)
font_xl = get_font(42)


# =====================================================================
# 1. СИСТЕМА СОХРАНЕНИЙ (Стартовые монеты: 0)
# =====================================================================
SAVE_FILE = "pvz_ultimate_save.json"

def get_default_save():
    return {
        "coins": 0,  # Стартовое значение 0 монет!
        "max_level": 1,  # 1: День, 2: Ночь, 3: Бассейн, 4: Крыша
        "unlocked_plants": ["sunflower", "peashooter"],
        "stats": {"kills": 0, "coins_collected": 0, "bosses_killed": 0},
        "achievements": {
            "first_blood": False,
            "zombie_hunter": False,
            "boss_slayer": False,
            "collector": False,
            "roof_master": False,
        }
    }

def load_save():
    default = get_default_save()
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in default.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            pass
    return default

def write_save(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

SAVE_DATA = load_save()


# =====================================================================
# 2. КАТАЛОГ РАСТЕНИЙ И ДОСТИЖЕНИЙ
# =====================================================================
PLANT_CATALOG = {
    "sunflower":  {"name": "Подсолнух",   "cost": 50,  "hp": 100, "cd": 5.0,  "shop": 0,   "desc": "Даёт солнышки"},
    "peashooter": {"name": "Горохострел", "cost": 100, "hp": 100, "cd": 5.0,  "shop": 0,   "desc": "Стреляет горохом"},
    "puffshroom": {"name": "Пыхгриб",     "cost": 0,   "hp": 80,  "cd": 4.5,  "shop": 0,   "desc": "Выдаётся Ночью (0 солнц)"},
    "lilypad":    {"name": "Кувшинка",    "cost": 25,  "hp": 100, "cd": 3.5,  "shop": 0,   "desc": "Выдаётся в Бассейне"},
    "cabbage":    {"name": "Капупульта",  "cost": 100, "hp": 100, "cd": 5.5,  "shop": 0,   "desc": "Выдаётся на Крыше"},
    "mine":       {"name": "Карт. мина",  "cost": 25,  "hp": 100, "cd": 12.0, "shop": 50,  "desc": "Взрыв (5 сек взвод)"},
    "wallnut":    {"name": "Стена-орех",  "cost": 50,  "hp": 650, "cd": 11.0, "shop": 75,  "desc": "Крепкая броня"},
    "snowpea":    {"name": "Мороз-горох", "cost": 150, "hp": 100, "cd": 6.5,  "shop": 120, "desc": "Замедляет врагов"},
    "cherry":     {"name": "Вишня-бомба", "cost": 150, "hp": 100, "cd": 16.0, "shop": 150, "desc": "Мощный взрыв 3x3"},
    "repeater":   {"name": "Двойной горох","cost": 200, "hp": 120, "cd": 6.5,  "shop": 200, "desc": "2 горошины сразу"},
}

LEVEL_INFO = {
    1: {"name": "День",    "mandatory": ["sunflower", "peashooter"], "boss_name": "Зомби-Тракторист"},
    2: {"name": "Ночь",    "mandatory": ["sunflower", "puffshroom"], "boss_name": "Некромант Ночи"},
    3: {"name": "Бассейн", "mandatory": ["sunflower", "lilypad"],    "boss_name": "Меха-Кракен"},
    4: {"name": "Крыша",   "mandatory": ["sunflower", "cabbage"],    "boss_name": "Доктор Зомбосс"},
}

ACHIEVEMENTS_INFO = {
    "first_blood":   {"title": "Первая победа",     "desc": "Пройти 1-й уровень (День)",         "reward": 30},
    "zombie_hunter": {"title": "Охотник на зомби",  "desc": "Уничтожить 30 зомби за всё время",  "reward": 50},
    "boss_slayer":   {"title": "Гроза Боссов",      "desc": "Победить любого Босса уровня",      "reward": 50},
    "collector":     {"title": "Нумизмат",          "desc": "Собрать 15 монет на поле боя",      "reward": 40},
    "roof_master":   {"title": "Повелитель Крыши",  "desc": "Пройти 4-й уровень и победить Зомбосса", "reward": 150},
}


# =====================================================================
# 3. ПИКСЕЛЬ-АРТ ГЕНЕРАТОР ТЕКСТУР 32x32 (Все текстуры прорисованы!)
# =====================================================================
def surf32():
    return pygame.Surface((32, 32), pygame.SRCALPHA)

def scale32(s, w=CELL_SIZE, h=CELL_SIZE):
    return pygame.transform.scale(s, (w, h))

def build_all_textures():
    t = {}

    # 1. Плитки поля (День, Ночь, Вода, Крыша)
    for name, c1, c2 in [
        ("day_0", (95, 185, 65), (80, 160, 52)),
        ("day_1", (82, 168, 55), (68, 148, 44)),
        ("night_0", (42, 68, 98), (32, 54, 80)),
        ("night_1", (35, 58, 86), (26, 46, 70)),
        ("roof_0", (170, 88, 55), (140, 68, 40)),
        ("roof_1", (155, 78, 48), (128, 60, 35)),
    ]:
        s = surf32()
        s.fill(c1)
        pygame.draw.rect(s, c2, (0, 0, 32, 32), 1)
        if "roof" in name:
            for y in range(6, 32, 8):
                pygame.draw.line(s, c2, (0, y), (31, y), 1)
        else:
            for i in range(12):
                s.set_at(((i * 7 + 3) % 30, (i * 11 + 5) % 30), c2)
        t[name] = scale32(s)

    w = surf32()
    w.fill((45, 135, 215))
    for y in range(5, 30, 8):
        pygame.draw.arc(w, (110, 195, 255), (4, y, 12, 5), 0, math.pi, 1)
        pygame.draw.arc(w, (110, 195, 255), (16, y + 2, 12, 5), 0, math.pi, 1)
    pygame.draw.rect(w, (35, 110, 185), (0, 0, 32, 32), 1)
    t["water"] = scale32(w)

    # 2. Растения (32x32)
    # Подсолнух
    sf = surf32()
    pygame.draw.rect(sf, (40, 150, 40), (14, 18, 4, 11))
    pygame.draw.ellipse(sf, (50, 180, 45), (7, 25, 9, 5))
    pygame.draw.ellipse(sf, (50, 180, 45), (16, 25, 9, 5))
    for a in range(0, 360, 30):
        rx, ry = int(16 + math.cos(math.radians(a)) * 8), int(12 + math.sin(math.radians(a)) * 8)
        pygame.draw.circle(sf, (255, 215, 20), (rx, ry), 4)
    pygame.draw.circle(sf, (125, 70, 25), (16, 12), 7)
    pygame.draw.rect(sf, (20, 20, 20), (13, 10, 2, 3))
    pygame.draw.rect(sf, (20, 20, 20), (18, 10, 2, 3))
    t["sunflower"] = scale32(sf)
    t["sunflower_icon"] = scale32(sf, 38, 38)

    # Горохострел, Морозный горох, Двойной горох
    for key, body_c, dark_c in [
        ("peashooter", (75, 210, 55), (35, 130, 30)),
        ("snowpea", (90, 195, 250), (35, 115, 175)),
        ("repeater", (55, 185, 45), (25, 110, 25)),
    ]:
        p = surf32()
        pygame.draw.rect(p, (35, 145, 35), (13, 17, 4, 12))
        pygame.draw.ellipse(p, (50, 175, 45), (7, 25, 18, 5))
        pygame.draw.circle(p, body_c, (13, 12), 7)
        pygame.draw.rect(p, body_c, (17, 8, 9, 8))
        pygame.draw.ellipse(p, dark_c, (24, 7, 4, 10))
        pygame.draw.rect(p, (15, 15, 15), (14, 9, 3, 4))
        if key == "snowpea":
            pygame.draw.polygon(p, (210, 245, 255), [(6, 9), (2, 6), (6, 14)])
        elif key == "repeater":
            pygame.draw.polygon(p, (40, 140, 30), [(8, 5), (14, 2), (16, 6)])
        t[key] = scale32(p)
        t[f"{key}_icon"] = scale32(p, 38, 38)

    # Пыхгриб (Ночной гриб)
    pf = surf32()
    pygame.draw.ellipse(pf, (225, 215, 195), (10, 18, 12, 11))
    pygame.draw.ellipse(pf, (155, 75, 205), (5, 9, 22, 12))
    pygame.draw.circle(pf, (205, 145, 245), (11, 13), 2)
    pygame.draw.circle(pf, (205, 145, 245), (20, 14), 3)
    pygame.draw.rect(pf, (15, 15, 15), (13, 21, 2, 3))
    pygame.draw.rect(pf, (15, 15, 15), (18, 21, 2, 3))
    pygame.draw.circle(pf, (120, 50, 165), (25, 22), 3)
    t["puffshroom"] = scale32(pf)
    t["puffshroom_icon"] = scale32(pf, 38, 38)

    # Кувшинка (Бассейн)
    lp = surf32()
    pygame.draw.ellipse(lp, (45, 175, 55), (3, 18, 26, 12))
    pygame.draw.ellipse(lp, (25, 125, 35), (3, 18, 26, 12), 2)
    pygame.draw.polygon(lp, (45, 135, 215), [(16, 24), (28, 20), (28, 26)])
    pygame.draw.circle(lp, (255, 190, 210), (11, 21), 3)
    t["lilypad"] = scale32(lp)
    t["lilypad_icon"] = scale32(lp, 38, 38)

    # Капупульта (Крыша)
    cb = surf32()
    pygame.draw.ellipse(cb, (70, 190, 60), (7, 15, 18, 14))
    pygame.draw.ellipse(cb, (45, 140, 40), (7, 15, 18, 14), 1)
    pygame.draw.line(cb, (50, 140, 40), (14, 16), (6, 6), 3)
    pygame.draw.circle(cb, (110, 225, 85), (6, 6), 5)
    pygame.draw.rect(cb, (20, 20, 20), (14, 19, 2, 3))
    pygame.draw.rect(cb, (20, 20, 20), (19, 19, 2, 3))
    t["cabbage"] = scale32(cb)
    t["cabbage_icon"] = scale32(cb, 38, 38)

    # Картофельная мина
    mn = surf32()
    pygame.draw.ellipse(mn, (185, 140, 80), (6, 14, 20, 14))
    pygame.draw.rect(mn, (150, 150, 150), (15, 7, 2, 7))
    pygame.draw.circle(mn, (255, 40, 40), (16, 6), 4)
    pygame.draw.rect(mn, (255, 255, 255), (11, 18, 3, 3))
    pygame.draw.rect(mn, (255, 255, 255), (18, 18, 3, 3))
    t["mine"] = scale32(mn)
    t["mine_icon"] = scale32(mn, 38, 38)

    mn_sub = surf32()
    pygame.draw.ellipse(mn_sub, (115, 75, 40), (7, 22, 18, 7))
    pygame.draw.circle(mn_sub, (255, 200, 40), (16, 17), 3)
    t["mine_buried"] = scale32(mn_sub)

    # Орех
    wn = surf32()
    pygame.draw.ellipse(wn, (175, 120, 55), (6, 5, 20, 25))
    pygame.draw.ellipse(wn, (120, 75, 30), (6, 5, 20, 25), 2)
    pygame.draw.circle(wn, (255, 255, 255), (13, 14), 3)
    pygame.draw.circle(wn, (255, 255, 255), (19, 14), 3)
    pygame.draw.circle(wn, (20, 20, 20), (14, 14), 1)
    pygame.draw.circle(wn, (20, 20, 20), (20, 14), 1)
    t["wallnut"] = scale32(wn)
    t["wallnut_icon"] = scale32(wn, 38, 38)

    # Вишня-бомба
    ch = surf32()
    pygame.draw.line(ch, (50, 150, 50), (11, 18), (16, 5), 2)
    pygame.draw.line(ch, (50, 150, 50), (21, 18), (16, 5), 2)
    pygame.draw.circle(ch, (225, 25, 35), (10, 20), 7)
    pygame.draw.circle(ch, (225, 25, 35), (22, 20), 7)
    pygame.draw.circle(ch, (255, 255, 255), (9, 19), 2)
    pygame.draw.circle(ch, (255, 255, 255), (21, 19), 2)
    t["cherry"] = scale32(ch)
    t["cherry_icon"] = scale32(ch, 38, 38)

    # 3. Зомби (6 видов + 4 Босса)
    for zt in ["normal", "cone", "bucket", "pole", "football", "balloon", "boss1", "boss2", "boss3", "boss4"]:
        z = surf32()
        # Ноги и тело
        pants = (230, 230, 230) if zt == "football" else (50, 70, 110)
        coat = (210, 35, 35) if zt == "football" else ((90, 40, 120) if zt == "boss2" else (75, 65, 60))
        pygame.draw.rect(z, pants, (13, 23, 4, 8))
        pygame.draw.rect(z, pants, (18, 23, 4, 8))
        pygame.draw.rect(z, coat, (11, 14, 11, 10))
        pygame.draw.rect(z, (115, 160, 110), (5, 15, 7, 3))  # Руки
        pygame.draw.rect(z, (115, 160, 110), (11, 6, 10, 9))  # Голова
        pygame.draw.circle(z, (255, 240, 150), (13, 10), 2)
        pygame.draw.circle(z, (200, 20, 20), (13, 10), 1)

        if zt == "cone":
            pygame.draw.polygon(z, (245, 125, 20), [(10, 7), (22, 7), (16, 0)])
        elif zt == "bucket":
            pygame.draw.rect(z, (165, 170, 180), (10, 0, 12, 8))
        elif zt == "pole":
            pygame.draw.line(z, (220, 190, 120), (2, 24), (29, 8), 2)
            pygame.draw.rect(z, (220, 50, 50), (11, 5, 10, 2))
        elif zt == "football":
            pygame.draw.ellipse(z, (220, 30, 30), (9, 3, 14, 11))
            pygame.draw.rect(z, (220, 220, 220), (9, 7, 5, 5), 1)
        elif zt == "balloon":
            pygame.draw.line(z, (220, 220, 220), (16, 14), (16, 5), 1)
            pygame.draw.circle(z, (255, 50, 70), (16, 4), 4)
        elif zt.startswith("boss"):
            # Корона/шлем босса и гигантский размер
            pygame.draw.rect(z, (255, 200, 20), (9, 1, 14, 5))
            pygame.draw.circle(z, (255, 30, 30), (13, 10), 2)
            if zt == "boss1":  # На тракторе
                pygame.draw.rect(z, (220, 40, 40), (4, 20, 24, 9))
                pygame.draw.circle(z, (30, 30, 30), (9, 29), 4)
                pygame.draw.circle(z, (30, 30, 30), (23, 29), 4)
            elif zt == "boss3":  # Кракен
                pygame.draw.rect(z, (40, 190, 170), (6, 14, 20, 15))
            elif zt == "boss4":  # Зомбосс-Мех
                pygame.draw.rect(z, (130, 140, 155), (5, 10, 22, 20))

        size = (CELL_SIZE + 18, CELL_SIZE + 18) if zt.startswith("boss") else (CELL_SIZE, CELL_SIZE)
        t[f"z_{zt}"] = scale32(z, size[0], size[1])

    # 4. Солнышко, Монета, Снаряды, Лопата, Косилка
    sun = surf32()
    pygame.draw.circle(sun, (255, 200, 20), (16, 16), 14)
    pygame.draw.circle(sun, (255, 245, 90), (16, 16), 10)
    t["sun"] = scale32(sun, 46, 46)
    t["sun_icon"] = scale32(sun, 32, 32)

    coin = surf32()
    pygame.draw.circle(coin, (255, 215, 0), (16, 16), 11)
    pygame.draw.circle(coin, (200, 150, 0), (16, 16), 11, 2)
    pygame.draw.rect(coin, (255, 250, 180), (14, 10, 4, 12))
    t["coin"] = scale32(coin, 38, 38)

    for b_name, b_col in [
        ("pea", (90, 235, 65)),
        ("snow", (110, 210, 255)),
        ("spore", (190, 100, 250)),
        ("cabbage_proj", (100, 220, 75)),
        ("fireball", (255, 90, 20)),
    ]:
        b = surf32()
        pygame.draw.circle(b, b_col, (16, 16), 10)
        pygame.draw.circle(b, (255, 255, 255), (13, 13), 3)
        t[b_name] = scale32(b, 22, 22)

    sh = surf32()
    pygame.draw.line(sh, (160, 110, 50), (6, 26), (22, 10), 4)
    pygame.draw.polygon(sh, (190, 195, 205), [(18, 6), (27, 6), (27, 15), (21, 15)])
    t["shovel"] = scale32(sh, 40, 40)

    mw = surf32()
    pygame.draw.rect(mw, (220, 45, 45), (6, 14, 20, 11), border_radius=3)
    pygame.draw.circle(mw, (40, 40, 45), (10, 26), 4)
    pygame.draw.circle(mw, (40, 40, 45), (22, 26), 4)
    t["mower"] = scale32(mw, 52, 52)

    return t

TEX = build_all_textures()
# =====================================================================
# 4. ИГРОВЫЕ ОБЪЕКТЫ (Растения, Снаряды, Зомби, Боссы, Монеты)
# =====================================================================
class Plant:
    def __init__(self, row, col, p_type, has_lilypad=False):
        self.row = row
        self.col = col
        self.type = p_type
        self.has_lilypad = has_lilypad
        self.x = GRID_X + col * CELL_SIZE
        self.y = GRID_Y + row * CELL_SIZE

        info = PLANT_CATALOG[p_type]
        self.max_hp = info["hp"]
        self.hp = float(self.max_hp)
        self.timer = 0.0
        self.burst_pending = False
        self.burst_timer = 0.0
        self.armed = False

    def update(self, dt, game):
        self.timer += dt

        # Вторая горошина для Двойного гороха
        if self.burst_pending:
            self.burst_timer -= dt
            if self.burst_timer <= 0:
                self.burst_pending = False
                game.projectiles.append(Projectile(self.row, self.x + 52, self.y + 20, "pea", 22))

        if self.type == "sunflower":
            if self.timer >= 8.5:
                self.timer = 0.0
                game.suns.append(DropItem(self.x + 35, self.y + 15, self.y + 52, "sun"))

        elif self.type in ("peashooter", "snowpea", "repeater", "puffshroom", "cabbage"):
            cd_shoot = 1.45
            if self.timer >= cd_shoot:
                # Пыхгриб бьёт на 4 клетки вперёд, остальные — на всю линию
                max_dist = self.x + CELL_SIZE * 4.2 if self.type == "puffshroom" else WIDTH + 30
                has_target = any(z.row == self.row and self.x <= z.x <= max_dist for z in game.zombies)
                if has_target:
                    self.timer = 0.0
                    if self.type == "peashooter":
                        game.projectiles.append(Projectile(self.row, self.x + 52, self.y + 20, "pea", 22))
                    elif self.type == "snowpea":
                        game.projectiles.append(Projectile(self.row, self.x + 52, self.y + 20, "snow", 22, slow=True))
                    elif self.type == "repeater":
                        game.projectiles.append(Projectile(self.row, self.x + 52, self.y + 20, "pea", 22))
                        self.burst_pending = True
                        self.burst_timer = 0.18
                    elif self.type == "puffshroom":
                        game.projectiles.append(Projectile(self.row, self.x + 48, self.y + 26, "spore", 18))
                    elif self.type == "cabbage":
                        game.projectiles.append(Projectile(self.row, self.x + 45, self.y + 15, "cabbage_proj", 30, lobbed=True))

        elif self.type == "mine":
            if not self.armed and self.timer >= 5.0:
                self.armed = True

    def draw(self, surf):
        if self.has_lilypad and self.type != "lilypad":
            surf.blit(TEX["lilypad"], (self.x, self.y + 8))

        if self.type == "mine" and not self.armed:
            surf.blit(TEX["mine_buried"], (self.x, self.y))
            prog = min(1.0, self.timer / 5.0)
            pygame.draw.rect(surf, (40, 40, 40), (self.x + 14, self.y + 8, 48, 5))
            pygame.draw.rect(surf, (255, 215, 40), (self.x + 14, self.y + 8, int(48 * prog), 5))
        else:
            y_off = -4 if (self.has_lilypad and self.type != "lilypad") else 0
            surf.blit(TEX[self.type], (self.x, self.y + y_off))

        if self.hp < self.max_hp:
            ratio = max(0.0, self.hp / self.max_hp)
            pygame.draw.rect(surf, (40, 20, 20), (self.x + 12, self.y + CELL_SIZE - 8, 52, 5))
            pygame.draw.rect(surf, (90, 235, 80), (self.x + 12, self.y + CELL_SIZE - 8, int(52 * ratio), 5))


class Projectile:
    def __init__(self, row, x, y, p_type, damage, slow=False, lobbed=False, is_enemy=False):
        self.row = row
        self.x = float(x)
        self.start_x = float(x)
        self.y = float(y)
        self.base_y = float(y)
        self.type = p_type
        self.damage = damage
        self.slow = slow
        self.lobbed = lobbed
        self.is_enemy = is_enemy
        self.speed = -260.0 if is_enemy else 340.0
        self.alive = True
        self.flight_time = 0.0

    def update(self, dt, game):
        self.x += self.speed * dt
        self.flight_time += dt

        if self.lobbed:
            # Навесная траектория для Капупульты
            self.y = self.base_y - abs(math.sin(self.flight_time * 5.5)) * 32

        if self.x > WIDTH + 30 or self.x < GRID_X - 40:
            self.alive = False
            return

        if self.is_enemy:
            # Огненный шар Зомбосса бьёт по растениям
            for p in list(game.plants):
                if p.row == self.row and abs((p.x + 35) - self.x) < 28:
                    p.hp -= self.damage
                    if p.hp <= 0:
                        game.remove_plant(p)
                    self.alive = False
                    break
        else:
            for z in game.zombies:
                if z.row == self.row and z.x + 10 <= self.x <= z.x + 65:
                    z.hp -= self.damage
                    if self.slow:
                        z.slow_timer = 4.0
                    if z.z_type == "balloon":
                        z.z_type = "normal"  # Сбили шарик!
                    self.alive = False
                    break

    def draw(self, surf):
        surf.blit(TEX[self.type], (int(self.x), int(self.y)))


class Zombie:
    def __init__(self, row, z_type="normal", boss_lvl=0):
        self.row = row
        self.x = float(WIDTH + random.randint(5, 35))
        self.y = float(GRID_Y + row * CELL_SIZE)
        self.z_type = z_type
        self.boss_lvl = boss_lvl
        self.skill_timer = 0.0
        self.slow_timer = 0.0

        hp_map = {
            "normal": 100, "cone": 240, "bucket": 440,
            "pole": 150, "football": 620, "balloon": 120
        }
        spd_map = {
            "normal": 20.0, "cone": 19.0, "bucket": 17.0,
            "pole": 35.0, "football": 30.0, "balloon": 28.0
        }

        if boss_lvl > 0:
            self.z_type = f"boss{boss_lvl}"
            self.max_hp = 900 + boss_lvl * 350
            self.base_speed = 11.5
            self.damage = 75.0
        else:
            self.max_hp = hp_map.get(z_type, 100)
            self.base_speed = spd_map.get(z_type, 20.0)
            self.damage = 28.0

        self.hp = float(self.max_hp)

    def update(self, dt, game):
        spd = self.base_speed * (0.5 if self.slow_timer > 0 else 1.0)
        if self.slow_timer > 0:
            self.slow_timer -= dt

        # Потеря брони у конуса и ведра
        if self.boss_lvl == 0:
            if self.z_type == "bucket" and self.hp <= 240:
                self.z_type = "cone"
            elif self.z_type == "cone" and self.hp <= 100:
                self.z_type = "normal"

        # Способности Боссов
        if self.boss_lvl == 2:  # Некромант призывает зомби
            self.skill_timer += dt
            if self.skill_timer >= 7.0:
                self.skill_timer = 0.0
                r_spawn = random.randint(0, ROWS - 1)
                z_minion = Zombie(r_spawn, "cone")
                z_minion.x = max(GRID_X + 180.0, self.x - 60.0)
                game.zombies.append(z_minion)
        elif self.boss_lvl == 4:  # Зомбосс стреляет огненными шарами
            self.skill_timer += dt
            if self.skill_timer >= 4.5:
                self.skill_timer = 0.0
                game.projectiles.append(Projectile(self.row, self.x, self.y + 24, "fireball", 80, is_enemy=True))

        # Проверка растений на пути (Зомби на шарике перелетает их!)
        target = None
        if self.z_type != "balloon":
            for p in game.plants:
                if p.row == self.row and p.x + 12 <= self.x + 30 <= p.x + CELL_SIZE + 4:
                    target = p
                    break

        if target:
            if target.type == "mine" and target.armed:
                game.explode_mine(target)
                return
            target.hp -= self.damage * dt
            if target.hp <= 0:
                game.remove_plant(target)
            # Бегун с шестом после первой встречи теряет разбег
            if self.z_type == "pole":
                self.base_speed = 19.0
        else:
            self.x -= spd * dt

    def draw(self, surf):
        y_draw = int(self.y - 14) if self.boss_lvl > 0 else int(self.y - 4)
        if self.z_type == "balloon":
            y_draw -= 12
        surf.blit(TEX[f"z_{self.z_type}"], (int(self.x), y_draw))

        if self.hp < self.max_hp and self.boss_lvl == 0:
            ratio = max(0.0, self.hp / self.max_hp)
            pygame.draw.rect(surf, (40, 20, 20), (int(self.x + 12), int(self.y - 8), 48, 5))
            pygame.draw.rect(surf, (235, 70, 50), (int(self.x + 12), int(self.y - 8), int(48 * ratio), 5))


class DropItem:
    def __init__(self, x, y, target_y, item_type="sun", value=25):
        self.x = float(x)
        self.y = float(y)
        self.target_y = float(target_y)
        self.type = item_type  # "sun" или "coin"
        self.value = value
        self.collected = False
        self.alive = True
        self.timer = 11.0

    def update(self, dt, game):
        if self.collected:
            tx, ty = (50.0, 42.0) if self.type == "sun" else (820.0, 25.0)
            dx, dy = tx - self.x, ty - self.y
            dist = math.hypot(dx, dy)
            if dist < 20:
                if self.type == "sun":
                    game.sun += self.value
                else:
                    SAVE_DATA["coins"] += self.value
                    SAVE_DATA["stats"]["coins_collected"] += 1
                    game.coins_earned += self.value
                    game.check_achievements()
                    write_save(SAVE_DATA)
                self.alive = False
            else:
                self.x += (dx / dist) * 680 * dt
                self.y += (dy / dist) * 680 * dt
        else:
            if self.y < self.target_y:
                self.y += 75.0 * dt
            else:
                self.timer -= dt
                if self.timer <= 0:
                    self.alive = False

    def draw(self, surf):
        surf.blit(TEX[self.type], (int(self.x - 20), int(self.y - 20)))


class LawnMower:
    def __init__(self, row):
        self.row = row
        self.x = float(GRID_X - 56)
        self.y = float(GRID_Y + row * CELL_SIZE + 14)
        self.active = False
        self.alive = True

    def update(self, dt, game):
        if not self.active:
            for z in game.zombies:
                if z.row == self.row and z.x < self.x + 42:
                    self.active = True
                    break
        else:
            self.x += 390.0 * dt
            for z in game.zombies:
                if z.row == self.row and abs(z.x - self.x) < 48:
                    if z.boss_lvl > 0:
                        z.hp -= 450  # Боссу наносит огромный урон, а обычных сносит сразу
                        self.alive = False
                    else:
                        z.hp = 0
            if self.x > WIDTH + 40:
                self.alive = False

    def draw(self, surf):
        surf.blit(TEX["mower"], (int(self.x), int(self.y)))


# =====================================================================
# 5. ГЛАВНЫЙ КЛАСС ИГРЫ И УРОВНЕЙ
# =====================================================================
class PvZUltimateGame:
    def __init__(self):
        self.state = "MENU"  # MENU, SHOP, ACHIV, PLAYING, VICTORY, GAMEOVER
        self.level = 1
        self.popup_text = ""
        self.popup_timer = 0.0
        self.start_level(1, go_playing=False)

    def show_popup(self, text):
        self.popup_text = text
        self.popup_timer = 3.5

    def check_achievements(self):
        ach = SAVE_DATA["achievements"]
        st = SAVE_DATA["stats"]
        unlocked_now = []

        if st["kills"] >= 30 and not ach["zombie_hunter"]:
            ach["zombie_hunter"] = True
            unlocked_now.append("zombie_hunter")
        if st["bosses_killed"] >= 1 and not ach["boss_slayer"]:
            ach["boss_slayer"] = True
            unlocked_now.append("boss_slayer")
        if st["coins_collected"] >= 15 and not ach["collector"]:
            ach["collector"] = True
            unlocked_now.append("collector")

        for k in unlocked_now:
            rew = ACHIEVEMENTS_INFO[k]["reward"]
            SAVE_DATA["coins"] += rew
            self.show_popup(f"АЧИВКА: {ACHIEVEMENTS_INFO[k]['title']} (+{rew} монет!)")
        if unlocked_now:
            write_save(SAVE_DATA)

    def start_level(self, lvl, go_playing=True):
        self.level = lvl
        self.sun = 100 if lvl != 2 else 50
        self.plants = []
        self.zombies = []
        self.projectiles = []
        self.suns = []
        self.mowers = [LawnMower(r) for r in range(ROWS)]
        self.selected_card = None
        self.shovel_active = False
        self.coins_earned = 0

        # Собираем колоду: сначала обязательные для уровня (выдаются бесплатно!), затем купленные
        mandatory = LEVEL_INFO[lvl]["mandatory"]
        deck = list(mandatory)
        for p_id in SAVE_DATA["unlocked_plants"]:
            if p_id not in deck and len(deck) < 7:
                deck.append(p_id)
        self.active_deck = deck
        self.cooldowns = {p: 0.0 for p in PLANT_CATALOG}

        # На уровне Бассейн сразу ставим 3 стартовые кувшинки на воду
        if lvl == 3:
            self.plants.append(Plant(2, 0, "lilypad", has_lilypad=True))
            self.plants.append(Plant(3, 0, "lilypad", has_lilypad=True))

        self.sky_sun_timer = 4.5
        self.spawn_timer = 5.0
        self.spawned_zombies = 0
        self.total_zombies = 14 + lvl * 4
        self.boss_spawned = False

        if go_playing:
            self.state = "PLAYING"

    def is_water_row(self, row):
        return self.level == 3 and row in (2, 3)

    def remove_plant(self, plant):
        if plant in self.plants:
            # Если на Кувшинке съели растение — остаётся сама Кувшинка
            if plant.has_lilypad and plant.type != "lilypad":
                plant.type = "lilypad"
                plant.max_hp = 100
                plant.hp = 100.0
            else:
                self.plants.remove(plant)

    def explode_mine(self, mine):
        cx = mine.x + 38
        for z in self.zombies:
            if z.row == mine.row and abs((z.x + 30) - cx) <= 95:
                z.hp -= 350
        self.remove_plant(mine)

    def explode_cherry(self, row, col):
        for z in self.zombies:
            if abs(z.row - row) <= 1:
                z_col = (z.x - GRID_X) / CELL_SIZE
                if abs(z_col - col) <= 1.6:
                    z.hp -= 450

    def update_playing(self, dt):
        if self.popup_timer > 0:
            self.popup_timer -= dt

        for k in self.cooldowns:
            if self.cooldowns[k] > 0:
                self.cooldowns[k] = max(0.0, self.cooldowns[k] - dt)

        # Солнышки падают с неба на всех уровнях, кроме Ночи (Уровень 2)
        if self.level != 2:
            self.sky_sun_timer -= dt
            if self.sky_sun_timer <= 0:
                self.sky_sun_timer = random.uniform(6.0, 8.0)
                sx = random.randint(GRID_X + 30, GRID_X + COLS * CELL_SIZE - 40)
                ty = random.randint(GRID_Y + 40, GRID_Y + ROWS * CELL_SIZE - 30)
                self.suns.append(DropItem(sx, GRID_Y - 15, ty, "sun", 25))

        # Спавн волн зомби и Босса в финале
        if self.spawned_zombies < self.total_zombies:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                prog = self.spawned_zombies / max(1, self.total_zombies)
                self.spawn_timer = max(2.4, 6.2 - prog * 3.0)
                row = random.randint(0, ROWS - 1)

                pool = ["normal", "cone"]
                if self.spawned_zombies >= 3:
                    pool += ["bucket", "pole"]
                if self.level >= 2 and self.spawned_zombies >= 5:
                    pool.append("football")
                if self.level >= 3 and self.spawned_zombies >= 4:
                    pool.append("balloon")

                self.zombies.append(Zombie(row, random.choice(pool)))
                self.spawned_zombies += 1

        elif not self.boss_spawned and len(self.zombies) == 0:
            self.boss_spawned = True
            boss_row = 2
            self.zombies.append(Zombie(boss_row, boss_lvl=self.level))
            self.show_popup(f"БОСС УРОВНЯ: {LEVEL_INFO[self.level]['boss_name']}!")

        for p in list(self.plants):
            p.update(dt, self)
        for m in list(self.mowers):
            m.update(dt, self)
        self.mowers = [m for m in self.mowers if m.alive]
        for proj in list(self.projectiles):
            proj.update(dt, self)
        self.projectiles = [pr for pr in self.projectiles if pr.alive]

        # Обновление зомби и выпадение монет
        alive_zombies = []
        for z in self.zombies:
            z.update(dt, self)
            if z.x < GRID_X - 65:
                self.state = "GAMEOVER"
            if z.hp > 0:
                alive_zombies.append(z)
            else:
                SAVE_DATA["stats"]["kills"] += 1
                if z.boss_lvl > 0:
                    SAVE_DATA["stats"]["bosses_killed"] += 1
                    self.suns.append(DropItem(z.x + 25, z.y + 20, z.y + 45, "coin", 25))
                elif random.random() < 0.45:
                    self.suns.append(DropItem(z.x + 20, z.y + 15, z.y + 45, "coin", 10))
                self.check_achievements()
        self.zombies = alive_zombies

        for s in list(self.suns):
            s.update(dt, self)
        self.suns = [s for s in self.suns if s.alive]

        # Проверка победы над Боссом и уровнем
        if self.boss_spawned and len(self.zombies) == 0 and self.state == "PLAYING":
            self.state = "VICTORY"
            reward = 40 * self.level
            SAVE_DATA["coins"] += reward
            self.coins_earned += reward

            if self.level == 1 and not SAVE_DATA["achievements"]["first_blood"]:
                SAVE_DATA["achievements"]["first_blood"] = True
                SAVE_DATA["coins"] += ACHIEVEMENTS_INFO["first_blood"]["reward"]
            if self.level == 4 and not SAVE_DATA["achievements"]["roof_master"]:
                SAVE_DATA["achievements"]["roof_master"] = True
                SAVE_DATA["coins"] += ACHIEVEMENTS_INFO["roof_master"]["reward"]

            if self.level < 4:
                SAVE_DATA["max_level"] = max(SAVE_DATA["max_level"], self.level + 1)
            write_save(SAVE_DATA)

    # -----------------------------------------------------------------
    # ОТРИСОВКА ЭКРАНОВ
    # -----------------------------------------------------------------
    def draw_playing(self, surf):
        bg_colors = {1: (65, 130, 50), 2: (22, 32, 55), 3: (55, 135, 120), 4: (95, 65, 55)}
        surf.fill(bg_colors[self.level])

        # Дом слева
        pygame.draw.rect(surf, (130, 85, 50), (0, GRID_Y - 8, GRID_X - 50, ROWS * CELL_SIZE + 16))
        pygame.draw.rect(surf, (160, 150, 135), (GRID_X - 50, GRID_Y, 50, ROWS * CELL_SIZE))

        # Сетка 5x8
        theme = {1: "day", 2: "night", 3: "day", 4: "roof"}[self.level]
        for r in range(ROWS):
            for c in range(COLS):
                cx, cy = GRID_X + c * CELL_SIZE, GRID_Y + r * CELL_SIZE
                if self.is_water_row(r):
                    surf.blit(TEX["water"], (cx, cy))
                else:
                    parity = (r + c) % 2
                    surf.blit(TEX[f"{theme}_{parity}"], (cx, cy))

        # Верхняя панель
        panel = pygame.Rect(10, 8, WIDTH - 20, 96)
        pygame.draw.rect(surf, (110, 70, 35), panel, border_radius=10)
        pygame.draw.rect(surf, (70, 42, 18), panel, 3, border_radius=10)

              # Окошко Солнышек
        pygame.draw.rect(surf, (235, 220, 175), (18, 16, 78, 80), border_radius=8)
        surf.blit(TEX["sun_icon"], (41, 20))
        s_lbl = font_md.render(str(self.sun), True, (35, 20, 10))
        surf.blit(s_lbl, (57 - s_lbl.get_width() // 2, 62))

        # Карточки растений (Обязательные + Купленные)
        for i, p_id in enumerate(self.active_deck):
            rect = pygame.Rect(104 + i * 78, 16, 72, 80)
            info = PLANT_CATALOG[p_id]
            ready = self.sun >= info["cost"] and self.cooldowns[p_id] <= 0
            bg = (210, 235, 180) if ready else (130, 130, 130)
            if self.selected_card == p_id:
                bg = (255, 245, 120)

            pygame.draw.rect(surf, bg, rect, border_radius=6)
            pygame.draw.rect(surf, (255, 215, 0) if self.selected_card == p_id else (50, 35, 20), rect, 2, border_radius=6)
            surf.blit(TEX[f"{p_id}_icon"], (rect.x + 17, rect.y + 4))

            n_lbl = font_xs.render(info["name"][:9], True, (25, 25, 25))
            surf.blit(n_lbl, (rect.centerx - n_lbl.get_width() // 2, rect.y + 43))
            c_lbl = font_sm.render(str(info["cost"]), True, (20, 60, 15) if ready else (175, 25, 25))
            surf.blit(c_lbl, (rect.centerx - c_lbl.get_width() // 2, rect.y + 59))

            if self.cooldowns[p_id] > 0:
                h_cd = int(80 * (self.cooldowns[p_id] / info["cd"]))
                cd_s = pygame.Surface((72, h_cd), pygame.SRCALPHA)
                cd_s.fill((0, 0, 0, 140))
                surf.blit(cd_s, (rect.x, rect.y))

        # Лопата
        sh_rect = pygame.Rect(660, 18, 64, 76)
        pygame.draw.rect(surf, (255, 185, 110) if self.shovel_active else (195, 175, 140), sh_rect, border_radius=8)
        pygame.draw.rect(surf, (70, 45, 20), sh_rect, 2, border_radius=8)
        surf.blit(TEX["shovel"], (sh_rect.x + 12, sh_rect.y + 10))
        surf.blit(font_xs.render("Лопата", True, (40, 25, 10)), (sh_rect.x + 11, sh_rect.y + 54))

        # Монеты и прогресс уровня
        surf.blit(font_sm.render(f"Монеты: {SAVE_DATA['coins']}", True, (255, 225, 60)), (735, 16))
        surf.blit(font_xs.render(f"Ур.{self.level}: {LEVEL_INFO[self.level]['name']}", True, (230, 230, 230)), (735, 38))
        prog = min(1.0, self.spawned_zombies / max(1, self.total_zombies))
        pygame.draw.rect(surf, (45, 30, 20), (735, 58, 125, 14), border_radius=5)
        pygame.draw.rect(surf, (120, 230, 70), (735, 58, int(125 * prog), 14), border_radius=5)

        menu_btn = pygame.Rect(872, 22, 68, 64)
        pygame.draw.rect(surf, (175, 65, 55), menu_btn, border_radius=8)
        surf.blit(font_sm.render("МЕНЮ", True, (255, 255, 255)), (menu_btn.x + 12, menu_btn.y + 23))

        # Отрисовка всех объектов
        for m in self.mowers: m.draw(surf)
        for p in self.plants: p.draw(surf)
        for z in self.zombies: z.draw(surf)
        for pr in self.projectiles: pr.draw(surf)
        for s in self.suns: s.draw(surf)

        # Полоска здоровья Босса
        boss = next((z for z in self.zombies if z.boss_lvl > 0), None)
        if boss:
            b_ratio = max(0.0, boss.hp / boss.max_hp)
            pygame.draw.rect(surf, (40, 15, 15), (280, 106, 400, 16), border_radius=6)
            pygame.draw.rect(surf, (235, 45, 45), (280, 106, int(400 * b_ratio), 16), border_radius=6)
            b_txt = font_xs.render(f"БОСС: {LEVEL_INFO[self.level]['boss_name']} ({int(boss.hp)} HP)", True, (255, 255, 255))
            surf.blit(b_txt, (480 - b_txt.get_width() // 2, 107))

        if self.popup_timer > 0:
            p_lbl = font_md.render(self.popup_text, True, (255, 245, 100))
            pygame.draw.rect(surf, (30, 30, 30), (WIDTH // 2 - p_lbl.get_width() // 2 - 14, 550, p_lbl.get_width() + 28, 34), border_radius=8)
            surf.blit(p_lbl, (WIDTH // 2 - p_lbl.get_width() // 2, 556))

        return sh_rect, menu_btn

    def handle_playing_click(self, mx, my, button, sh_rect, menu_btn):
        if button == 3:
            self.selected_card = None
            self.shovel_active = False
            return

        for s in reversed(self.suns):
            if not s.collected and math.hypot(mx - s.x, my - s.y) <= 34:
                s.collected = True
                return

        if menu_btn.collidepoint(mx, my):
            self.state = "MENU"
            return

        if sh_rect.collidepoint(mx, my):
            self.shovel_active = not self.shovel_active
            self.selected_card = None
            return

        for i, p_id in enumerate(self.active_deck):
            rect = pygame.Rect(104 + i * 78, 16, 72, 80)
            if rect.collidepoint(mx, my):
                info = PLANT_CATALOG[p_id]
                if self.sun >= info["cost"] and self.cooldowns[p_id] <= 0:
                    self.selected_card = None if self.selected_card == p_id else p_id
                    self.shovel_active = False
                return

        if GRID_X <= mx < GRID_X + COLS * CELL_SIZE and GRID_Y <= my < GRID_Y + ROWS * CELL_SIZE:
            col = (mx - GRID_X) // CELL_SIZE
            row = (my - GRID_Y) // CELL_SIZE
            existing = next((p for p in self.plants if p.row == row and p.col == col), None)

            if self.shovel_active:
                if existing:
                    self.remove_plant(existing)
                self.shovel_active = False
                return

            if not self.selected_card:
                return

            info = PLANT_CATALOG[self.selected_card]
            is_water = self.is_water_row(row)
            can_plant = False
            on_lily = False

            if self.selected_card == "cherry":
                can_plant = True
            elif is_water:
                if self.selected_card == "lilypad" and existing is None:
                    can_plant = True
                    on_lily = True
                elif self.selected_card != "lilypad" and existing and existing.type == "lilypad":
                    can_plant = True
                    on_lily = True
                else:
                    self.show_popup("На воду сначала нужно посадить Кувшинку!")
            else:
                if self.selected_card == "lilypad":
                    self.show_popup("Кувшинку можно сажать только на воду!")
                elif existing is None:
                    can_plant = True

            if can_plant and self.sun >= info["cost"]:
                self.sun -= info["cost"]
                self.cooldowns[self.selected_card] = info["cd"]
                if self.selected_card == "cherry":
                    self.explode_cherry(row, col)
                else:
                    if existing and existing.type == "lilypad":
                        self.plants.remove(existing)
                    self.plants.append(Plant(row, col, self.selected_card, has_lilypad=on_lily))
                self.selected_card = None
    def draw_menu(self, surf):
        surf.fill((45, 115, 175))
        pygame.draw.rect(surf, (65, 145, 50), (0, 430, WIDTH, 170))

        title = font_xl.render("PLANTS vs. ZOMBIES: ULTIMATE", True, (130, 250, 80))
        surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 32))

        c_box = pygame.Rect(WIDTH // 2 - 140, 90, 280, 38)
        pygame.draw.rect(surf, (40, 60, 85), c_box, border_radius=8)
        c_lbl = font_md.render(f"Ваши Монеты: {SAVE_DATA['coins']}", True, (255, 220, 50))
        surf.blit(c_lbl, (c_box.centerx - c_lbl.get_width() // 2, c_box.y + 8))

        buttons = []
        for lvl in range(1, 5):
            r = pygame.Rect(160 + (lvl - 1) * 165, 155, 150, 120)
            unlocked = lvl <= SAVE_DATA["max_level"]
            col = (75, 175, 60) if unlocked else (110, 115, 125)
            pygame.draw.rect(surf, col, r, border_radius=12)
            pygame.draw.rect(surf, (255, 255, 255), r, 2, border_radius=12)

            l1 = font_md.render(f"Уровень {lvl}", True, (255, 255, 255))
            l2 = font_sm.render(LEVEL_INFO[lvl]["name"], True, (255, 240, 150))
            req_p = PLANT_CATALOG[LEVEL_INFO[lvl]["mandatory"][1]]["name"]
            l3 = font_xs.render(f"Выдаётся: {req_p}", True, (220, 245, 220))
            status = font_xs.render("ОТКРЫТО" if unlocked else "ЗАКРЫТО", True, (180, 255, 180) if unlocked else (255, 170, 170))

            surf.blit(l1, (r.centerx - l1.get_width() // 2, r.y + 14))
            surf.blit(l2, (r.centerx - l2.get_width() // 2, r.y + 42))
            surf.blit(l3, (r.centerx - l3.get_width() // 2, r.y + 68))
            surf.blit(status, (r.centerx - status.get_width() // 2, r.y + 94))
            buttons.append((r, ("LVL", lvl)))

        b_shop = pygame.Rect(210, 310, 250, 58)
        b_ach = pygame.Rect(500, 310, 250, 58)
        b_reset = pygame.Rect(210, 385, 250, 46)
        b_exit = pygame.Rect(500, 385, 250, 46)

        for rect, txt, col, act in [
            (b_shop, "МАГАЗИН РАСТЕНИЙ", (215, 140, 35), ("STATE", "SHOP")),
            (b_ach, "ДОСТИЖЕНИЯ (АЧИВКИ)", (90, 130, 205), ("STATE", "ACHIV")),
            (b_reset, "Сбросить сохранения (0 монет)", (140, 85, 85), ("RESET", None)),
            (b_exit, "ВЫХОД ИЗ ИГРЫ", (175, 60, 60), ("EXIT", None)),
        ]:
            pygame.draw.rect(surf, col, rect, border_radius=10)
            pygame.draw.rect(surf, (255, 255, 255), rect, 2, border_radius=10)
            lbl = font_sm.render(txt, True, (255, 255, 255))
            surf.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))
            buttons.append((rect, act))

        return buttons

    def draw_shop(self, surf):
        surf.fill((40, 75, 105))
        t = font_lg.render("МАГАЗИН РАСТЕНИЙ", True, (255, 240, 120))
        surf.blit(t, (WIDTH // 2 - t.get_width() // 2, 24))
        c_lbl = font_md.render(f"Ваши Монеты: {SAVE_DATA['coins']}", True, (255, 220, 50))
        surf.blit(c_lbl, (720, 28))

        shop_items = [k for k, v in PLANT_CATALOG.items() if v["shop"] > 0]
        rects = []
        for i, p_id in enumerate(shop_items):
            info = PLANT_CATALOG[p_id]
            r = pygame.Rect(130, 85 + i * 82, 700, 70)
            owned = p_id in SAVE_DATA["unlocked_plants"]
            can_buy = SAVE_DATA["coins"] >= info["shop"] and not owned
            col = (65, 145, 65) if owned else ((85, 130, 175) if can_buy else (95, 95, 105))

            pygame.draw.rect(surf, col, r, border_radius=10)
            pygame.draw.rect(surf, (255, 255, 255), r, 2, border_radius=10)
            surf.blit(TEX[f"{p_id}_icon"], (r.x + 18, r.y + 15))

            title = font_md.render(f"{info['name']} — {info['desc']}", True, (255, 255, 255))
            surf.blit(title, (r.x + 75, r.y + 14))
            sub = font_sm.render(f"Стоимость на поле: {info['cost']} солнц", True, (220, 235, 250))
            surf.blit(sub, (r.x + 75, r.y + 40))

            st_txt = "КУПЛЕНО" if owned else f"КУПИТЬ ({info['shop']} монет)"
            st_lbl = font_md.render(st_txt, True, (255, 240, 110) if not owned else (190, 255, 190))
            surf.blit(st_lbl, (r.right - st_lbl.get_width() - 22, r.y + 24))
            rects.append((r, p_id))

        back = pygame.Rect(40, 525, 150, 48)
        pygame.draw.rect(surf, (180, 65, 65), back, border_radius=8)
        surf.blit(font_md.render("НАЗАД", True, (255, 255, 255)), (back.x + 42, back.y + 13))
        return rects, back

    def draw_achiv(self, surf):
        surf.fill((50, 55, 90))
        t = font_lg.render("ДОСТИЖЕНИЯ (АЧИВКИ)", True, (255, 240, 120))
        surf.blit(t, (WIDTH // 2 - t.get_width() // 2, 24))

        st = SAVE_DATA["stats"]
        stat_lbl = font_sm.render(
            f"Статистика: Убито зомби: {st['kills']} | Побеждено боссов: {st['bosses_killed']} | Собрано монет: {st['coins_collected']}",
            True, (210, 225, 255)
        )
        surf.blit(stat_lbl, (WIDTH // 2 - stat_lbl.get_width() // 2, 62))

        for i, (k, info) in enumerate(ACHIEVEMENTS_INFO.items()):
            r = pygame.Rect(120, 100 + i * 78, 720, 66)
            done = SAVE_DATA["achievements"].get(k, False)
            pygame.draw.rect(surf, (60, 140, 75) if done else (85, 85, 105), r, border_radius=10)
            pygame.draw.rect(surf, (255, 255, 255), r, 2, border_radius=10)

            t1 = font_md.render(f"{info['title']} (+{info['reward']} монет)", True, (255, 245, 130) if done else (255, 255, 255))
            t2 = font_sm.render(info["desc"], True, (230, 230, 230))
            st_lbl = font_md.render("ВЫПОЛНЕНО" if done else "В ПРОЦЕССЕ", True, (180, 255, 180) if done else (255, 180, 180))

            surf.blit(t1, (r.x + 20, r.y + 10))
            surf.blit(t2, (r.x + 20, r.y + 36))
            surf.blit(st_lbl, (r.right - st_lbl.get_width() - 20, r.y + 22))

        back = pygame.Rect(40, 525, 150, 48)
        pygame.draw.rect(surf, (180, 65, 65), back, border_radius=8)
        surf.blit(font_md.render("НАЗАД", True, (255, 255, 255)), (back.x + 42, back.y + 13))
        return back


# =====================================================================
# 6. ГЛАВНЫЙ ЦИКЛ ПРОГРАММЫ
# =====================================================================
def main():
    game = PvZUltimateGame()
    sh_rect = menu_btn = pygame.Rect(0, 0, 0, 0)

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                if game.state == "MENU":
                    for r, (act, val) in game.draw_menu(screen):
                        if r.collidepoint(mx, my):
                            if act == "LVL" and val <= SAVE_DATA["max_level"]:
                                game.start_level(val, go_playing=True)
                            elif act == "STATE":
                                game.state = val
                            elif act == "RESET":
                                SAVE_DATA.clear()
                                SAVE_DATA.update(get_default_save())
                                write_save(SAVE_DATA)
                            elif act == "EXIT":
                                pygame.quit()
                                sys.exit()

                elif game.state == "SHOP":
                    rects, back = game.draw_shop(screen)
                    if back.collidepoint(mx, my):
                        game.state = "MENU"
                    for r, p_id in rects:
                        if r.collidepoint(mx, my):
                            cost = PLANT_CATALOG[p_id]["shop"]
                            if p_id not in SAVE_DATA["unlocked_plants"] and SAVE_DATA["coins"] >= cost:
                                SAVE_DATA["coins"] -= cost
                                SAVE_DATA["unlocked_plants"].append(p_id)
                                write_save(SAVE_DATA)

                elif game.state == "ACHIV":
                    back = game.draw_achiv(screen)
                    if back.collidepoint(mx, my):
                        game.state = "MENU"

                elif game.state == "PLAYING":
                    game.handle_playing_click(mx, my, event.button, sh_rect, menu_btn)

                elif game.state in ("VICTORY", "GAMEOVER"):
                    if pygame.Rect(WIDTH // 2 - 120, 360, 240, 54).collidepoint(mx, my):
                        game.state = "MENU"

        if game.state == "MENU":
            game.draw_menu(screen)
        elif game.state == "SHOP":
            game.draw_shop(screen)
        elif game.state == "ACHIV":
            game.draw_achiv(screen)
        elif game.state in ("PLAYING", "VICTORY", "GAMEOVER"):
            if game.state == "PLAYING":
                game.update_playing(dt)
            sh_rect, menu_btn = game.draw_playing(screen)

            if game.state in ("VICTORY", "GAMEOVER"):
                ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 175))
                screen.blit(ov, (0, 0))

                win = game.state == "VICTORY"
                t_txt = f"УРОВЕНЬ {game.level} ПРОЙДЕН!" if win else "МОЗГИ СЪЕДЕНЫ! ПОРАЖЕНИЕ"
                t_lbl = font_lg.render(t_txt, True, (110, 255, 95) if win else (255, 80, 80))
                screen.blit(t_lbl, (WIDTH // 2 - t_lbl.get_width() // 2, 210))

                c_lbl = font_md.render(f"Заработано за бой: +{game.coins_earned} монет (Всего: {SAVE_DATA['coins']})", True, (255, 225, 60))
                screen.blit(c_lbl, (WIDTH // 2 - c_lbl.get_width() // 2, 275))

                b_back = pygame.Rect(WIDTH // 2 - 120, 360, 240, 54)
                pygame.draw.rect(screen, (75, 165, 60), b_back, border_radius=10)
                pygame.draw.rect(screen, (255, 255, 255), b_back, 2, border_radius=10)
                surf_b = font_md.render("В ГЛАВНОЕ МЕНЮ", True, (255, 255, 255))
                screen.blit(surf_b, (b_back.centerx - surf_b.get_width() // 2, b_back.centery - surf_b.get_height() // 2))

        pygame.display.flip()


if __name__ == "__main__":
    main()
