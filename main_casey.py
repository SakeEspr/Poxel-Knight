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
DASH_SPEED = 14
DASH_TIME = 12
DASH_COOLDOWN = 40

enemy1_JUMP_CHANCE = 0.03   #% chance each frame while patrolling

# Global game state
static_background = None  # Will be set after platforms are created
roof_restored = False     # Track if the roof has been restored after falling through

JUMP_SPEED = -11
MAX_JUMP_TIME = 15
JUMP_HOLD_FORCE = -0.5

ATTACK_RANGE = 60
ATTACK_WIDTH = 40
ATTACK_HEIGHT = 50
ATTACK_DAMAGE = 10

# Well dimensions
WELL_WIDTH = 300
WELL_HEIGHT = 100

BG = (255, 200, 200)

moving_left = False
moving_right = False
DEBUG_HITBOXES = False  # Toggle with left bracket
waiting_for_reentry = False  # Set when player teleports above the screen and waits to re-enter
middle_platforms_visible = True
# Small delay (in frames) to wait after teleport before restoring the environment
waiting_for_reentry_counter = 0

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

# ---------- LOAD WELL IMAGES ----------
try:
    well_img = pygame.image.load('img/BG/well1.png')
    well_img = pygame.transform.scale(well_img, (WELL_WIDTH, WELL_HEIGHT))
    well_img = well_img.convert_alpha()
    
    well2_img = pygame.image.load('img/BG/well2.png')
    well2_img = pygame.transform.scale(well2_img, (WELL_WIDTH, WELL_HEIGHT))
    well2_img = well2_img.convert_alpha()
except pygame.error:
    well_img = None
    well2_img = None

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

 #PLATFORM CLASS ----------
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, invisible=False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if invisible:
            self.image.set_alpha(0)
            self.image.fill((0, 0, 0))
        # Convert for better performance
        self.image = self.image.convert_alpha() if invisible else self.image.convert()
        self.rect = pygame.Rect(x, y, width, height)

platform_group = pygame.sprite.Group()

# Vertical platform positions (used to split the ground into three segments)
VPLAT_WIDTH = 25
VPLAT_HEIGHT = 100
VPLAT_Y = 600  # top y so bottom aligns with ground at 650
VPLAT_LEFT_X = 475
VPLAT_RIGHT_X = 700

# Split the main ground into three segments so the middle is between the two columns
GROUND_Y = 650
GROUND_H = 80

# Compute left/middle/right segments
left_x = 0
left_w = max(0, int(VPLAT_LEFT_X - left_x))
mid_x = int(VPLAT_LEFT_X)
mid_w = max(0, int(VPLAT_RIGHT_X - VPLAT_LEFT_X))
right_x = int(VPLAT_RIGHT_X)
right_w = max(0, SCREEN_WIDTH - right_x)

platforms = [
    (left_x, GROUND_Y, left_w, GROUND_H, True),
    (mid_x, GROUND_Y, mid_w, GROUND_H, True),
    (right_x, GROUND_Y, right_w, GROUND_H, True),
    (0, 700, SCREEN_WIDTH, 200, False),  # Floor
]

for platform_data in platforms:
    platform = Platform(*platform_data)
    platform_group.add(platform)
    # Keep a reference to the middle ground segment so we can remove it later
    if platform_data[0] == mid_x and platform_data[2] == mid_w and platform_data[3] == GROUND_H:
        middle_ground_platform = platform

    # Vertical platforms that appear after enemy is killed
vertical_platforms = []  # list of Platform instances added at runtime
vertical_platforms_active = False
 
# Create roof segments (left, middle, right) so we can remove the middle roof later
ROOF_Y = -350
ROOF_H = 400
roof_left = (left_x, ROOF_Y, left_w, ROOF_H, True)
roof_mid = (mid_x, ROOF_Y, mid_w, ROOF_H, True)
roof_right = (right_x, ROOF_Y, right_w, ROOF_H, True)
for roof_data in (roof_left, roof_mid, roof_right):
    roof_plat = Platform(*roof_data)
    platform_group.add(roof_plat)
    if roof_data[0] == mid_x and roof_data[2] == mid_w:
        middle_roof_platform = roof_plat
 

