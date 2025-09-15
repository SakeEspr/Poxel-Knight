import pygame

class Camera:
    def __init__(self, screen_width, screen_height, y_offset=100):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.y_offset = y_offset  # How much higher to position camera
        self.x = 0
        self.y = 0
        
    def follow_target(self, target_rect):
        """Center the camera on the target (usually the player)"""
        self.x = target_rect.centerx - self.screen_width // 2
        self.y = target_rect.centery - self.screen_height // 2 -80
    
    def apply_to_rect(self, rect):
        """Apply camera offset to a rectangle for drawing"""
        return pygame.Rect(
            rect.x - self.x,
            rect.y - self.y,
            rect.width,
            rect.height
        )
    
    def apply_to_pos(self, x, y):
        """Apply camera offset to a position (x, y)"""
        return x - self.x, y - self.y
    
    def get_offset(self):
        """Get the current camera offset"""
        return self.x, self.y