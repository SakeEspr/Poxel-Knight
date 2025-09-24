import pygame
import os

pygame.init()

# ---------- CONFIG ----------
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Poxel')

FPS = 60
clock = pygame.time.Clock()

# ---------- GAME VARIABLES ----------
GRAVITY = 0.75
DASH_SPEED = 12
DASH_TIME = 10
DASH_COOLDOWN = 40

JUMP_SPEED = -11
MAX_JUMP_TIME = 15
JUMP_HOLD_FORCE = -0.5

ATTACK_RANGE = 60
ATTACK_WIDTH = 40
ATTACK_HEIGHT = 50
ATTACK_DAMAGE = 10

BG = (255, 200, 200)  # Pink background

moving_left = False
moving_right = False

# Health bar colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ---------- HEALTH BAR FUNCTION ----------
def draw_health_bar(x, y, current_health, max_health, width=200, height=20, label="Health"):
    # Background bar
    pygame.draw.rect(screen, BLACK, (x-2, y-2, width+4, height+4))
    pygame.draw.rect(screen, RED, (x, y, width, height))
    
    # Health bar
    health_ratio = max(0, current_health / max_health)
    health_width = int(width * health_ratio)
    pygame.draw.rect(screen, GREEN, (x, y, health_width, height))
    
    # Text
    font = pygame.font.Font(None, 24)
    text = font.render(f"{label}: {current_health}/{max_health}", True, WHITE)
    screen.blit(text, (x, y - 25))

# ---------- PLATFORM CLASS ----------
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, invisible=False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if invisible:
            self.image.set_alpha(0)
            self.image.fill((0, 0, 0))
        else:
            self.image.fill((255, 255, 255))  # White platforms
        self.rect = self.image.get_rect(topleft=(x, y))

platform_group = pygame.sprite.Group()

platforms = [
    (0, 650, SCREEN_WIDTH, 80),
    (0, 530, 300, 20),
    (900, 530, 300, 20),
    (280, 410, 200, 20),
    (720, 410, 200, 20)
]

for platform_data in platforms:
    platform = Platform(*platform_data)
    platform_group.add(platform)

def draw_bg():
    screen.fill(BG)  # Pink background
    platform_group.draw(screen)

# ---------- PROJECTILE CLASS ----------
class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, speed=6):
        super().__init__()
        self.direction = direction
        self.speed = speed
        
        # Create projectile sprite
        self.image = pygame.Surface((12, 6))
        self.image.fill((255, 255, 0))  # Yellow projectile
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
    def update(self):
        # Move horizontally
        self.rect.x += self.speed * self.direction
        
        # Remove if off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        
        # Check platform collisions
        for platform in platform_group:
            if self.rect.colliderect(platform.rect):
                self.kill()

