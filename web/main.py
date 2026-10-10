import asyncio
import pygame
import random
import math

# 1. 환경 설정
WIDTH, HEIGHT = 1000, 800
FPS = 60
SAFE_ZONE_POS = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
SAFE_ZONE_RADIUS = 120

# 수용 한계: 개체 수가 이 값에 가까워질수록 번식 확률이 0에 수렴
HERBIVORE_CAPACITY = 300
PREDATOR_CAPACITY = 40

# 통계 기록 (60프레임 = 약 1초마다, 최근 300개 = 약 5분)
STATS_INTERVAL = 60
STATS_MAX_LEN = 300

# 색상
COLOR_BG = (30, 30, 30)
COLOR_PREY = (46, 204, 113)
COLOR_PREDATOR = (231, 76, 60)
COLOR_SAFE = (52, 152, 219)
COLOR_UI = (220, 220, 220)
COLOR_PANEL = (45, 45, 45)

# 2. 유전자(DNA) 클래스
class DNA:
    # 유전자별 (최소, 최대) 범위 - 음수나 비정상 값으로 변이하는 것을 막음
    LIMITS = {"size": (3, 25), "speed": (1, 8), "perception": (20, 250)}

    def __init__(self, size=None, speed=None, perception=None):
        self.size = size if size is not None else random.uniform(5, 15)
        self.speed = speed if speed is not None else random.uniform(2, 5)
        self.perception = perception if perception is not None else random.uniform(50, 150)

    def copy(self):
        return DNA(self.size, self.speed, self.perception)

    def mutate(self, rate=0.1):
        if random.random() < rate:
            self.size = self._clamp("size", self.size + random.uniform(-2, 2))
            self.speed = self._clamp("speed", self.speed + random.uniform(-0.5, 0.5))
            self.perception = self._clamp("perception", self.perception + random.uniform(-10, 10))

    @classmethod
    def _clamp(cls, gene, value):
        lo, hi = cls.LIMITS[gene]
        return max(lo, min(hi, value))

# 3. 기본 개체 클래스
class Agent:
    def __init__(self, x, y, dna, color):
        self.pos = pygame.Vector2(x, y)
        angle = random.uniform(0, 2 * math.pi)
        self.vel = pygame.Vector2(math.cos(angle), math.sin(angle))
        self.dna = dna
        self.color = color
        self.age = 0
        self.alive = True

    def move(self):
        self.pos += self.vel * self.dna.speed
        # 벽에 닿으면 화면 안으로 되돌린 뒤 안쪽 방향으로 튕김 (벽 밖에 갇히는 현상 방지)
        if self.pos.x < 0:
            self.pos.x, self.vel.x = 0, abs(self.vel.x)
        elif self.pos.x > WIDTH:
            self.pos.x, self.vel.x = WIDTH, -abs(self.vel.x)
        if self.pos.y < 0:
            self.pos.y, self.vel.y = 0, abs(self.vel.y)
        elif self.pos.y > HEIGHT:
            self.pos.y, self.vel.y = HEIGHT, -abs(self.vel.y)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), int(self.dna.size))

class Herbivore(Agent):
    def __init__(self, x, y, dna):
        super().__init__(x, y, dna, COLOR_PREY)
        self.health = 100.0

    def update(self):
        self.move()
        self.age += 1
        # 빠를수록 체력이 빨리 닳음
        self.health -= 0.1 + (self.dna.speed * 0.05)
        if self.health <= 0: self.alive = False

    def try_reproduce(self, population):
        # 일정 나이 이상이면 낮은 확률로 번식 (개체가 많을수록 확률 감소)
        crowding = max(0.0, 1 - population / HERBIVORE_CAPACITY)
        if self.age > 200 and random.random() < 0.01 * crowding:
            self.health -= 30
            child_dna = self.dna.copy()
            child_dna.mutate()
            return Herbivore(self.pos.x, self.pos.y, child_dna)
        return None

    def is_in_safe_zone(self):
        return self.pos.distance_to(SAFE_ZONE_POS) < SAFE_ZONE_RADIUS

