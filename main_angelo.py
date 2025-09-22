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


BROWN = (139, 69, 19)  # ADD: Color for platforms

# Load background image
Back = pygame.image.load('img/BG/New_BG.png')
Back = pygame.transform.scale(Back, (SCREEN_WIDTH, SCREEN_HEIGHT))

moving_left = False
moving_right = False

# ADD: PLATFORM CLASS ----------
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, invisible=False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if invisible:
            self.image.set_alpha(0)
            self.image.fill((0, 0, 0))
        self.rect = pygame.Rect(x, y, width, height)

platform_group = pygame.sprite.Group()

# ADD: Define your platforms (x, y, width, height)
platforms = [
    (0, 650, SCREEN_WIDTH, 80, True),      # Ground/floor
    (0, 530, 300, 20),         # Platform 1
    (900, 530, 300, 20)
]

# ADD: Create platform sprites
for platform_data in platforms:
    platform = Platform(*platform_data)
    platform_group.add(platform)

def draw_bg():
    screen.blit(Back, (0, 0))  # Draw the background image
    platform_group.draw(screen)  # ADD: Draw all platforms

# ---------- PLAYER CLASS ----------
class Player(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        super().__init__()
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.direction = 1
        self.flip = False

        self.vel_y = 0
        self.jump = False
        self.in_air = True

        # Dash
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0

        # Animations
        self.attacking = False
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

    def move(self, moving_left, moving_right):
        dx = 0
        dy = 0

        mouse = pygame.mouse.get_pressed()
        keys = pygame.key.get_pressed()
        
        # # Attack input
        # if mouse[1] and not self.dashing:
        #     self.attacking = True
        #     self.update_action(5)

        # Dash input
        if keys[pygame.K_LSHIFT] and not self.dashing and self.dash_cooldown == 0:
            self.dashing = True
            self.dash_timer = DASH_TIME
            self.dash_cooldown = DASH_COOLDOWN
            self.vel_y = 0
            self.update_action(4)  # Dash animation

        # --- DASH BEHAVIOR ---
        if self.dashing:
            dx = DASH_SPEED * self.direction
            dy = 0
            self.update_action(4)  # Keep dash animation active while dashing
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dashing = False
        else:
            # Normal movement
            if moving_left:
                dx = -self.speed
                self.flip = True
                self.direction = -1
            if moving_right:
                dx = self.speed
                self.flip = False
                self.direction = 1

            # Jump
            if self.jump and not self.in_air:
                self.vel_y = -15
                self.jump = False
                self.in_air = True

            # Gravity
            self.vel_y += GRAVITY
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

        # Dash cooldown
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # REPLACE: Old floor collision with platform collision
        # --- PLATFORM COLLISION ---
        # Move horizontally first
        self.rect.x += dx
        
        # Check for horizontal collisions
        for platform in platform_group:
            if self.rect.colliderect(platform.rect):
                if dx > 0:  # Moving right
                    self.rect.right = platform.rect.left
                elif dx < 0:  # Moving left
                    self.rect.left = platform.rect.right

        # Move vertically
        self.rect.y += dy
        self.in_air = True
        
        # Check for vertical collisions
        for platform in platform_group:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:  # Falling down
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.in_air = False
                elif self.vel_y < 0:  # Jumping up
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

        # Keep player on screen
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        self.image = self.animation_list[self.action][self.frame_index]

        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

            # Loop dash animation while dashing
            if self.action == 4:
                if self.frame_index >= len(self.animation_list[4]):
                    self.frame_index = 0
            else:
                if self.frame_index >= len(self.animation_list[self.action]):
                    self.frame_index = 0

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

# ---------- MAIN LOOP ----------
player = Player('player', 200, 200, 3, 5)

run = True
while run:
    clock.tick(FPS)
    draw_bg()

    player.update_animation()
    player.draw()

    # --- STATE HANDLING ---
    if player.alive:
        if player.dashing:
            player.update_action(4)  # Dash
        elif player.in_air:
            if player.vel_y < 0 + 0.5:
                player.update_action(2)  # Jump
            else:
                player.update_action(3)  # Fall
        elif moving_left or moving_right:
            player.update_action(1)  # Run
        else:
            player.update_action(0)  # Idle
        player.move(moving_left, moving_right)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_SPACE and player.alive:
                player.jump = True
            if event.key == pygame.K_BACKSPACE:
                run = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False

    pygame.display.update()

pygame.quit()