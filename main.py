import pygame
import random # Import random module 
from setting import SETTING # Import game setting 
from classes.player import Player # Import player from the player class
from classes.platform import Platform # Import platform from the platform class
from classes.camera import Camera # Import Camera
from classes.ui import UI # Import UI
from classes.enemy import Enemy # Import enemy from the enemy class

# Initialize game
pygame.init()

# Create game window
screen = pygame.display.setmode((SETTING["WIDTH"], SETTING["HEIGHT"]))
pygame.display.set_caption(SETTING["TITLE"])


pygame.quit()