def create_vertical_platforms():
    """Create two vertical platforms and add them to platform_group and our list.
    Safe to call multiple times; will only create once.
    """
    global vertical_platforms_active, vertical_platforms
    if vertical_platforms_active:
        return
    # Create platform sprites at visual positions
    p1 = Platform(VPLAT_LEFT_X, VPLAT_Y, VPLAT_WIDTH, VPLAT_HEIGHT, invisible=True)
    p2 = Platform(VPLAT_RIGHT_X, VPLAT_Y, VPLAT_WIDTH, VPLAT_HEIGHT, invisible=True)

    # Store the original visual rects for drawing the full image
    orig_r1 = p1.rect.copy()
    orig_r2 = p2.rect.copy()

    # Determine tight hitbox from the image's non-transparent pixels
    try:
        b1 = p1.image.get_bounding_rect()  # bounding rect of non-transparent pixels (local coords)
        b2 = p2.image.get_bounding_rect()
    except Exception:
        # Fallback to full rect if something goes wrong
        b1 = p1.image.get_rect()
        b2 = p2.image.get_rect()

    # Convert bounding rects to world coordinates based on the visual rect origin
    hit_r1 = pygame.Rect(orig_r1.x + b1.x, orig_r1.y + b1.y, b1.width, b1.height)
    hit_r2 = pygame.Rect(orig_r2.x + b2.x, orig_r2.y + b2.y, b2.width, b2.height)

    # Assign tight hitboxes to the platform sprites (these are used for collisions)
    p1.rect = hit_r1
    p2.rect = hit_r2

    # Keep the original visual rects for drawing so the image stays the same
    p1._visual_rect = orig_r1
    p2._visual_rect = orig_r2

    # Add to collision group and store in runtime list
    platform_group.add(p1)
    platform_group.add(p2)
    vertical_platforms = [p1, p2]
    vertical_platforms_active = True

def remove_vertical_platforms():
    """Remove the runtime vertical platforms from the collision group and clear list."""
    global vertical_platforms_active, vertical_platforms
    for p in list(vertical_platforms):
        try:
            platform_group.remove(p)
        except Exception:
            pass
    vertical_platforms = []
    vertical_platforms_active = False

def create_static_background(black_bg=False):
    """Create a single surface with background and platforms combined.
    If black_bg is True, uses a black background instead of the normal one."""
    bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    if black_bg:
        # Fill with pure black for post-well background
        bg_surface.fill((0, 0, 0))
    else:
        # Normal background
        bg_surface.blit(Back, (0, 0))
    
    # When using black background, draw ALL platforms
    # Otherwise only draw non-invisible ones
    for platform in platform_group:
        if black_bg or platform.image.get_alpha() != 0:
            bg_surface.blit(platform.image, platform.rect)
    
    return bg_surface.convert()  # Convert for faster blitting

# Create the static background once
static_background = create_static_background()

# Track whether we've processed the enemy1 death effects once
enemy1_dead_handled = False
# When True we suppress the death-environment visuals (platform removal / well)
boss_env_suppressed = False

def draw_bg():
    """OPTIMIZED: Just blit the pre-rendered background"""
    screen.blit(static_background, (0, 0))

def draw_well():
    """Draw a well with its front part appearing in front of characters"""
    if well_img:
        # Draw the back part of the well first
        screen.blit(well_img, (450, 575))

def draw_well_front():
    """Draw the front part of the well"""
    if well2_img:
        # Draw the front part of the well
        screen.blit(well2_img, (450, 612))

def enemy1_dead():
    # Note: the front part of the well is drawn each frame from the main loop
    # so we don't draw it here (avoids one-off draws at death time).
    create_vertical_platforms()  # Create vertical platforms when enemy dies
    # Remove the middle ground segment to create a gap between vertical platforms
    try:
        middle_ground_platform
    except NameError:
        pass
    else:
        try:
            platform_group.remove(middle_ground_platform)
        except Exception:
            pass
        else:
            # Recreate the static background so the removed middle platform is no longer
            # drawn into the pre-baked background surface.
            try:
                static_background = create_static_background()
            except Exception:
                # If create_static_background isn't available or fails, ignore so game stays running
                pass
    # Also remove the middle roof platform so the roof gap appears
    try:
        middle_roof_platform
    except NameError:
        pass
    else:
        try:
            platform_group.remove(middle_roof_platform)
        except Exception:
            pass
        else:
            try:
                static_background = create_static_background()
            except Exception:
                pass

