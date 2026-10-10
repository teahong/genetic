import pygame
import random
import math

# 기본 설정
WIDTH, HEIGHT = 1000, 800
FPS = 60

# 색상 정의
WHITE = (255, 255, 255)
GREEN = (46, 204, 113)  # 초식동물
RED = (231, 76, 60)     # 포식자
BLUE = (52, 152, 219)   # 안전지대

class DNA:
    def __init__(self, size=None, speed=None, perception=None):
        # 유전자가 없으면 랜덤 생성 (초기 세대)
        self.size = size if size else random.uniform(5, 15)
        self.speed = speed if speed else random.uniform(2, 5)
        self.perception = perception if perception else random.uniform(50, 150)

    def mutate(self, rate=0.1):
        """드문 확률로 돌연변이 발생"""
        if random.random() < rate:
            self.size += random.uniform(-2, 2)
            self.speed += random.uniform(-0.5, 0.5)
            self.perception += random.uniform(-10, 10)

# Pygame 초기화 및 창 생성
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("유전 알고리즘 진화 시뮬레이션")
clock = pygame.time.Clock()

class Agent:
    def __init__(self, x, y, dna, color):
        self.pos = pygame.Vector2(x, y)
        # 무작위 방향으로 시작
        self.vel = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.dna = dna
        self.color = color
        self.health = 100.0  # 포식자는 배고픔, 초식동물은 수명으로 활용
        self.age = 0         # 생존 시간

    def move(self):
        """유전된 속도에 따라 이동하고 벽에 부딪히면 튕김"""
        self.pos += self.vel * self.dna.speed

        # 화면 경계 처리
        if self.pos.x < 0 or self.pos.x > WIDTH:
            self.vel.x *= -1
        if self.pos.y < 0 or self.pos.y > HEIGHT:
            self.vel.y *= -1

    def draw(self, surface):
        """유전된 크기에 따라 화면에 그림"""
        # 인식 범위(Perception) 시각화 (선택 사항: 디버깅용)
        # pygame.draw.circle(surface, (200, 200, 200), (int(self.pos.x), int(self.pos.y)), int(self.dna.perception), 1)
        
        # 실제 개체 그리기
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), int(self.dna.size))

# 안전지대 설정 (가운데 원)
SAFE_ZONE_POS = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
SAFE_ZONE_RADIUS = 120

class Herbivore(Agent):
    def __init__(self, x, y, dna):
        super().__init__(x, y, dna, GREEN)
        
    def update(self):
        self.move()
        self.age += 1
        # 수명 시스템: 시간에 따라 체력 감소 (속도가 빠를수록 빨리 감소)
        self.health -= 0.1 + (self.dna.speed * 0.05)
        
    def is_safe(self):
        """중앙 안전지대에 있는지 확인"""
        dist = self.pos.distance_to(SAFE_ZONE_POS)
        return dist < SAFE_ZONE_RADIUS

class Predator(Agent):
    def __init__(self, x, y, dna):
        super().__init__(x, y, dna, RED)
        self.hunger = 100.0  # 포식자는 굶주림 지표 사용
        
    def update(self):
        self.move()
        self.age += 1
        # 굶주림: 시간에 따라 배고파짐 (크고 빠를수록 에너지 소모가 큼)
        self.hunger -= 0.05 + (self.dna.size * 0.01) + (self.dna.speed * 0.05)

    def eat(self):
        """초식동물을 잡아먹었을 때 허기 회복"""
        self.hunger = min(100, self.hunger + 60)

# 안전지대 시각화 함수
def draw_safe_zone(surface):
    # 투명한 원을 그리기 위해 별도의 surface 활용 가능하지만, 여기선 단순 원으로 표시
    pygame.draw.circle(surface, BLUE, (int(SAFE_ZONE_POS.x), int(SAFE_ZONE_POS.y)), SAFE_ZONE_RADIUS, 2)