class Predator(Agent):
    def __init__(self, x, y, dna):
        super().__init__(x, y, dna, COLOR_PREDATOR)
        self.hunger = 100.0

    def update(self):
        self.move()
        self.age += 1
        # 크고 빠를수록 빨리 배고파짐
        self.hunger -= 0.05 + (self.dna.size * 0.01) + (self.dna.speed * 0.05)
        if self.hunger <= 0: self.alive = False

    def eat(self):
        self.hunger = min(100, self.hunger + 60)

    def try_reproduce(self, population):
        crowding = max(0.0, 1 - population / PREDATOR_CAPACITY)
        if self.hunger > 70 and random.random() < 0.005 * crowding:
            self.hunger -= 40
            child_dna = self.dna.copy()
            child_dna.mutate()
            return Predator(self.pos.x, self.pos.y, child_dna)
        return None

# 4. 통계
def average_genes(agents):
    if not agents:
        return 0, 0, 0
    n = len(agents)
    return (sum(a.dna.size for a in agents) / n,
            sum(a.dna.speed for a in agents) / n,
            sum(a.dna.perception for a in agents) / n)

def record_stats(history, herbivores, predators):
    h_size, h_speed, _ = average_genes(herbivores)
    p_size, p_speed, _ = average_genes(predators)
    values = {"h_count": len(herbivores), "p_count": len(predators),
              "h_size": h_size, "p_size": p_size,
              "h_speed": h_speed, "p_speed": p_speed}
    for key, val in values.items():
        history[key].append(val)
        if len(history[key]) > STATS_MAX_LEN:
            history[key].pop(0)

# 5. UI 및 그래프 함수
FONT_PATH = "NanumGothic-Regular.ttf"  # main.py와 같은 폴더에 둠

def load_font(size):
    # 브라우저에는 시스템 한글 폰트가 없으므로 함께 배포한 나눔고딕 사용
    return pygame.font.Font(FONT_PATH, size)

def draw_text(screen, font, text, pos, color=COLOR_UI):
    screen.blit(font.render(text, True, color), pos)

def draw_line_graph(screen, data, color, rect, max_val):
    if len(data) < 2: return
    x0, y0, w, h = rect
    step = w / (STATS_MAX_LEN - 1)
    points = [(x0 + i * step, y0 + h - (min(val, max_val) / max_val) * h) for i, val in enumerate(data)]
    pygame.draw.lines(screen, color, False, points, 2)

def draw_graph_panel(screen, font, title, rect, series, max_val):
    pygame.draw.rect(screen, COLOR_PANEL, rect)
    pygame.draw.rect(screen, COLOR_UI, rect, 1)
    draw_text(screen, font, f"{title} (최대 {max_val})", (rect[0], rect[1] - 20))
    for data, color in series:
        draw_line_graph(screen, data, color, rect, max_val)