# ---------- ENEMY CLASS ----------
class Enemy1(pygame.sprite.Sprite):
    def __init__(self, x, y, scale, speed):
        super().__init__()
        self.alive = True
        self.speed = speed * 2.5  # Make enemy1 20% faster than player
        self.direction = -1
        self.flip = False  # Start flipped since direction is -1
        
        # Health
        self.max_health = 120
        self.health = self.max_health
        
        # Movement
        self.vel_y = 0
        self.in_air = True
        self.patrol_distance = 500
        self.start_x = x
        
        # Jumping
        self.can_jump = True
        self.jump_cooldown = 0
        self.jump_timer = 180  # 3 seconds at 60 FPS
        self.is_jumping = False
        
        # AI states
        self.state = 'patrol'  # 'patrol', 'chase'
        self.detection_range = 250
        self.reaction_time = 60
        
        # Animation system
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        
        # Load animations with error handling and convert for performance
        animation_types = ['Idle', 'Run']
        for animation in animation_types:
            temp_list = []
            try:
                animation_path = f'img/enemy/{animation}'
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
                        img = pygame.Surface((70, 90))
                        img.fill((255, 0, 0))  # Red enemy1
                        img = img.convert()
                        temp_list.append(img)
            except:
                # Fallback animation
                for i in range(4):
                    img = pygame.Surface((70, 90))
                    img.fill((255, 0, 0))
                    img = img.convert()
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

    def ai_behavior(self, player):
        if not self.alive or not player.alive:
            return
            
        dx = 0
        dy = 0
        
        # Calculate distance to player
        distance_to_player = abs(self.rect.centerx - player.rect.centerx)
        player_height_diff = self.rect.centery - player.rect.centery
        
        # Update cooldowns
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1

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
            # enemy1_JUMP_CHANCE is a float probability in [0,1]
            if (
                not self.in_air
                and self.jump_cooldown == 0
                and random.random() < enemy1_JUMP_CHANCE
            ):
                if abs(dx) > 0:  # Only jump if moving
                    self.vel_y = JUMP_SPEED * 0.8  # Smaller patrol jump
                    self.in_air = True
                    self.jump_cooldown = 60  # cooldown in frames   
        
        

        if distance_to_player <= self.detection_range:
            if self.state == 'patrol':
                self.detection_timer += 1
                if self.detection_timer >= self.reaction_time:
                    self.state = 'chase'
                    self.detection_timer = 0
        else:
            self.state = 'patrol'
            self.detection_timer = 0  # Reset timer when player leaves range


        
        # Calculate movement speed (90% when jumping)
        current_speed = self.speed * 0.9 if self.is_jumping else self.speed
        
        # Chase behavior
        if self.state == 'chase':
            # Face player (reversed flip logic)
            if player.rect.centerx > self.rect.centerx:
                self.direction = 1
                self.flip = True  # Flipped from original
                dx = current_speed
            else:
                self.direction = -1
                self.flip = False  # Flipped from original
                dx = -current_speed
        
        # Patrol behavior
        elif self.state == 'patrol':
            if self.rect.centerx <= self.start_x - self.patrol_distance:
                self.direction = 1
                self.flip = True  # Flipped from original
            elif self.rect.centerx >= self.start_x + self.patrol_distance:
                self.direction = -1
                self.flip = False  # Flipped from original
            
            dx = current_speed * self.direction
            
            # Random jump while patrolling (removed old jump logic since we now have timed jumps)
        
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
                    self.is_jumping = False  # Reset jumping state when landing
                elif self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
        
        # Keep enemy1 on screen
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

    def update_animation(self):
        ANIMATION_COOLDOWN = 50  # Made faster - was 100
        
        # Save bottom position to maintain consistent height
        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx
        
        # Update image and recreate rect
        self.image = self.animation_list[self.action][self.frame_index]
        new_rect = self.image.get_rect()
        new_rect.centerx = old_centerx
        new_rect.bottom = old_bottom
        self.rect = new_rect
        
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            
            if self.frame_index >= len(self.animation_list[self.action]):
                self.frame_index = 0

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self):
        # Update animation based on state
        if self.state == 'chase' or self.state == 'patrol':
            # Check if enemy1 is actually moving
            if abs(self.speed) > 0:
                self.update_action(1)  # Run animation
            else:
                self.update_action(0)  # Idle animation
        else:
            self.update_action(0)  # Idle animation
        
        # Update animation frame
        self.update_animation()
        
        # Flip the image if needed
        img = pygame.transform.flip(self.image, self.flip, False)
        
        # Draw sprite anchored to bottom of collision rect
        draw_x = self.rect.left
        draw_y = self.rect.bottom - img.get_height()
        screen.blit(img, (draw_x, draw_y))

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
        if self.damage_cooldown == 0 and not self.dashing:
            self.current_masks -= 1  # Lose one mask
            self.damage_cooldown = 90  # 1 second of invincibility at 60 FPS
            
            if self.current_masks <= 0:
                self.current_masks = 0
                self.alive = False

    def create_attack_hitbox(self, attack_type):
        """Create the attack hitbox based on attack type"""
        if attack_type == 'up':
            return pygame.Rect(
                self.rect.centerx - ATTACK_WIDTH // 2,
                self.rect.top - ATTACK_RANGE,
                ATTACK_WIDTH,
                ATTACK_RANGE
            )
        elif attack_type == 'down':
            return pygame.Rect(
                self.rect.centerx - ATTACK_WIDTH // 2,
                self.rect.bottom,
                ATTACK_WIDTH,
                ATTACK_RANGE
            )
        else:  # side attack
            x = self.rect.right if self.direction == 1 else self.rect.left - ATTACK_RANGE
            return pygame.Rect(
                x,
                self.rect.centery - ATTACK_HEIGHT // 2,
                ATTACK_RANGE,
                ATTACK_HEIGHT
            )

    def attack(self):
        # Only attack if not on cooldown and not dashing
        if self.attack_cooldown > 0 or self.dashing:
            return

        keys = pygame.key.get_pressed()
        self.attacking = True
        self.attack_cooldown = 20

        # Determine attack type
        if keys[pygame.K_w]:
            self.attack_type = 'up'
            animation_index = 6
        elif keys[pygame.K_s] and self.in_air:
            self.attack_type = 'down'
            animation_index = 7
        else:
            self.attack_type = 'side'
            animation_index = 5

        # Set attack duration and animation
        self.attack_timer = len(self.animation_list[animation_index]) * 40
        self.update_action(animation_index)

        # Create the attack hitbox
        self.attack_rect = self.create_attack_hitbox(self.attack_type)

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
                        # Wall jump - sends you up and to opposite side with more outward force
                        self.vel_y = JUMP_SPEED  # Up
                        if self.wall_side == -1:  # Left wall
                            dx = self.speed * 4  # Go right with more force
                            self.flip = False
                            self.direction = 1
                        elif self.wall_side == 1:  # Right wall
                            dx = -self.speed * 4  # Go left with more force
                            self.flip = True
                            self.direction = -1
                        self.wall_sliding = False
                        self.wall_side = 0
                        self.jump_timer = MAX_JUMP_TIME
                else:
                    # Variable height jumping
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

        # Update attack state
        if self.attacking:
            self.attack_timer -= 1
            
            # End attack if timer runs out
            if self.attack_timer <= 0:
                self.attacking = False
                self.attack_type = None
                self.attack_rect = None
            # Update attack hitbox position
            elif self.attack_rect:
                self.attack_rect = self.create_attack_hitbox(self.attack_type)

        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # HORIZONTAL COLLISIONS AND WALL DETECTION (screen borders only)
        # Horizontal movement
        self.rect.x += dx

        # Horizontal collision with platforms (runtime vertical platforms included)
        for platform in platform_group:
            if self.rect.colliderect(platform.rect):
                if dx > 0:
                    # Hit a platform moving right -> place player to the left of it
                    self.rect.right = platform.rect.left
                    # If in air and moving into platform, enable wall sliding
                    if self.in_air:
                        self.wall_sliding = True
                        self.wall_side = 1
                elif dx < 0:
                    # Hit a platform moving left -> place player to the right of it
                    self.rect.left = platform.rect.right
                    if self.in_air:
                        self.wall_sliding = True
                        self.wall_side = -1

        # Check screen boundaries for wall jumping
        if self.in_air and self.vel_y > 0:
            if self.rect.left <= 0:
                self.rect.left = 0
                # Check if player is moving toward the left wall
                if moving_left:
                    self.wall_sliding = True
                    self.wall_side = -1
                else:
                    self.wall_sliding = False
                    self.wall_side = 0
            elif self.rect.right >= SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH
                # Check if player is moving toward the right wall
                if moving_right:
                    self.wall_sliding = True
                    self.wall_side = 1
                else:
                    self.wall_sliding = False
                    self.wall_side = 0
            else:
                # Not touching any walls
                self.wall_sliding = False
                self.wall_side = 0
        else:
            # Normal screen boundary collision when not in air or not falling
            if self.rect.left < 0:
                self.rect.left = 0
            elif self.rect.right > SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH
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

        # Teleport if falling far below the screen
        # Use the module-level waiting_for_reentry flag to signal the main loop
        global waiting_for_reentry, waiting_for_reentry_counter

        if self.rect.top > SCREEN_HEIGHT - 200:
            # Place the player just above the visible screen (so they are not "deleted")
            # This keeps the player visible as they re-enter and prevents moving them far off-screen.
            try:
                img_h = self.image.get_height()
            except Exception:
                img_h = 64

            # Put the player's top just above the screen
            self.rect.top = -img_h - 300
            # Reset vertical velocity so gravity will pull them back into view naturally
            self.vel_y = 0
            
            # Immediately restore bottom platform and clear well graphics
            try:
                # Clear the well images right away so it stops drawing
                global well_img, well2_img, boss_env_suppressed, roof_restored
                well_img = None
                well2_img = None
                boss_env_suppressed = True
                roof_restored = False  # Mark roof as not restored yet
                
                # Restore only bottom platform right away if missing
                if middle_ground_platform not in platform_group:
                    platform_group.add(middle_ground_platform)
                    middle_platforms_visible = True
                
                # Remove vertical platforms since we're resetting
                remove_vertical_platforms()
            except Exception:
                pass

            # Start a short delay to avoid immediately restoring the top while the
            # player is still overlapping the roof area. This prevents the fast
            # replace/flash issue reported by placing the top back too soon.
            waiting_for_reentry = True
            # Frames to wait before the main loop will perform the restore
            waiting_for_reentry_counter = 120

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
def check_combat(player, enemy1):
    # Player attacking enemy1
    if player.attacking and player.attack_rect and enemy1.alive:
        if player.attack_rect.colliderect(enemy1.rect):
            enemy1.take_damage(ATTACK_DAMAGE)
            
            # Special bounce for downward attack
            if player.attack_type == 'down' and player.vel_y >= 0:
                player.vel_y = -13  # Bounce up
                player.attacking = False
                player.attack_cooldown = 15
                player.update_action(0)  # Back to idle
            
            # Prevent multiple hits from same attack
            player.attack_rect = None

    # enemy1 damages player on collision (with invincibility frames check)
    if enemy1.alive and player.alive and player.rect.colliderect(enemy1.rect):
        player.take_damage(1)  # Take 1 mask of damage