def simulate():
    # 초기 개체 생성
    herbivores = [Herbivore(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()) for _ in range(20)]
    predators = [Predator(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()) for _ in range(5)]

    running = True
    while running:
        screen.fill((30, 30, 30))  # 배경색 (어두운 회색)
        
        # 1. 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. 안전지대 그리기
        draw_safe_zone(screen)

        # 3. 초식동물 업데이트 및 번식
        for h in herbivores[:]:
            h.update()
            h.draw(screen)
            
            # 수명 다함
            if h.health <= 0:
                herbivores.remove(h)
                continue
            
            # 번식 (일정 시간 생존 시 낮은 확률로 자식 생성)
            if h.age > 200 and random.random() < 0.01:
                child_dna = DNA(h.dna.size, h.dna.speed, h.dna.perception)
                child_dna.mutate() # 돌연변이 발생
                herbivores.append(Herbivore(h.pos.x, h.pos.y, child_dna))
                h.health -= 30 # 번식 에너지 소모

        # 4. 포식자 업데이트 및 사냥
        for p in predators[:]:
            p.update()
            p.draw(screen)

            if p.hunger <= 0:
                predators.remove(p)
                continue

            # 사냥 로직
            for h in herbivores[:]:
                if not h.is_safe(): # 안전지대 밖의 초식동물만 사냥 가능
                    dist = p.pos.distance_to(h.pos)
                    if dist < (p.dna.size + h.dna.size):
                        herbivores.remove(h)
                        p.eat()

            # 포식자 번식
            if p.hunger > 70 and random.random() < 0.005:
                child_dna = DNA(p.dna.size, p.dna.speed, p.dna.perception)
                child_dna.mutate()
                predators.append(Predator(p.pos.x, p.pos.y, child_dna))
                p.hunger -= 40

        # 개체 수 유지 (완전 멸종 방지용 - 선택 사항)
        if len(herbivores) < 5:
            herbivores.append(Herbivore(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()))
        if len(predators) < 3: # 포식자가 3마리 미만으로 떨어지면 새로 추가
            predators.append(Predator(random.randint(0, WIDTH), random.randint(0, HEIGHT), DNA()))

        # --- 통계 계산 ---
        h_count = len(herbivores)
        p_count = len(predators)

        # 1000마리 초과 시 종료
        if h_count > 1000 or p_count > 1000:
            print("개체 수가 1000을 초과하여 시뮬레이션을 종료합니다.")
            running = False

        # 평균 속성 계산
        def get_avg_stats(agents):
            if not agents:
                return 0, 0, 0
            avg_size = sum(a.dna.size for a in agents) / len(agents)
            avg_speed = sum(a.dna.speed for a in agents) / len(agents)
            avg_perc = sum(a.dna.perception for a in agents) / len(agents)
            return avg_size, avg_speed, avg_perc

        h_size, h_speed, h_perc = get_avg_stats(herbivores)
        p_size, p_speed, p_perc = get_avg_stats(predators)

        # --- 통계 표시 (한국어) ---
        # 폰트 설정 (Windows 기본 한글 폰트)
        try:
            font = pygame.font.SysFont("malgungothic", 15)
        except:
            font = pygame.font.SysFont("arial", 15) # fallback

        def draw_text(text, x, y, color):
            img = font.render(text, True, color)
            screen.blit(img, (x, y))

        # 왼쪽 상단: 수치 표시
        draw_text(f"초식동물 수: {h_count}", 10, 10, GREEN)
        draw_text(f"평균 크기: {h_size:.2f}", 20, 30, GREEN)
        draw_text(f"평균 속도: {h_speed:.2f}", 20, 50, GREEN)
        draw_text(f"평균 인식: {h_perc:.2f}", 20, 70, GREEN)

        draw_text(f"포식자 수: {p_count}", 10, 100, RED)
        draw_text(f"평균 크기: {p_size:.2f}", 20, 120, RED)
        draw_text(f"평균 속도: {p_speed:.2f}", 20, 140, RED)
        draw_text(f"평균 인식: {p_perc:.2f}", 20, 160, RED)

        # --- 그래프 데이터 저장 ---
        if not hasattr(simulate, "history"):
            simulate.history = {"h_size": [], "p_size": [], "h_speed": [], "p_speed": []}
        
        # 주기적으로 데이터 추가 (매 프레임마다 하면 너무 많으므로)
        if pygame.time.get_ticks() % 10 == 0:
            simulate.history["h_size"].append(h_size)
            simulate.history["p_size"].append(p_size)
            simulate.history["h_speed"].append(h_speed)
            simulate.history["p_speed"].append(p_speed)
            
            # 그래프 길이 제한
            max_len = 300
            if len(simulate.history["h_size"]) > max_len:
                for key in simulate.history:
                    simulate.history[key].pop(0)

        # --- 그래프 그리기 (하단) ---
        graph_width = 300
        graph_height = 100
        graph_x = 10
        graph_y = HEIGHT - graph_height - 10
        
        # 배경
        pygame.draw.rect(screen, (50, 50, 50), (graph_x, graph_y, graph_width, graph_height))
        pygame.draw.rect(screen, (255, 255, 255), (graph_x, graph_y, graph_width, graph_height), 1)
        draw_text("평균 크기 (초록: 초식, 빨강: 포식)", graph_x, graph_y - 20, WHITE)

        def draw_line_graph(data, color, offset_x, offset_y, g_width, g_height, max_val=20):
            if len(data) < 2: return
            points = []
            for i, val in enumerate(data):
                x = offset_x + (i / len(data)) * g_width
                # y값 정규화 (최대값 기준)
                y = offset_y + g_height - (min(val, max_val) / max_val) * g_height
                points.append((x, y))
            pygame.draw.lines(screen, color, False, points, 2)

        draw_line_graph(simulate.history["h_size"], GREEN, graph_x, graph_y, graph_width, graph_height, 20)
        draw_line_graph(simulate.history["p_size"], RED, graph_x, graph_y, graph_width, graph_height, 20)

        # 속도 그래프 (오른쪽에 추가)
        graph_x2 = graph_x + graph_width + 20
        pygame.draw.rect(screen, (50, 50, 50), (graph_x2, graph_y, graph_width, graph_height))
        pygame.draw.rect(screen, (255, 255, 255), (graph_x2, graph_y, graph_width, graph_height), 1)
        draw_text("평균 속도", graph_x2, graph_y - 20, WHITE)

        draw_line_graph(simulate.history["h_speed"], GREEN, graph_x2, graph_y, graph_width, graph_height, 10)
        draw_line_graph(simulate.history["p_speed"], RED, graph_x2, graph_y, graph_width, graph_height, 10)


        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

# 실행
if __name__ == "__main__":
    simulate()