import pygame
import os
import random

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

ENEMY_JUMP_CHANCE = 0.03   # 1% chance each frame while patrolling

JUMP_SPEED = -11
MAX_JUMP_TIME = 15
JUMP_HOLD_FORCE = -0.5

ATTACK_RANGE = 60
ATTACK_WIDTH = 40
ATTACK_HEIGHT = 50
ATTACK_DAMAGE = 10

BG = (255, 200, 200)

moving_left = False
moving_right = False

# OPTIMIZED: Pre-scale background once and convert for better blitting performance
try:
    Back = pygame.image.load('img/BG/New_BG.png')
    Back = pygame.transform.scale(Back, (SCREEN_WIDTH, SCREEN_HEIGHT))
    Back = Back.convert()  # Convert for faster blitting
except pygame.error:
    # Fallback if image doesn't exist
    Back = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    Back.fill(BG)
    Back = Back.convert()

# Health bar colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ---------- LOAD HEALTH MASKS ----------
try:
    mask_filled = pygame.image.load('img/player/Mask/mask_filled.png')
    mask_empty = pygame.image.load('img/player/Mask/mask_empty.png')
    # Scale masks to appropriate size (adjust scale as needed)
    MASK_SCALE = 2  # Adjust this value to make masks bigger/smaller
    mask_filled = pygame.transform.scale(mask_filled, 
        (int(mask_filled.get_width() * MASK_SCALE), 
         int(mask_filled.get_height() * MASK_SCALE)))
    mask_empty = pygame.transform.scale(mask_empty, 
        (int(mask_empty.get_width() * MASK_SCALE), 
         int(mask_empty.get_height() * MASK_SCALE)))
    # Convert for better performance
    mask_filled = mask_filled.convert_alpha()
    mask_empty = mask_empty.convert_alpha()
except pygame.error:
    # Fallback if images don't exist
    mask_filled = pygame.Surface((30, 30))
    mask_filled.fill(GREEN)
    mask_empty = pygame.Surface((30, 30))
    mask_empty.fill(RED)
    mask_filled = mask_filled.convert()
    mask_empty = mask_empty.convert()

# ---------- HEALTH MASK FUNCTION ----------
def draw_health_masks(current_masks, max_masks=5):
    """Draw health masks Hollow Knight style"""
    mask_spacing = 10  # Space between masks
    start_x = 20  # Starting X position
    start_y = 20  # Starting Y position
    
    for i in range(max_masks):
        x = start_x + i * (mask_filled.get_width() + mask_spacing)
        y = start_y
        
        if i < current_masks:
            screen.blit(mask_filled, (x, y))
        else:
            screen.blit(mask_empty, (x, y))

# ADD: PLATFORM CLASS ----------
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, invisible=False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if invisible:
            self.image.set_alpha(0)
            self.image.fill((0, 0, 0))
        else:
            self.image.fill((0, 0, 0))  # Gray platforms for visibility
        # Convert for better performance
        self.image = self.image.convert_alpha() if invisible else self.image.convert()
        self.rect = pygame.Rect(x, y, width, height)

platform_group = pygame.sprite.Group()

platforms = [
    (0, 650, SCREEN_WIDTH, 80, True),      # Ground/floor
    (100, 530, 240, 20),                     # Platform 1
    (800, 530, 240, 20),
    (0, 0, SCREEN_WIDTH, 2)
]

for platform_data in platforms:
    platform = Platform(*platform_data)
    platform_group.add(platform)

# OPTIMIZED: Create a static background surface that includes platforms
# This way we only need to blit one surface instead of background + all platforms
def create_static_background():
    """Create a single surface with background and platforms combined"""
    bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg_surface.blit(Back, (0, 0))  # Draw background
    
    # Draw non-invisible platforms onto the background
    for platform in platform_group:
        if platform.image.get_alpha() != 0:  # Only draw visible platforms
            bg_surface.blit(platform.image, platform.rect)
    
    return bg_surface.convert()  # Convert for faster blitting

# Create the static background once
static_background = create_static_background()

def draw_bg():
    """OPTIMIZED: Just blit the pre-rendered background"""
    screen.blit(static_background, (0, 0))

