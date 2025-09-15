import pygame

# ---------- CONFIG ----------
SCREEN_W, SCREEN_H = 800, 600
FPS = 60

GRAVITY = 0.5
MOVE_SPEED = 6
JUMP_SPEED = -8
MAX_JUMP_TIME = 10

DASH_SPEED = 12
DASH_TIME = 10
DASH_COOLDOWN = 20
ATTACK_TIME = 10


# ---------- BASE OBJECT CLASS ----------
class GameObject:
    def __init__(self, rect, color=(255,255,255)):
        self.rect = rect
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)


# ---------- PLAYER ----------
class Player(GameObject):
    def __init__(self, x, y, w=30, h=30, color=(0, 200, 255)):
        super().__init__(pygame.Rect(x, y, w, h), color)
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

        # --- SCREEN WRAP (horizontal + vertical) ---
        '''
        if self.rect.right < 0:
            self.rect.left = SCREEN_W
        elif self.rect.left > SCREEN_W:
            self.rect.right = 0

        if self.rect.bottom < 0:
            self.rect.top = SCREEN_H
        elif self.rect.top > SCREEN_H:
            self.rect.bottom = 0
            '''


    # --- Draw ---
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

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
    pygame.display.set_caption("Hollow")
    clock = pygame.time.Clock()

    objects = []
    player = Player(200, 450)
    objects.append(player)

    # Platforms
    objects.append(GameObject(pygame.Rect(-1500, 550, 10000000, 100), (150, 150, 150)))

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


if __name__ == "__main__":
    main()


