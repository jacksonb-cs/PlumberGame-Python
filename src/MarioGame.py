# Jackson Bullard
# CSCE 3193H - 001
# Assignment 8

import pygame
import time

from pygame.locals import *
from time import sleep


# Sprite class - Inherited by all of the sprites
class Sprite:
    def __init__(self, image):
        # Stores image
        self.image = image

        # Sets rect if Mario or Goomba
        if isinstance(self.image, list):
            self.rect = self.image[0].get_rect()
        # Sets rect if Tube or Fireball
        else:
            # Stores rect object, which stores position and size
            self.rect = self.image.get_rect()

        # True iff sprite is moving or last moved to the left
        self.flip = False
        self.kill = False  # Marks sprite for deletion if true

    # Detects collision between two sprites
    def collidesWith(self, sprite):
        if (not self.rect.right < sprite.rect.left and
                not self.rect.left > sprite.rect.right and
                not self.rect.bottom < sprite.rect.top and
                not self.rect.top > sprite.rect.bottom):
            return True
        else:
            return False

    def update(self):
        pass


# Tube class - tubes.
class Tube(Sprite):
    def __init__(self, x, y):
        # Calls parent to store image and generate Rect info
        super().__init__(pygame.image.load("tube.png"))

        # Set tube position
        self.rect.left = x
        self.rect.top = y


# Fireball class - Extra spicy
class Fireball(Sprite):
    def __init__(self, model, mario_center, flip):
        # Reference to game Model (necessary to access ground position)
        self.model = model

        # Calls parent to store image and generate Rect info
        super().__init__(pygame.image.load("fireball.png"))

        # Initial position and orientation info
        self.rect.center = mario_center
        self.flip = flip

        # Fireball specific attributes
        self.velY = 0.0   # Vertical velocity

    # MAIN UPDATE METHOD (overrides update from Sprite class)
    def update(self):
        if self.flip:
            self.rect.move_ip(-25, 0)
        else:
            self.rect.move_ip(25, 0)

        # Removes fireball from game once it has left the screen (and then some)
        if (self.rect.left > self.model.scrollVal + 1400 or
                self.rect.right < self.model.scrollVal - 500):
            self.kill = True

        # Vertical motion
        if self.rect.bottom < self.model.ground:
            self.velY += 2.0

        self.rect.top += self.velY

        # Bounce fireball
        if self.rect.bottom > self.model.ground:
            self.rect.bottom = self.model.ground
            self.velY = -self.velY


# Goomba class - Bad guys
class Goomba(Sprite):
    def __init__(self, model, x, y):
        # Reference to game Model (for Tube collision)
        self.model = model

        self.frame = 0  # Animation frame
        self.dying = False  # True after being hit by a fireball
        self.deathTimer = 8     # Frames of being on fire before dying

        # Loads images
        image = [pygame.image.load("goomba.png"),
                 pygame.image.load("goomba_fire.png")]
        super().__init__(image)

        # Sets initial position
        self.rect.left = x
        self.rect.bottom = y

    # MAIN UPDATE METHOD (overrides update from Sprite class)
    def update(self):
        if self.flip and not self.dying:
            self.rect.move_ip(7, 0)
        elif not self.dying:
            self.rect.move_ip(-7, 0)

        for s in self.model.sprites:
            # Collide with tube
            if isinstance(s, Tube) and self.collidesWith(s):
                self.flip = not self.flip
            # Collide with fireball
            elif isinstance(s, Fireball) and self.collidesWith(s):
                # Set to die and change frame (flaming goomba image)
                self.dying = True
                self.frame = 1
                # Kill fireball
                s.kill = True

        if self.dying and self.deathTimer < 1:
            self.kill = True    # Dies
        elif self.dying:
            self.deathTimer -= 1    # Counts down death