# ---------- ENEMY CLASS ----------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, scale, speed):
        super().__init__()
        self.alive = True
        self.speed = speed * 2.7 # Make enemy faster
        self.direction = -1
        self.flip = False
        
        # Health
        self.max_health = 200  # Make enemy stronger
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
        
        # OPTIMIZED: Create enemy sprite once and convert
        self.base_image = pygame.Surface((70, 90))  # Make enemy bigger
        self.base_image = self.base_image.convert()
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        # Cache flipped version
        self.flipped_image = None
        self.current_color = None

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def ai_behavior(self, player):
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
            self.shoot_cooldown = 75  # Faster shooting (1.25 seconds at 60 FPS)
            
            # Face player
            if player.rect.centerx > self.rect.centerx:
                self.direction = 1
                self.flip = False
            else:
                self.direction = -1
                self.flip = True
        
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
        
        # Patrol behavior
        elif self.state == 'patrol':
            if self.rect.centerx <= self.start_x - self.patrol_distance:
                self.direction = 1
                self.flip = False
            elif self.rect.centerx >= self.start_x + self.patrol_distance:
                self.direction = -1
                self.flip = True
            
            dx = self.speed * self.direction
            
            # Random jump while patrolling (small chance)
            if (
                not self.in_air
                and self.jump_cooldown == 0
                and random.random() < ENEMY_JUMP_CHANCE
    ):
                if abs(dx) > 0:  # Only jump if moving
                    self.vel_y = JUMP_SPEED * 0.8  # Smaller patrol jump
                    self.in_air = True
                    self.jump_cooldown = 60  # cooldown in frames   
        
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
        # OPTIMIZED: Only update color/flip when needed
        color = None
        if self.state == 'shoot':
            color = (255, 200, 0)  # Orange when shooting
        elif self.state == 'chase':
            color = (255, 100, 100)  # Light red when chasing
        else:
            color = (255, 0, 0)  # Normal red when patrolling
        
        # Only recreate image if color changed
        if color != self.current_color:
            self.current_color = color
            self.base_image.fill(color)
            self.flipped_image = pygame.transform.flip(self.base_image, True, False)
        
        # Use cached flipped version
        if self.flip:
            screen.blit(self.flipped_image, self.rect)
        else:
            screen.blit(self.base_image, self.rect)

