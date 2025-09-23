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

JUMP_SPEED = -11     # initial jump impulse
MAX_JUMP_TIME = 15      # how many frames you can extend jump
JUMP_HOLD_FORCE = -0.5  # extra upward push while holding jump

# Attack variables
ATTACK_DURATION = 50  # frames the attack lasts
ATTACK_COOLDOWN = 20  # frames before you can attack again
ATTACK_RANGE = 60     # pixels in front of player
ATTACK_WIDTH = 40     # width of attack hitbox
ATTACK_HEIGHT = 50    # height of attack hitbox
ATTACK_DAMAGE = 10    # damage dealt

BG = (255, 200, 200)  # background for test animations

moving_left = False
moving_right = False

# ---------- PLATFORM CLASS ----------
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, invisible=False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if invisible:
            self.image.set_alpha(0)
            self.image.fill((0, 0, 0))
        else:
            self.image.fill((255, 255, 255))  # platform color
        self.rect = self.image.get_rect(topleft=(x, y))

platform_group = pygame.sprite.Group()

platforms = [
    (0, 650, SCREEN_WIDTH, 80),  # Ground
    (0, 530, 300, 20),
    (900, 530, 300, 20),
    (280, 410, 200, 20),
    (720, 410, 200, 20)
]

for platform_data in platforms:
    platform = Platform(*platform_data)
    platform_group.add(platform)

def draw_bg():
    screen.fill(BG)
    platform_group.draw(screen)

# ---------- PLAYER CLASS ----------
class Player(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        super().__init__()
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.direction = 1
        self.flip = False

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
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.attack_rect = None  # Hitbox for attack

        # Animations
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()

        animation_types = ['Idle', 'Run', 'Jump', 'Fall', 'Dash', 'Attack']
        for animation in animation_types:
            temp_list = []
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png')
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def attack(self):
        """Initiates an attack if not on cooldown"""
        if self.attack_cooldown == 0 and not self.dashing:
            self.attacking = True
            self.attack_timer = ATTACK_DURATION
            self.attack_cooldown = ATTACK_COOLDOWN
            
            # Create attack hitbox
            if self.direction == 1:  # Facing right
                self.attack_rect = pygame.Rect(
                    self.rect.right, 
                    self.rect.centery - ATTACK_HEIGHT // 2,
                    ATTACK_RANGE, 
                    ATTACK_HEIGHT
                )
            else:  # Facing left
                self.attack_rect = pygame.Rect(
                    self.rect.left - ATTACK_RANGE, 
                    self.rect.centery - ATTACK_HEIGHT // 2,
                    ATTACK_RANGE, 
                    ATTACK_HEIGHT
                )
            
            # Set attack animation
            self.update_action(5)  # Attack is index 5

    def move(self, moving_left, moving_right):
        dx = 0
        dy = 0
        keys = pygame.key.get_pressed()

        # --- DASH INPUT ---
        if keys[pygame.K_LSHIFT] and not self.dashing and self.dash_cooldown == 0 and not self.attacking:
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
            # Horizontal move (reduced if attacking)
            if moving_left:
                dx = -self.speed
                self.flip = True
                self.direction = -1
            if moving_right:
                dx = self.speed 
                self.flip = False
                self.direction = 1

            # --- HOLD TO JUMP ---
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

        # Update dash cooldown
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # Update attack state
        if self.attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attacking = False
                self.attack_rect = None
            # Update attack hitbox position if player moves
            elif self.attack_rect:
                if self.direction == 1:
                    self.attack_rect.x = self.rect.right
                else:
                    self.attack_rect.x = self.rect.left - ATTACK_RANGE
                self.attack_rect.centery = self.rect.centery

        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # --- COLLISIONS ---
        self.rect.x += dx
        for platform in platform_group:
            if self.rect.colliderect(platform.rect):
                if dx > 0:
                    self.rect.right = platform.rect.left
                elif dx < 0:
                    self.rect.left = platform.rect.right

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
        # Slower animation for attack to match longer duration
        if self.action == 5:  # Attack animation
            ANIMATION_COOLDOWN = 100
        
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            
            # Check if animation finished
            if self.frame_index >= len(self.animation_list[self.action]):
                if self.action == 5:  # Attack animation finished
                    self.attacking = False
                    self.attack_rect = None
                self.frame_index = 0

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
        
        # # Draw attack hitbox for debugging (optional - remove in final version)
        # if self.attack_rect:
        #     # Semi-transparent red rectangle to show attack area
        #     s = pygame.Surface((self.attack_rect.width, self.attack_rect.height))
        #     s.set_alpha(50)
        #     s.fill((255, 0, 0))
        #     screen.blit(s, (self.attack_rect.x, self.attack_rect.y))

# ---------- MAIN LOOP ----------
player = Player('player', 200, 200, 3, 5)

run = True
while run:
    clock.tick(FPS)
    draw_bg()

    player.update_animation()
    player.draw()

    if player.alive:
        # Priority system for animations
        if player.attacking:
            player.update_action(5)  # Attack
        elif player.dashing:
            player.update_action(4)  # Dash
        elif player.in_air:
            if player.vel_y < 0:
                player.update_action(2)  # Jump
            else:
                player.update_action(3)  # Fall
        elif moving_left or moving_right:
            player.update_action(1)  # Run
        else:
            player.update_action(0)  # Idle
        
        player.move(moving_left, moving_right)

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
        # Mouse click for attack
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                player.attack()

    pygame.display.update()

pygame.quit()