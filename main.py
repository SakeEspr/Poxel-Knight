import pygame
import os

# ---------- CONFIG ----------
SCREEN_W, SCREEN_H = 800, 600
FPS = 60

GRAVITY = 0.5
MOVE_SPEED = 6
JUMP_SPEED = -8
MAX_JUMP_TIME = 10

DASH_SPEED = 12
DASH_TIME = 10
DASH_COOLDOWN = 30
ATTACK_TIME = 10

SCALE = 2  # scale up sprites

# ---------- BASE OBJECT CLASS ----------
class GameObject:
    def __init__(self, rect, color=(255,255,255)):
        self.rect = rect
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

# ---------- PLAYER ----------
class Player(GameObject):
    def __init__(self, x, y, frames):
        super().__init__(pygame.Rect(x, y, frames[0].get_width(), frames[0].get_height()))
        self.frames = frames
        self.current_anim = "idle"
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed = 6
        self.facing = 1

        # physics
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.jump_timer = 0

        # actions
        self.attacking = False
        self.attack_timer = 0
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0

    # --- Animation ---
    def set_animation(self, name):
        if self.current_anim != name:
            self.current_anim = name
            self.frame_index = 0
            self.anim_timer = 0
            self.anim_speed = ANIM_SPEEDS.get(name, 6)

    def update_animation(self):
        if self.attacking:
            self.set_animation("attack")
            return
        if self.dashing:
            self.set_animation("dash")
            return
        if not self.on_ground:
            self.set_animation("jump" if self.vel_y < 0 else "fall")
            return
        if self.vel_x != 0:
            self.set_animation("run" if abs(self.vel_x) > 4 else "walk")
        else:
            self.set_animation("idle")

    def animate(self):
        anim_frames = ANIMATIONS.get(self.current_anim, [0])
        safe_frames = [f for f in anim_frames if f < len(self.frames)]
        if not safe_frames:
            safe_frames = [0]

        self.anim_timer += 1
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(safe_frames)

        return self.frames[safe_frames[self.frame_index]]

    # --- Update ---
    def update(self, keys, mouse, objects):
        # Dash input
        if mouse[2] and not self.dashing and self.dash_cooldown == 0 and not self.attacking:
            self.dashing = True
            self.dash_timer = DASH_TIME
            self.dash_cooldown = DASH_COOLDOWN
            self.vel_y = 0

        # Horizontal input
        if not self.dashing and not self.attacking:
            if keys[pygame.K_a]:
                self.vel_x = -MOVE_SPEED
                self.facing = -1
            elif keys[pygame.K_d]:
                self.vel_x = MOVE_SPEED
                self.facing = 1
            else:
                self.vel_x = 0

        # Vertical movement
        if not self.dashing:
            self.vel_y += GRAVITY
            if self.vel_y > 15:
                self.vel_y = 15

        # Jump
        if keys[pygame.K_SPACE] and not self.dashing:
            if self.on_ground:
                self.vel_y = JUMP_SPEED
                self.on_ground = False
                self.jump_timer = MAX_JUMP_TIME
            elif self.jump_timer > 0:
                self.vel_y = JUMP_SPEED
                self.jump_timer -= 1
        else:
            self.jump_timer = 0

        # Attack
        if mouse[0] and not self.attacking and not self.dashing:
            self.attacking = True
            self.attack_timer = ATTACK_TIME
            self.vel_x = 0
            self.vel_y = 0

        if self.attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attacking = False

        # Dash logic
        if self.dashing:
            self.vel_x = DASH_SPEED * self.facing
            self.vel_y = 0
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dashing = False

        # Dash cooldown
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # Move & collide
        self.rect.x += int(self.vel_x)
        self.rect.y += int(self.vel_y)
        self.on_ground = False

        for obj in objects:
            if obj is self:
                continue
            if self.rect.colliderect(obj.rect):
                # vertical
                if self.vel_y > 0 and self.rect.bottom > obj.rect.top and self.rect.top < obj.rect.top:
                    self.rect.bottom = obj.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_timer = 0
                elif self.vel_y < 0 and self.rect.top < obj.rect.bottom and self.rect.bottom > obj.rect.bottom:
                    self.rect.top = obj.rect.bottom
                    self.vel_y = 0
                # horizontal
                if self.vel_x > 0 and self.rect.right > obj.rect.left and self.rect.left < obj.rect.left:
                    self.rect.right = obj.rect.left
                    self.vel_x = 0
                elif self.vel_x < 0 and self.rect.left < obj.rect.right and self.rect.right > obj.rect.right:
                    self.rect.left = obj.rect.right
                    self.vel_x = 0

        self.update_animation()

    # --- Draw ---
    def draw(self, surface):
        frame = self.animate()
        image = pygame.transform.flip(frame, self.facing == -1, False)
        surface.blit(image, self.rect.topleft)

        # Attack hitbox
        if self.attacking:
            attack_rect = pygame.Rect(
                self.rect.right if self.facing > 0 else self.rect.left - 20,
                self.rect.top + 5, 20, self.rect.height - 10
            )
            pygame.draw.rect(surface, (255, 255, 0), attack_rect)

# ---------- MAIN ----------
def main():
    pygame.init()
    print("Pygame initialized successfully!")

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Hollow Knight Demo")
    clock = pygame.time.Clock()

    # --- Load sprite sheet ---
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    sprite_path = os.path.join(BASE_DIR, "assets", "knight.png")
    print("Loading sprite from:", sprite_path)
    if not os.path.exists(sprite_path):
        raise FileNotFoundError(f"Sprite file not found at {sprite_path}")

    sprite_sheet = pygame.image.load(sprite_path).convert_alpha()

    # --- Slice frames safely ---
    FRAME_WIDTH = 30
    FRAME_HEIGHT = 21
    EXPECTED_FRAMES = 18
    sheet_width, sheet_height = sprite_sheet.get_size()
    TOTAL_FRAMES = min(sheet_width // FRAME_WIDTH, EXPECTED_FRAMES)

    frames = []
    for i in range(TOTAL_FRAMES):
        rect = pygame.Rect(i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT)
        if rect.right > sheet_width or rect.bottom > sheet_height:
            continue
        frame = sprite_sheet.subsurface(rect).copy()
        frame = pygame.transform.scale(frame, (FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE))
        frames.append(frame)

    print(f"Loaded {len(frames)} frames")

    # --- Animation mapping ---
    global ANIMATIONS, ANIM_SPEEDS
    ANIMATIONS = {
        "idle": [0],
        "walk": [1,2,3,4],
        "run": [5,6,7,8],
        "jump": [9],
        "fall": [10],
        "attack": [11,12,13],
        "dash": [14,15,16,17]
    }
    ANIM_SPEEDS = {
        "idle": 12,
        "walk": 6,
        "run": 4,
        "jump": 8,
        "fall": 8,
        "attack": 4,
        "dash": 3
    }

    objects = []
    player = Player(200, 450, frames)
    objects.append(player)

    # Platforms
    objects.append(GameObject(pygame.Rect(100, 500, 600, 20), (150, 150, 150)))
    objects.append(GameObject(pygame.Rect(300, 400, 200, 20), (150, 150, 150)))
    objects.append(GameObject(pygame.Rect(500, 300, 150, 20), (150, 150, 150)))

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()

        player.update(keys, mouse, objects)

        screen.fill((50,50,100))
        for obj in objects:
            obj.draw(screen)

        pygame.display.flip()

    pygame.quit()
    print("Game closed successfully.")

if __name__ == "__main__":
    main()