# ---------- PLAYER CLASS ----------
class Player(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        super().__init__()
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.direction = 1
        self.flip = False
        
        # Health - Modified for mask system
        self.max_masks = 5  # 5 masks like Hollow Knight
        self.current_masks = 5  # Start with full health
        self.damage_cooldown = 0  # Invincibility frames after taking damage

        # Jump
        self.vel_y = 0
        self.in_air = True
        self.jump_pressed = False
        self.jump_timer = 0
        
        # Wall jump mechanics
        self.wall_sliding = False
        self.wall_side = 0  # -1 for left wall, 1 for right wall, 0 for no wall
        self.wall_slide_speed = 2  # Speed when sliding down wall
        
        # Wall jump mechanics
        self.wall_sliding = False
        self.wall_side = 0  # -1 for left wall, 1 for right wall, 0 for no wall
        self.wall_slide_speed = 2  # Speed when sliding down wall

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

        # OPTIMIZED: Load animations with error handling and convert for performance
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
                        img = img.convert_alpha()  # Convert for better performance
                        temp_list.append(img)
                else:
                    # Fallback: create simple colored rectangles
                    for i in range(4):  # 4 frames fallback
                        img = pygame.Surface((60, 80))
                        img.fill((0, 100, 200))  # Blue player
                        img = img.convert()
                        temp_list.append(img)
            except:
                # Fallback animation
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
        # Only take damage if not in invincibility frames
        if self.damage_cooldown == 0:
            self.current_masks -= 1  # Lose one mask
            self.damage_cooldown = 60  # 1 second of invincibility at 60 FPS
            
            if self.current_masks <= 0:
                self.current_masks = 0
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

        # Update damage cooldown
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1

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

            # Wall jump logic
            if keys[pygame.K_SPACE]:
                if not self.jump_pressed:
                    self.jump_pressed = True
                    if not self.in_air:
                        # Ground jump
                        self.vel_y = JUMP_SPEED
                        self.in_air = True
                        self.jump_timer = MAX_JUMP_TIME
                    elif self.wall_sliding:
                        # Wall jump
                        self.vel_y = JUMP_SPEED
                        # Push away from wall
                        if self.wall_side == -1:  # Left wall
                            dx = self.speed * 1.5  # Jump right with extra force
                            self.flip = False
                            self.direction = 1
                        elif self.wall_side == 1:  # Right wall
                            dx = -self.speed * 1.5  # Jump left with extra force
                            self.flip = True
                            self.direction = -1
                        self.wall_sliding = False
                        self.wall_side = 0
                        self.jump_timer = MAX_JUMP_TIME
                else:
                    if self.jump_timer > 0 and not self.wall_sliding:
                        self.vel_y += JUMP_HOLD_FORCE
                        self.jump_timer -= 1
            else:
                self.jump_pressed = False
                self.jump_timer = 0

            # Apply gravity (reduced when wall sliding)
            if self.wall_sliding:
                # Slower fall when wall sliding
                self.vel_y += GRAVITY * 0.3
                if self.vel_y > self.wall_slide_speed:
                    self.vel_y = self.wall_slide_speed
            else:
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
        
        # Wall detection for wall jumping
        wall_detected = False
        
        # Skip platform collision during dash to allow dashing through enemy
        if not self.dashing:
            for platform in platform_group:
                if self.rect.colliderect(platform.rect):
                    if dx > 0:
                        self.rect.right = platform.rect.left
                        # Detect right wall
                        if self.in_air and self.vel_y > 0:
                            wall_detected = True
                            self.wall_side = 1
                    elif dx < 0:
                        self.rect.left = platform.rect.right
                        # Detect left wall
                        if self.in_air and self.vel_y > 0:
                            wall_detected = True
                            self.wall_side = -1
        
        # Check screen boundaries for wall jumping
        if self.in_air and self.vel_y > 0:
            if self.rect.left <= 0 and dx < 0:
                self.rect.left = 0
                wall_detected = True
                self.wall_side = -1
            elif self.rect.right >= SCREEN_WIDTH and dx > 0:
                self.rect.right = SCREEN_WIDTH
                wall_detected = True
                self.wall_side = 1
        else:
            # Normal screen boundary collision when not wall jumping
            if self.rect.left < 0:
                self.rect.left = 0
            elif self.rect.right > SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH
        
        # Update wall sliding state
        if wall_detected and self.in_air and self.vel_y > 0:
            # Check if player is moving toward the wall or holding toward wall
            if (self.wall_side == -1 and moving_left) or (self.wall_side == 1 and moving_right):
                self.wall_sliding = True
            else:
                self.wall_sliding = False
                self.wall_side = 0
        else:
            self.wall_sliding = False
            self.wall_side = 0

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
                    # Reset wall sliding when touching ground
                    self.wall_sliding = False
                    self.wall_side = 0
                elif self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        if self.action in [5, 6, 7]:  # attack animations faster
            ANIMATION_COOLDOWN = 3

        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

            if self.frame_index >= len(self.animation_list[self.action]):
                if self.action in [5, 6, 7]:
                    self.attacking = False
                    self.attack_type = None
                    self.attack_rect = None
                self.frame_index = 0
        
        # Downward pogo mechanic for last 3 frames
        if self.action == 7 and self.attack_rect and self.attacking:  # Attack_Down
            last_frames_start = len(self.animation_list[7]) - 3
            if self.frame_index >= last_frames_start:
                # Update attack_rect position each frame
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

        # Simple fixed offset for attack animation
        if self.action == 5:  # Side Attack
            if self.direction == 1:  # Facing right
                draw_x += 15
            else:  # Facing left
                draw_x -= 30
        elif self.action == 7:  # Down Attack
            draw_y += 30  # move sprite downward a bit

        # Flash effect when in invincibility frames (optional)
        if self.damage_cooldown > 0 and self.damage_cooldown % 10 < 5:
            # Make player semi-transparent when invincible
            img.set_alpha(128)
        else:
            img.set_alpha(255)

        screen.blit(img, (draw_x, draw_y))

# ---------- COMBAT SYSTEM ----------
def check_combat(player, enemy):
    # Player attacking enemy
    if player.attacking and player.attack_rect and enemy.alive:
        if player.attack_rect.colliderect(enemy.rect):
            enemy.take_damage(ATTACK_DAMAGE)
            
            # Special bounce for downward attack
            if player.attack_type == 'down' and player.vel_y >= 0:
                player.vel_y = -13  # Bounce up
                player.attacking = False
                player.attack_cooldown = 15
                player.update_action(0)  # Back to idle
            
            # Prevent multiple hits from same attack
            player.attack_rect = None

    # Enemy damages player on collision (with invincibility frames check)
    if enemy.alive and player.alive and player.rect.colliderect(enemy.rect):
        player.take_damage(1)  # Take 1 mask of damage

# ---------- DRAW ENEMY HEALTH BAR ----------
def draw_enemy_health_bar(enemy):
    """Draw a simple health bar for the enemy"""
    if enemy.alive and enemy.health < enemy.max_health:
        bar_width = 50
        bar_height = 5
        bar_x = enemy.rect.centerx - bar_width // 2
        bar_y = enemy.rect.top - 15
        
        # Background
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        
        # Health
        health_width = int(bar_width * (enemy.health / enemy.max_health))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, bar_height))

# ---------- GAME RESTART FUNCTION ----------
def restart_game():
    global player, enemy
    player = Player('player', 200, 200, 3, 5)
    enemy = Enemy(800, 500, 2, 2)

# ---------- MAIN LOOP ----------
player = Player('player', 200, 200, 3, 5)
enemy = Enemy(800, 500, 2, 2)

run = True
while run:
    clock.tick(FPS)
    draw_bg()  # Now much faster!

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
        elif player.wall_sliding:
            # Use idle animation for wall sliding (could be a dedicated wall slide animation)
            player.update_action(0)
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
        enemy.ai_behavior(player)
        enemy.draw()
        draw_enemy_health_bar(enemy)  # Draw enemy health bar
    
    # Check combat
    check_combat(player, enemy)
    
    # Draw health masks instead of health bars
    draw_health_masks(player.current_masks, player.max_masks)
    
    # Check if player died and restart game
    if not player.alive or not enemy.alive:
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