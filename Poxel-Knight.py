import pygame
import os

# ---------- CONFIG ----------
SCREEN_W, SCREEN_H = 1200, 700
FPS = 60

GRAVITY = 0.5
MOVE_SPEED = 6
JUMP_SPEED = -9
MAX_JUMP_TIME = 10

DASH_SPEED = 12
DASH_TIME = 10
DASH_COOLDOWN = 40
ATTACK_TIME = 10

# ---------- LOAD ASSETS ----------
def load_animation_images(path, scale):
    frames = []
    for filename in sorted(os.listdir(path)):
        img = pygame.image.load(os.path.join(path, filename)).convert_alpha()
        img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
        frames.append(img)
    return frames


# ---------- BASE OBJECT CLASS ----------
class GameObject:
    def __init__(self, rect, color=(255,255,255), visible=True):
        self.rect = rect
        self.color = color
        self.visible = visible

    def draw(self, surface):
        if self.visible:
            pygame.draw.rect(surface, self.color, self.rect)


# ---------- PLAYER (with animation + physics) ----------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, scale=3, speed=MOVE_SPEED):
        super().__init__()
        self.alive = True
        self.speed = speed
        self.direction = 1
        self.flip = False

        # animations
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()

        # load animations
        idle = load_animation_images("player/Idle", scale)
        run = load_animation_images("player/Run", scale)
        self.animation_list = [idle, run]

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

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
                self.direction = -1
                self.flip = True
            elif keys[pygame.K_d]:
                self.vel_x = MOVE_SPEED
                self.direction = 1
                self.flip = False
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

        if self.attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attacking = False

        # Dash logic
        if self.dashing:
            self.vel_x = DASH_SPEED * self.direction
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
            if self.rect.colliderect(obj.rect):
                # vertical collision
                if self.vel_y > 0 and self.rect.bottom > obj.rect.top and self.rect.top < obj.rect.top:
                    self.rect.bottom = obj.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_timer = 0
                elif self.vel_y < 0 and self.rect.top < obj.rect.bottom and self.rect.bottom > obj.rect.bottom:
                    self.rect.top = obj.rect.bottom
                    self.vel_y = 0
                # horizontal collision
                if self.vel_x > 0 and self.rect.right > obj.rect.left and self.rect.left < obj.rect.left:
                    self.rect.right = obj.rect.left
                    self.vel_x = 0
                elif self.vel_x < 0 and self.rect.left < obj.rect.right and self.rect.right > obj.rect.right:
                    self.rect.left = obj.rect.right
                    self.vel_x = 0

        # update animation state
        if self.vel_x != 0:
            self.update_action(1)  # running
        else:
            self.update_action(0)  # idle
        self.update_animation()

    # --- Animations ---
    def update_animation(self):
        ANIMATION_COOLDOWN = 120
        self.image = self.animation_list[self.action][self.frame_index]
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

    def draw(self, surface):
        surface.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


# ---------- MAIN ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Hollow Knight Clone")
    clock = pygame.time.Clock()

    # setup objects
    objects = []
    player = Player(200, 450)
    objects.append(GameObject(pygame.Rect(10, 675, SCREEN_W - 20, 40), (50, 50, 50)))  # ground
    objects.append(GameObject(pygame.Rect(40, 525, 200, 20), (50, 50, 50)))
    objects.append(GameObject(pygame.Rect(960, 525, 200, 20), (50, 50, 50)))
    objects.append(GameObject(pygame.Rect(390, 370, 425, 20), (50, 50, 50)))

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()

        # update
        player.update(keys, mouse, objects)

        # draw
        screen.fill((30, 30, 30))
        for obj in objects:
            obj.draw(screen)
        player.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