# Mario class - The one and only
class Mario(Sprite):
    def __init__(self, model, x, y):
        self.model = model  # Reference to game Model

        self.velY = 0  # Vertical velocity (positive is down)
        self.frame = 0  # Animation frame
        self.fireReady = True   # Restricts fireballs to semi-automatic

        self.jumping = False  # True if space bar is pressed
        self.jumpCooldown = 0  # Stores current jump cooldown
        self.cooldownTime = 3  # Max jump cooldown time
        self.jumpLimit = 8  # Max time Mario can accelerate upwards in one jump

        # Loads all Mario images (necessary for animation)
        mario_images = [pygame.image.load("mario1.png"),
                        pygame.image.load("mario2.png"),
                        pygame.image.load("mario3.png"),
                        pygame.image.load("mario4.png"),
                        pygame.image.load("mario5.png")]

        # Calls parent class
        super().__init__(mario_images)

        # Sets starting position
        self.rect.left = x
        self.rect.bottom = y
        self.prevX = x
        self.prevY = y

    # MAIN UPDATE METHOD (overrides update from Sprite class)
    def update(self):
        # Determine if Mario can jump or continue to jump
        if (self.jumping and  # Must hold space...
                self.jumpCooldown == self.cooldownTime and  # ...not be on cooldown...
                self.jumpLimit > 0):  # ... or be out of jump juice (jumpLimit)
            self.velY = -15
            self.jumpLimit -= 1
        # Keeps Mario from briefly clipping through the ground
        elif self.model.ground - self.rect.bottom < self.velY:
            self.rect.top = self.model.ground - self.rect.height
            self.velY = 0
        # Mario accelerates downward
        elif self.rect.bottom < self.model.ground:
            self.velY += 1.4
        # Mario is on the ground
        else:
            self.velY = 0

        # Update Mario's vertical position
        self.rect.move_ip(0, self.velY)

        # Update various jumping variables
        if (not self.jumping and self.jumpLimit < 8 and
                self.jumpCooldown == self.cooldownTime):
            self.jumpCooldown = 0  # Starts jumpCooldown
            self.jumpLimit = 8  # Resets jumpLimit

        # Collision detection
        for s in self.model.sprites:
            # Only check Tubes
            if isinstance(s, Tube):
                if self.collidesWith(s):
                    self.fixCollision(s)

        # Prevents Mario from jumping midair
        if self.jumpCooldown == self.cooldownTime and self.velY == 0:
            self.jumpCooldown = 0

        # jumpCooldown timer
        if self.jumpCooldown < self.cooldownTime and self.velY == 0:
            self.jumpCooldown += 1

        # Stores position (collision rectification uses previous frame's position)
        self.prevX = self.rect.left
        self.prevY = self.rect.top

    # Fixes Mario-Tube collisions
    def fixCollision(self, sprite):
        # Corrects vertical tube collisions
        if self.prevY + self.rect.height < sprite.rect.top:
            self.rect.bottom = sprite.rect.top - 1
            self.velY = 0
        # If Mario is coming from the right
        elif self.prevX > sprite.rect.right:
            viewCorrect = self.rect.left  # Used to correct scrollVal

            self.rect.left = sprite.rect.right + 1

            viewCorrect -= self.rect.left
            self.model.scrollVal -= viewCorrect
        # If Mario is coming from the left
        else:
            viewCorrect = self.rect.left

            self.rect.right = sprite.rect.left - 1

            viewCorrect -= self.rect.left
            self.model.scrollVal -= viewCorrect

    # Shoots a fireball
    def fire(self):
        self.model.sprites.append(Fireball(self.model, self.rect.center, self.flip))


# Model class - Handles the things that happen
class Model:
    def __init__(self):
        self.ground = 525  # Vertical position of the ground
        self.scrollVal = 0  # Offset used in View to draw sprites (modified by Controller)
        self.mario = Mario(self, 250, 200)  # Mario is born

        # Populate sprites list
        self.sprites = []  # List of all sprites currently in game
        # Add Mario
        self.sprites.append(self.mario)
        # Add tubes
        self.sprites.append(Tube(100, 375))
        self.sprites.append(Tube(500, 460))
        self.sprites.append(Tube(800, 320))
        # Add goombas
        self.sprites.append(Goomba(self, 600, 525))

    def update(self):
        liveSprites = []    # Sprites not to be killed

        # Iterate through all sprites
        for s in self.sprites:
            if not s.kill:
                s.update()
                liveSprites.append(s)
        # Save new list of sprites
        self.sprites = liveSprites