def draw_ui(screen, font, herbivores, predators, history, selected_agent):
    # (1) 현재 통계 (좌측 상단)
    y = 10
    for label, agents, color in (("초식동물", herbivores, COLOR_PREY), ("포식자", predators, COLOR_PREDATOR)):
        size, speed, perc = average_genes(agents)
        draw_text(screen, font, f"{label} 수: {len(agents)}", (10, y), color)
        draw_text(screen, font, f"평균 크기 {size:.2f} / 속도 {speed:.2f} / 인식 {perc:.1f}", (20, y + 20), color)
        y += 50

    # (2) 선택한 개체 정보 (우측 상단)
    if selected_agent:
        pygame.draw.circle(screen, (255, 255, 255), (int(selected_agent.pos.x), int(selected_agent.pos.y)), int(selected_agent.dna.size) + 7, 1)
        is_prey = isinstance(selected_agent, Herbivore)
        energy = f"체력: {selected_agent.health:.1f}" if is_prey else f"포만감: {selected_agent.hunger:.1f}"
        txts = [
            f"종류: {'초식동물' if is_prey else '포식자'}",
            f"크기: {selected_agent.dna.size:.2f}",
            f"속도: {selected_agent.dna.speed:.2f}",
            f"인식: {selected_agent.dna.perception:.2f}",
            f"나이: {selected_agent.age}",
            energy,
        ]
        info_x, info_y = WIDTH - 170, 10
        pygame.draw.rect(screen, COLOR_PANEL, (info_x - 10, info_y - 5, 170, len(txts) * 22 + 10))
        for t in txts:
            draw_text(screen, font, t, (info_x, info_y))
            info_y += 22

    # (3) 추세 그래프 (하단, 초록: 초식동물 / 빨강: 포식자)
    g_w, g_h, gap = 300, 100, 20
    g_y = HEIGHT - g_h - 10
    panels = [
        ("개체 수", "count", HERBIVORE_CAPACITY),
        ("평균 크기", "size", 20),
        ("평균 속도", "speed", 8),
    ]
    for i, (title, key, max_val) in enumerate(panels):
        rect = (10 + i * (g_w + gap), g_y, g_w, g_h)
        draw_graph_panel(screen, font, title, rect,
                         [(history[f"h_{key}"], COLOR_PREY), (history[f"p_{key}"], COLOR_PREDATOR)], max_val)

# 6. 메인 루프
async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("진화 시뮬레이션")
    clock = pygame.time.Clock()
    font = load_font(15)

    herbivores = [Herbivore(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()) for _ in range(30)]
    predators = [Predator(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()) for _ in range(5)]

    stats_history = {k: [] for k in ("h_count", "p_count", "h_size", "p_size", "h_speed", "p_speed")}
    selected_agent = None
    frame_count = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                selected_agent = None
                for a in herbivores + predators:
                    if a.pos.distance_to(mouse_pos) < a.dna.size + 15:
                        selected_agent = a
                        break

        # 초식동물: 이동, 사망, 번식
        newborns = []
        for h in herbivores:
            h.update()
            if h.alive:
                child = h.try_reproduce(len(herbivores) + len(newborns))
                if child: newborns.append(child)
        herbivores = [h for h in herbivores if h.alive] + newborns

        # 포식자: 이동, 사망, 사냥, 번식
        newborns = []
        for p in predators:
            p.update()
            if not p.alive: continue
            for h in herbivores:
                if h.alive and not h.is_in_safe_zone() and p.pos.distance_to(h.pos) < (p.dna.size + h.dna.size):
                    h.alive = False
                    p.eat()
            child = p.try_reproduce(len(predators) + len(newborns))
            if child: newborns.append(child)
        predators = [p for p in predators if p.alive] + newborns
        herbivores = [h for h in herbivores if h.alive]

        # 죽거나 잡아먹힌 개체는 선택 해제
        if selected_agent and not selected_agent.alive:
            selected_agent = None

        # 최소 수 유지 (완전 멸종 방지)
        if len(herbivores) < 5: herbivores.append(Herbivore(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()))
        if len(predators) < 3: predators.append(Predator(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()))

        # 통계 수집
        frame_count += 1
        if frame_count % STATS_INTERVAL == 0:
            record_stats(stats_history, herbivores, predators)

        # 그리기
        screen.fill(COLOR_BG)
        pygame.draw.circle(screen, (40, 60, 100), (int(SAFE_ZONE_POS.x), int(SAFE_ZONE_POS.y)), SAFE_ZONE_RADIUS)
        pygame.draw.circle(screen, COLOR_SAFE, (int(SAFE_ZONE_POS.x), int(SAFE_ZONE_POS.y)), SAFE_ZONE_RADIUS, 2)
        for a in herbivores + predators:
            a.draw(screen)
        draw_ui(screen, font, herbivores, predators, stats_history, selected_agent)

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)  # 브라우저에 제어권 반환
    pygame.quit()

asyncio.run(main())