# ---------- ENEMY CLASS ----------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, scale, speed):
        super().__init__()
        self.alive = True
        self.speed = speed * 1.2
        self.direction = -1
        self.flip = False
        
        # Health
        self.max_health = 120
        self.health = self.max_health
        
        # Movement
        self.vel_y = 0
        self.in_air = True
        self.patrol_distance = 200
        self.start_x = x
        
        # Jumping
        self.can_jump = True
        self.jump_cooldown = 0
        
        # AI states
        self.state = 'patrol'  # 'patrol', 'chase', 'shoot'
        self.detection_range = 250
        self.shoot_range = 200
        self.shoot_cooldown = 0
        
        # Create enemy sprite
        self.image = pygame.Surface((70, 90))
        self.image.fill((255, 0, 0))  # Red enemy
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def ai_behavior(self, player, projectile_group):
        if not self.alive or not player.alive:
            return
            
        dx = 0
        dy = 0
        
        # Calculate distance to player
        distance_to_player = abs(self.rect.centerx - player.rect.centerx)
        player_height_diff = self.rect.centery - player.rect.centery
        
        # Update cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1
        
        # State machine
        if distance_to_player <= self.shoot_range and self.shoot_cooldown == 0:
            self.state = 'shoot'
        elif distance_to_player <= self.detection_range:
            self.state = 'chase'
        else:
            self.state = 'patrol'
        
        # Shooting behavior
        if self.state == 'shoot':
            self.shoot_cooldown = 75
            
            # Face player
            if player.rect.centerx > self.rect.centerx:
                self.direction = 1
                self.flip = False
            else:
                self.direction = -1
                self.flip = True
            
            # Create projectile
            projectile = Projectile(self.rect.centerx, self.rect.centery, self.direction)
            projectile_group.add(projectile)
        
        # Chase behavior
        elif self.state == 'chase':
            # Face player
            if player.rect.centerx > self.rect.centerx:
                self.direction = 1
                self.flip = False
                dx = self.speed
            else:
                self.direction = -1
                self.flip = True
                dx = -self.speed
            
            # Jump if player is above and enemy can jump
            if player_height_diff > 60 and not self.in_air and self.jump_cooldown == 0 and distance_to_player < 150:
                self.vel_y = JUMP_SPEED * 1.1
                self.in_air = True
                self.jump_cooldown = 45
        
        # Patrol behavior
        elif self.state == 'patrol':
            if self.rect.centerx <= self.start_x - self.patrol_distance:
                self.direction = 1
                self.flip = False
            elif self.rect.centerx >= self.start_x + self.patrol_distance:
                self.direction = -1
                self.flip = True
            
            dx = self.speed * self.direction
            
            # Random jump while patrolling
            if not self.in_air and self.jump_cooldown == 0 and pygame.time.get_ticks() % 300 == 0:
                if abs(dx) > 0:
                    self.vel_y = JUMP_SPEED * 0.8
                    self.in_air = True
                    self.jump_cooldown = 60
        
        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y
        
        # Horizontal movement and collision
        self.rect.x += dx
        for platform in platform_group:
            if self.rect.colliderect(platform.rect):
                if dx > 0:
                    self.rect.right = platform.rect.left
                    if self.state == 'patrol':
                        self.direction = -1
                        self.flip = True
                elif dx < 0:
                    self.rect.left = platform.rect.right
                    if self.state == 'patrol':
                        self.direction = 1
                        self.flip = False
        
        # Vertical movement and collision
        self.rect.y += dy
        self.in_air = True
        for platform in platform_group:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.in_air = False
                elif self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
        
        # Keep enemy on screen
        if self.rect.left < 0:
            self.rect.left = 0
            if self.state == 'patrol':
                self.direction = 1
                self.flip = False
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            if self.state == 'patrol':
                self.direction = -1
                self.flip = True

    def draw(self):
        # Change color based on state
        if self.state == 'shoot':
            self.image.fill((255, 200, 0))  # Orange when shooting
        elif self.state == 'chase':
            self.image.fill((255, 100, 100))  # Light red when chasing
        else:
            self.image.fill((255, 0, 0))  # Normal red when patrolling
        
        img = pygame.transform.flip(self.image, self.flip, False)
        screen.blit(img, self.rect)