# View class - Handles the things you look at
class View:
    def __init__(self, model):
        screen_size = (1280, 720)  # Starts the pygame screen
        self.screen = pygame.display.set_mode(screen_size)

        pygame.display.set_caption("Mario Bootleg")  # Adds a window title
        icon = pygame.image.load("mario_icon.png")
        pygame.display.set_icon(icon)  # Adds a little Mario icon to the top left

        # Stores reference to game Model
        self.model = model
        # Store ground value as specified in Model
        self.ground = self.model.ground

    def update(self):
        # Draws the background (light blue)
        self.screen.fill([0, 232, 252])

        # Draws the ground (brown)
        pygame.draw.rect(self.screen, (32, 176, 44),
                         pygame.Rect(0, self.ground, 1280, 720 - self.ground))

        # Draw all sprites
        for s in self.model.sprites:
            # Draw Mario and Goombas
            if isinstance(s.image, list):
                # Store image
                image = s.image[s.frame]

                # Mario is offset opposite compared to other sprites when drawn
                if isinstance(s, Mario):
                    self.screen.blit(pygame.transform.flip(image, s.flip, False),
                                     s.rect.move(-self.model.scrollVal, 0))
                else:
                    self.screen.blit(pygame.transform.flip(image, s.flip, False),
                                     s.rect.move(-self.model.scrollVal, 0))
            # Draw Tubes and Fireballs
            else:
                self.screen.blit(pygame.transform.flip(s.image, s.flip, False),
                                 s.rect.move(-self.model.scrollVal, 0))

        # Updates the display
        pygame.display.flip()


# Controller class - Handles the buttons you press
class Controller:
    def __init__(self, model):
        self.model = model  # Stores reference to game Model
        self.keep_going = True  # Keeps game-loop going

    def update(self):
        # Checks for attempts to close the game
        for event in pygame.event.get():
            if event.type == QUIT:
                self.keep_going = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.keep_going = False

        # Gets whatever keys were pressed
        keys = pygame.key.get_pressed()

        if keys[K_LEFT] and keys[K_RIGHT]:
            pass  # Intentionally empty!
        # Move Mario left
        elif keys[K_LEFT]:
            self.model.mario.rect.move_ip(-10, 0)
            # Update animation frame
            self.model.mario.frame += 1
            self.model.mario.frame %= 5

            # Adjust scroll offset
            self.model.scrollVal -= 10

            # Face Mario to the left
            self.model.mario.flip = True
        # Move Mario right
        elif keys[K_RIGHT]:
            self.model.mario.rect.move_ip(10, 0)
            # Update animation frame
            self.model.mario.frame += 1
            self.model.mario.frame %= 5

            # Adjust scroll offset
            self.model.scrollVal += 10

            # Face Mario to the right
            self.model.mario.flip = False

        # Mario jumps
        if keys[K_SPACE]:
            self.model.mario.jumping = True
        else:
            self.model.mario.jumping = False

        # Mario shoots a fireball
        if keys[K_f] and self.model.mario.fireReady:
            self.model.mario.fire()     # Shoots
            self.model.mario.fireReady = False  # Disables until key release
        elif not keys[K_f]:
            self.model.mario.fireReady = True   # Enables fireball action


# Tutorial
print("Please have fun.")
print("Left and right arrows for movement.")
print("Space to jump.")
print("\"F\" to shoot fireballs.")

pygame.init()  # Initializes pygame
m = Model()  # Initializes Model
v = View(m)  # Initializes View
c = Controller(m)  # Initializes Controller

# Main game loop
while c.keep_going:
    c.update()
    m.update()
    v.update()
    sleep(0.04)

# Prints after game is closed
print("Goodbye")
