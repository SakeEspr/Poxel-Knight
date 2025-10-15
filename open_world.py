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

BG = (255, 200, 200)

moving_left = False
moving_right = False

Back = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
Back.fill(BG)
Back = Back.convert()

# ---------- HEALTH MASKS ----------
RED = (255, 0, 0)
GREEN = (0, 255, 0)

try:
    mask_filled = pygame.image.load('img/player/Mask/mask_filled.png')
    mask_empty = pygame.image.load('img/player/Mask/mask_empty.png')
    MASK_SCALE = 1.5
    mask_filled = pygame.transform.scale(mask_filled, 
        (int(mask_filled.get_width() * MASK_SCALE), int(mask_filled.get_height() * MASK_SCALE)))
    mask_empty = pygame.transform.scale(mask_empty, 
        (int(mask_empty.get_width() * MASK_SCALE), int(mask_empty.get_height() * MASK_SCALE)))
    mask_filled = mask_filled.convert_alpha()
    mask_empty = mask_empty.convert_alpha()
except:
    mask_filled = pygame.Surface((30, 30))
    mask_filled.fill(GREEN)
    mask_empty = pygame.Surface((30, 30))
    mask_empty.fill(RED)
    mask_filled = mask_filled.convert()
    mask_empty = mask_empty.convert()

def draw_health_masks(current_masks, max_masks=5):
    mask_spacing = 10
    start_x = 20
    start_y = 20
    for i in range(max_masks):
        x = start_x + i * (mask_filled.get_width() + mask_spacing)
        y = start_y
        if i < current_masks:
            screen.blit(mask_filled, (x, y))
        else:
            screen.blit(mask_empty, (x, y))

# ---------- PLATFORM CLASS ----------
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, invisible=False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if invisible:
            self.image.set_alpha(0)
            self.image.fill((0, 0, 0))
        else:
            self.image.fill((100, 100, 100))
        self.image = self.image.convert_alpha() if invisible else self.image.convert()
        self.rect = pygame.Rect(x, y, width, height)

platform_group = pygame.sprite.Group()
platforms = [
    (0, 775, SCREEN_WIDTH, 40),
    (0, 0, SCREEN_WIDTH, 1)
]
for platform_data in platforms:
    platform = Platform(*platform_data)
    platform_group.add(platform)

def create_static_background():
    bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg_surface.blit(Back, (0, 0))
    for platform in platform_group:
        if platform.image.get_alpha() != 0:
            bg_surface.blit(platform.image, platform.rect)
    return bg_surface.convert()

static_background = create_static_background()

def draw_bg():
    screen.blit(static_background, (0, 0))

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
        self.max_masks = 5
        self.current_masks = 5
        self.damage_cooldown = 0

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
        self.attack_type = None
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
                animation_path = f'img/{self.char_type}/{animation}'
                if os.path.exists(animation_path):
                    num_of_frames = len(os.listdir(animation_path))
                    for i in range(num_of_frames):
                        img = pygame.image.load(f'{animation_path}/{i}.png')
                        img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                        img = img.convert_alpha()
                        temp_list.append(img)
                else:
                    for i in range(4):
                        img = pygame.Surface((60, 80))
                        img.fill((0, 100, 200))
                        img = img.convert()
                        temp_list.append(img)
            except:
                for i in range(4):
                    img = pygame.Surface((60, 80))
                    img.fill((0, 100, 200))
                    img = img.convert()
                    temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def take_damage(self, damage):
        if self.damage_cooldown == 0:
            self.current_masks -= damage
            self.damage_cooldown = 60
            if self.current_masks <= 0:
                self.current_masks = 0
                self.alive = False

    def attack(self):
        if self.attack_cooldown == 0 and not self.dashing:
            keys = pygame.key.get_pressed()
            self.attacking = True
            self.attack_cooldown = 20
            if keys[pygame.K_w]:
                self.attack_type = 'up'
                self.attack_timer = len(self.animation_list[6]) * 40
                self.update_action(6)
                self.attack_rect = pygame.Rect(self.rect.centerx - 20, self.rect.top - 60, 40, 60)
            elif keys[pygame.K_s] and self.in_air:
                self.attack_type = 'down'
                self.attack_timer = len(self.animation_list[7]) * 40
                self.update_action(7)
                self.attack_rect = pygame.Rect(self.rect.centerx - 20, self.rect.bottom, 40, 60)
            else:
                self.attack_type = 'side'
                self.attack_timer = len(self.animation_list[5]) * 40
                self.update_action(5)
                if self.direction == 1:
                    self.attack_rect = pygame.Rect(self.rect.right, self.rect.centery - 25, 60, 50)
                else:
                    self.attack_rect = pygame.Rect(self.rect.left - 60, self.rect.centery - 25, 60, 50)

    def move(self, moving_left, moving_right):
        dx = 0
        dy = 0
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()

        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1

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

            # Jumping
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

        # Apply movement
        self.rect.x += dx
        self.rect.y += dy

        # Vertical collision only (platforms)
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

        # Dash cooldown
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # Attacking updates
        if self.attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attacking = False
                self.attack_type = None
                self.attack_rect = None
            elif self.attack_rect:
                if self.attack_type == 'side':
                    self.attack_rect.x = self.rect.right if self.direction == 1 else self.rect.left - 60
                    self.attack_rect.centery = self.rect.centery
                elif self.attack_type == 'up':
                    self.attack_rect.centerx = self.rect.centerx
                    self.attack_rect.y = self.rect.top - 60
                elif self.attack_type == 'down':
                    self.attack_rect.centerx = self.rect.centerx
                    self.attack_rect.y = self.rect.bottom

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    # Animation functions remain unchanged
    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        if self.action in [5,6,7]:
            ANIMATION_COOLDOWN = 3
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            if self.frame_index >= len(self.animation_list[self.action]):
                if self.action in [5,6,7]:
                    self.attacking = False
                    self.attack_type = None
                    self.attack_rect = None
                self.frame_index = 0

        if self.action == 7 and self.attack_rect and self.attacking:
            last_frames_start = len(self.animation_list[7]) - 3
            if self.frame_index >= last_frames_start:
                self.attack_rect.centerx = self.rect.centerx
                self.attack_rect.y = self.rect.bottom

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self):
        img = pygame.transform.flip(self.image, self.flip, False)
        draw_x = self.rect.left
        draw_y = self.rect.bottom - img.get_height()
        if self.action == 5:
            draw_x += 15 if self.direction == 1 else -30
        elif self.action == 7:
            draw_y += 30
        if self.damage_cooldown > 0 and self.damage_cooldown % 10 < 5:
            img.set_alpha(128)
        else:
            img.set_alpha(255)
        screen.blit(img, (draw_x, draw_y))

# ---------- GAME RESTART ----------
def restart_game():
    global player
    player = Player('player', 200, 200, 3, 5)

# ---------- MAIN LOOP ----------
player = Player('player', 200, 200, 3, 5)

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
            player.update_action(2 if player.vel_y < 0 else 3)
        elif moving_left or moving_right:
            player.update_action(1)
        else:
            player.update_action(0)

        player.move(moving_left, moving_right)

    draw_health_masks(player.current_masks, player.max_masks)

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