# ---------- PLAYER CLASS ----------
class Player(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        super().__init__()
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.direction = 1
        self.flip = False
        
        # Health
        self.max_health = 100
        self.health = self.max_health

        # Jump
        self.vel_y = 0
        self.in_air = True
        self.jump_pressed = False
        self.jump_timer = 0

        # Dash
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0

        # Attack
        self.attacking = False
        self.attack_type = None  # "side", "up", "down"
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.attack_rect = None

        # Animations
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()

        animation_types = ['Idle', 'Run', 'Jump', 'Fall', 'Dash', 'Attack', 'Attack_Up', 'Attack_Down']
        for animation in animation_types:
            temp_list = []
            try:
                num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
                for i in range(num_of_frames):
                    img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png')
                    img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                    temp_list.append(img)
            except:
                # Fallback to simple rectangles if images don't exist
                for i in range(4):
                    img = pygame.Surface((60, 80))
                    img.fill((0, 0, 255))  # Blue player
                    temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def attack(self):
        if self.attack_cooldown == 0 and not self.dashing:
            keys = pygame.key.get_pressed()
            self.attacking = True
            self.attack_cooldown = 20

            if keys[pygame.K_w]:
                # Upward attack
                self.attack_type = 'up'
                self.attack_timer = len(self.animation_list[6]) * 40
                self.update_action(6)

                self.attack_rect = pygame.Rect(
                    self.rect.centerx - ATTACK_WIDTH // 2,
                    self.rect.top - ATTACK_RANGE,
                    ATTACK_WIDTH,
                    ATTACK_RANGE
                )

            elif keys[pygame.K_s] and self.in_air:
                # Downward attack
                self.attack_type = 'down'
                self.attack_timer = len(self.animation_list[7]) * 40
                self.update_action(7)

                self.attack_rect = pygame.Rect(
                    self.rect.centerx - ATTACK_WIDTH // 2,
                    self.rect.bottom,
                    ATTACK_WIDTH,
                    ATTACK_RANGE
                )

            else:
                # Side attack
                self.attack_type = 'side'
                self.attack_timer = len(self.animation_list[5]) * 40
                self.update_action(5)

                if self.direction == 1:
                    self.attack_rect = pygame.Rect(
                        self.rect.right,
                        self.rect.centery - ATTACK_HEIGHT // 2,
                        ATTACK_RANGE,
                        ATTACK_HEIGHT
                    )
                else:
                    self.attack_rect = pygame.Rect(
                        self.rect.left - ATTACK_RANGE,
                        self.rect.centery - ATTACK_HEIGHT // 2,
                        ATTACK_RANGE,
                        ATTACK_HEIGHT
                    )

    def move(self, moving_left, moving_right):
        dx = 0
        dy = 0
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()

        # Dash input
        if mouse[2] and not self.dashing and self.dash_cooldown == 0 and not self.attacking:
            self.dashing = True
            self.dash_timer = DASH_TIME
            self.dash_cooldown = DASH_COOLDOWN
            self.vel_y = 0
            self.update_action(4)

        if self.dashing:
            dx = DASH_SPEED * self.direction
            dy = 0
            self.update_action(4)
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dashing = False
        else:
            if moving_left:
                dx = -self.speed
                self.flip = True
                self.direction = -1
            if moving_right:
                dx = self.speed
                self.flip = False
                self.direction = 1

            # Hold-to-jump
            if keys[pygame.K_SPACE]:
                if not self.jump_pressed:
                    self.jump_pressed = True
                    if not self.in_air:
                        self.vel_y = JUMP_SPEED
                        self.in_air = True
                        self.jump_timer = MAX_JUMP_TIME
                else:
                    if self.jump_timer > 0:
                        self.vel_y += JUMP_HOLD_FORCE
                        self.jump_timer -= 1
            else:
                self.jump_pressed = False
                self.jump_timer = 0

            # Gravity
            self.vel_y += GRAVITY
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

        # Dash cooldown
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # Attack updates
        if self.attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attacking = False
                self.attack_type = None
                self.attack_rect = None
            elif self.attack_rect:
                if self.attack_type == 'side':
                    if self.direction == 1:
                        self.attack_rect.x = self.rect.right
                    else:
                        self.attack_rect.x = self.rect.left - ATTACK_RANGE
                    self.attack_rect.centery = self.rect.centery
                elif self.attack_type == 'up':
                    self.attack_rect.centerx = self.rect.centerx
                    self.attack_rect.y = self.rect.top - ATTACK_RANGE
                elif self.attack_type == 'down':
                    self.attack_rect.centerx = self.rect.centerx
                    self.attack_rect.y = self.rect.bottom

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # Horizontal collisions
        self.rect.x += dx
        for platform in platform_group:
            if self.rect.colliderect(platform.rect):
                if dx > 0:
                    self.rect.right = platform.rect.left
                elif dx < 0:
                    self.rect.left = platform.rect.right

        # Vertical collisions
        self.rect.y += dy
        self.in_air = True
        for platform in platform_group:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.in_air = False
                    self.jump_timer = 0
                elif self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        if self.action in [5, 6, 7]:  # attack animations
            ANIMATION_COOLDOWN = 3

        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

            # End-of-animation resets
            if self.frame_index >= len(self.animation_list[self.action]):
                if self.action in [5, 6, 7]:
                    self.attacking = False
                    self.attack_type = None
                    self.attack_rect = None
                self.frame_index = 0

        # --- Downward pogo mechanic for last 3 frames ---
        if self.action == 7 and self.attack_rect and self.attacking:  # Attack_Down
            last_frames_start = len(self.animation_list[7]) - 3
            if self.frame_index >= last_frames_start:
                # Update attack_rect position each frame
                self.attack_rect.centerx = self.rect.centerx
                self.attack_rect.y = self.rect.bottom

                for platform in platform_group:
                    if self.attack_rect.colliderect(platform.rect) and self.vel_y >= 0:
                        self.vel_y = -13  # negative to go up
                        self.attacking = False
                        self.attack_cooldown = 15
                        self.update_action(0)  # back to idle
                        break

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self):
        img = pygame.transform.flip(self.image, self.flip, False)

        draw_x = self.rect.left
        draw_y = self.rect.bottom - img.get_height()

        # Offsets for attack animations (sprite alignment hack)
        if self.action == 5:  # Side Attack
            if self.direction == 1:  # facing right
                draw_x += 15
            else:  # facing left
                draw_x -= 30

        elif self.action == 7:  # Down Attack
            draw_y += 30  # move sprite downward a bit

        screen.blit(img, (draw_x, draw_y))