# ---------- DRAW enemy1 HEALTH BAR ----------
def draw_enemy1_health_bar(enemy1):
    """Draw a simple health bar for the enemy1"""
    if enemy1.alive and enemy1.health < enemy1.max_health:
        bar_width = 50
        bar_height = 5
        bar_x = enemy1.rect.centerx - bar_width // 2
        bar_y = enemy1.rect.top - 15
        
        # Background
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        
        # Health
        health_width = int(bar_width * (enemy1.health / enemy1.max_health))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, bar_height))

# ---------- MAIN MENU ----------
def draw_main_menu():
    """Draw the main menu screen"""
    try:
        main_menu_img = pygame.image.load('img/BG/main_screen.png')
        main_menu_img = pygame.transform.scale(main_menu_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        main_menu_img = main_menu_img.convert()
        screen.blit(main_menu_img, (0, 0))
    except pygame.error:
        # Fallback if image doesn't exist
        screen.fill((50, 50, 100))
        font = pygame.font.Font(None, 74)
        text = font.render('POXEL', True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(text, text_rect)
        
        font_small = pygame.font.Font(None, 36)
        text_small = font_small.render('Click anywhere to start', True, WHITE)
        text_rect_small = text_small.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(text_small, text_rect_small)

# ---------- GAME RESTART FUNCTION ----------
def restart_game():
    global player, enemy1, roof_restored
    player = Player('player', 200, 200, 3, 5)
    enemy1 = Enemy1(800, 500, 2, 2)
    roof_restored = False  # Reset roof state on game restart
    # Remove any runtime vertical platforms when restarting
    try:
        remove_vertical_platforms()
    except NameError:
        pass

# ---------- MAIN LOOP ----------
player = Player('player', 200, 200, 3, 5)
enemy1 = Enemy1(800, 500, 2, 2)

# Game state
game_state = 'menu'  # 'menu' or 'playing'

run = True
while run:
    clock.tick(FPS)
    
    if game_state == 'menu':
        draw_main_menu()
    elif game_state == 'playing':
        # Always fill with black first if we're in post-well state (player has gone through well)
        if waiting_for_reentry or boss_env_suppressed:
            screen.fill((0, 0, 0))
            # Draw all platforms on top of black background
            for platform in platform_group:
                screen.blit(platform.image, platform.rect)
        else:
            # Normal pre-well background
            draw_bg()
            # Draw the well behind everything if enemy is dead and not suppressed
            if not enemy1.alive and not boss_env_suppressed and well_img:
                draw_well()  # Draw back part of well first

        # Draw player on top of either background
        player.update_animation()
        player.draw()

        # Draw the front of the well in front of the player if boss death visuals are active
        if not enemy1.alive and not boss_env_suppressed and well2_img:
            draw_well_front()

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

        # Update enemy1 and run death effects only once when they die
        if enemy1.alive:
            enemy1.ai_behavior(player)
            enemy1.draw()
            draw_enemy1_health_bar(enemy1)  # Draw enemy1 health bar
        else:
            # enemy is dead
            if not enemy1_dead_handled:
                # Apply the death-time environment changes once
                enemy1_dead()
                enemy1_dead_handled = True
        
        # Draw runtime vertical platforms (if any)
        if vertical_platforms_active:
            for vp in vertical_platforms:
                # Draw visual at original visual rect if available, otherwise at collision rect
                vis_rect = getattr(vp, '_visual_rect', vp.rect)
                screen.blit(vp.image, vis_rect)

        # Check combat
        check_combat(player, enemy1)
        
        # Draw health masks instead of health bars
        draw_health_masks(player.current_masks, player.max_masks)
        
        # Check if player died and restart game
        if not player.alive:
            restart_game()
            
        # If player teleported above, handle delayed roof restoration
        if waiting_for_reentry:
            # Give the player a few frames to fall through before restoring the roof
            if waiting_for_reentry_counter > 0:
                waiting_for_reentry_counter -= 1
            elif player.rect.top >= 0 and not roof_restored:
                # After delay and player is back on screen, restore the roof
                try:
                    # Re-add the roof platform
                    if middle_roof_platform not in platform_group:
                        platform_group.add(middle_roof_platform)
                    roof_restored = True  # Mark roof as restored
                except Exception:
                    pass
                # Clear waiting state
                waiting_for_reentry = False
                waiting_for_reentry_counter = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_LEFTBRACKET:
                DEBUG_HITBOXES = not DEBUG_HITBOXES
                print(f"DEBUG_HITBOXES={DEBUG_HITBOXES}")
            if event.key == pygame.K_ESCAPE:
                run = False
            if event.key == pygame.K_RIGHTBRACKET:
                enemy1.health = 0
                enemy1.alive = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if game_state == 'menu':
                    # Start game on click
                    game_state = 'playing'
                    restart_game()
                elif game_state == 'playing':
                    player.attack()

    # Debug: draw hitbox outlines if enabled
    if DEBUG_HITBOXES and game_state == 'playing':
        # Draw platform hitboxes
        for plat in platform_group:
            pygame.draw.rect(screen, (255, 0, 0), plat.rect, 2)

        # Player hitbox
        pygame.draw.rect(screen, (255, 0, 0), player.rect, 2)

        # Enemy hitbox
        if enemy1:
            pygame.draw.rect(screen, (255, 0, 0), enemy1.rect, 2)

    pygame.display.update()

pygame.quit()