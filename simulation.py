import pygame
import random
import math

# 1. 환경 설정
WIDTH, HEIGHT = 1000, 800
FPS = 60
SAFE_ZONE_POS = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
SAFE_ZONE_RADIUS = 130

# 색상
COLOR_BG = (30, 30, 30)
COLOR_PREY = (46, 204, 113)
COLOR_PREDATOR = (231, 76, 60)
COLOR_SAFE = (52, 152, 219)
COLOR_UI = (220, 220, 220)
COLOR_PERCEPTION = (241, 196, 15) # 노란색 (인식 범위용)

# 2. 유전자(DNA) 클래스
class DNA:
    def __init__(self, size=None, speed=None, perception=None):
        self.size = size if size else random.uniform(5, 15)
        self.speed = speed if speed else random.uniform(2, 5)
        self.perception = perception if perception else random.uniform(50, 150)

    def mutate(self):
        rate = 0.1
        if random.random() < rate:
            self.size = max(3, self.size + random.uniform(-2, 2))
            self.speed = max(1, self.speed + random.uniform(-0.5, 0.5))
            self.perception = max(20, self.perception + random.uniform(-10, 10))

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
        if self.pos.x < 0 or self.pos.x > WIDTH: self.vel.x *= -1
        if self.pos.y < 0 or self.pos.y > HEIGHT: self.vel.y *= -1

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), int(self.dna.size))

class Herbivore(Agent):
    def __init__(self, x, y, dna):
        super().__init__(x, y, dna, COLOR_PREY)
        self.health = 100.0

    def update(self):
        self.move()
        self.age += 1
        self.health -= (0.05 + (self.dna.speed * 0.02))
        if self.health <= 0: self.alive = False

    def is_in_safe_zone(self):
        return self.pos.distance_to(SAFE_ZONE_POS) < SAFE_ZONE_RADIUS

class Predator(Agent):
    def __init__(self, x, y, dna):
        super().__init__(x, y, dna, COLOR_PREDATOR)
        self.hunger = 100.0

    def update(self):
        self.move()
        self.age += 1
        self.hunger -= (0.05 + (self.dna.size * 0.01) + (self.dna.speed * 0.05))
        if self.hunger <= 0: self.alive = False

    def eat(self):
        self.hunger = min(100, self.hunger + 60)

# 4. UI 및 그래프 함수
def draw_ui(screen, history, font, selected_agent):
    # (1) 개체 정보창 (좌측 상단)
    if selected_agent:
        pygame.draw.circle(screen, (255, 255, 255), (int(selected_agent.pos.x), int(selected_agent.pos.y)), int(selected_agent.dna.size)+7, 1)
        info_y = 20
        txts = [
            f"Type: {'Prey' if isinstance(selected_agent, Herbivore) else 'Predator'}",
            f"Size: {selected_agent.dna.size:.2f}",
            f"Speed: {selected_agent.dna.speed:.2f}",
            f"Perception: {selected_agent.dna.perception:.2f}"
        ]
        for t in txts:
            screen.blit(font.render(t, True, COLOR_UI), (20, info_y))
            info_y += 25

    # (2) 통계 그래프 및 수치 (우측 상단)
    start_x, start_y = WIDTH - 220, 180
    pygame.draw.rect(screen, (40, 40, 40), (start_x - 10, start_y - 160, 210, 200))
    
    # 마지막 데이터 수치 표시
    if history["size"]:
        s_val = history["size"][-1]
        v_val = history["speed"][-1]
        p_val = history["perception"][-1]
        screen.blit(font.render(f"Avg Size: {s_val:.1f}", True, (255, 255, 255)), (start_x, start_y + 10))
        screen.blit(font.render(f"Avg Speed: {v_val:.1f}", True, COLOR_PREY), (start_x, start_y + 30))
        screen.blit(font.render(f"Avg Perception: {p_val:.1f}", True, COLOR_PERCEPTION), (start_x, start_y + 50))

    # 그래프 선 그리기
    if len(history["size"]) > 1:
        for i in range(1, len(history["size"])):
            # Size (White)
            pygame.draw.line(screen, (255, 255, 255), 
                             (start_x + (i-1)*4, start_y - history["size"][i-1]*5),
                             (start_x + i*4, start_y - history["size"][i]*5), 2)
            # Speed (Green)
            pygame.draw.line(screen, COLOR_PREY, 
                             (start_x + (i-1)*4, start_y - history["speed"][i-1]*20),
                             (start_x + i*4, start_y - history["speed"][i]*20), 2)
            # Perception (Yellow) - 스케일 조정 (/2)
            pygame.draw.line(screen, COLOR_PERCEPTION, 
                             (start_x + (i-1)*4, start_y - history["perception"][i-1]*1.2),
                             (start_x + i*4, start_y - history["perception"][i]*1.2), 2)

# 5. 메인 루프
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Evolution Simulator: Data Visualization")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 16)

    herbivores = [Herbivore(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()) for _ in range(100)]
    predators = [Predator(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()) for _ in range(6)]
    
    stats_history = {"size": [], "speed": [], "perception": []}
    selected_agent = None
    frame_count = 0

    running = True
    while running:
        screen.fill(COLOR_BG)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                selected_agent = None
                for a in herbivores + predators:
                    if a.pos.distance_to(mouse_pos) < a.dna.size + 15:
                        selected_agent = a
                        break

        # 안전지대
        pygame.draw.circle(screen, (40, 60, 100), (int(SAFE_ZONE_POS.x), int(SAFE_ZONE_POS.y)), SAFE_ZONE_RADIUS)
        pygame.draw.circle(screen, COLOR_SAFE, (int(SAFE_ZONE_POS.x), int(SAFE_ZONE_POS.y)), SAFE_ZONE_RADIUS, 2)

        # 초식동물
        for h in herbivores[:]:
            h.update()
            if not h.alive:
                if selected_agent == h: selected_agent = None
                herbivores.remove(h)
                continue
            h.draw(screen)
            if h.health > 80 and random.random() < 0.01:
                h.health -= 50
                new_dna = DNA(h.dna.size, h.dna.speed, h.dna.perception)
                new_dna.mutate()
                herbivores.append(Herbivore(h.pos.x, h.pos.y, new_dna))

        # 포식자
        for p in predators[:]:
            p.update()
            if not p.alive:
                if selected_agent == p: selected_agent = None
                predators.remove(p)
                continue
            p.draw(screen)
            for h in herbivores[:]:
                if not h.is_in_safe_zone() and p.pos.distance_to(h.pos) < (p.dna.size + h.dna.size):
                    herbivores.remove(h)
                    p.eat()
            if p.hunger > 85 and random.random() < 0.007:
                p.hunger -= 60
                new_dna = DNA(p.dna.size, p.dna.speed, p.dna.perception)
                new_dna.mutate()
                predators.append(Predator(p.pos.x, p.pos.y, new_dna))

        # 최소 수 유지
        if len(herbivores) < 5: herbivores.append(Herbivore(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()))
        if len(predators) < 3: predators.append(Predator(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()))

        # 통계 수집
        frame_count += 1
        if frame_count % 120 == 0 and herbivores:
            stats_history["size"].append(sum(h.dna.size for h in herbivores) / len(herbivores))
            stats_history["speed"].append(sum(h.dna.speed for h in herbivores) / len(herbivores))
            stats_history["perception"].append(sum(h.dna.perception for h in herbivores) / len(herbivores))
            if len(stats_history["size"]) > 50:
                for key in stats_history: stats_history[key].pop(0)

        # UI 출력
        draw_ui(screen, stats_history, font, selected_agent)

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__":
    main()