# ---------- COMBAT SYSTEM ----------
def check_combat(player, enemy, projectile_group):
    # Player attacking enemy
    if player.attacking and player.attack_rect and enemy.alive:
        if player.attack_rect.colliderect(enemy.rect):
            enemy.take_damage(ATTACK_DAMAGE)
            # Prevent multiple hits from same attack
            player.attack_rect = None
    
    # Projectiles hitting player (only if not dashing)
    if not player.dashing:
        for projectile in projectile_group:
            if projectile.rect.colliderect(player.rect) and player.alive:
                player.take_damage(12)
                projectile.kill()

# ---------- GAME RESTART FUNCTION ----------
def restart_game():
    global player, enemy, projectile_group
    player = Player('player', 200, 200, 3, 5)
    enemy = Enemy(800, 500, 2, 2)
    projectile_group = pygame.sprite.Group()

# ---------- MAIN LOOP ----------
player = Player('player', 200, 200, 3, 5)
enemy = Enemy(800, 500, 2, 2)
projectile_group = pygame.sprite.Group()

run = True
while run:
    clock.tick(FPS)
    draw_bg()

    player.update_animation()
    player.draw()

    if player.alive:
        if player.attacking:
            if player.attack_type == 'up':
                player.update_action(6)
            elif player.attack_type == 'down':
                player.update_action(7)
            else:
                player.update_action(5)
        elif player.dashing:
            player.update_action(4)
        elif player.in_air:
            if player.vel_y < 0:
                player.update_action(2)
            else:
                player.update_action(3)
        elif moving_left or moving_right:
            player.update_action(1)
        else:
            player.update_action(0)
        
        player.move(moving_left, moving_right)

    # Update enemy
    if enemy.alive:
        enemy.ai_behavior(player, projectile_group)
        enemy.draw()
    
    # Update projectiles
    projectile_group.update()
    projectile_group.draw(screen)
    
    # Check combat
    check_combat(player, enemy, projectile_group)
    
    # Draw health bars
    draw_health_bar(50, 50, player.health, player.max_health, label="Player")
    draw_health_bar(50, 100, enemy.health, enemy.max_health, label="Enemy")
    
    # Check if player died and restart game
    if not player.alive:
        restart_game()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_BACKSPACE:
                run = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                player.attack()

    pygame.display.update()

pygame.quit()