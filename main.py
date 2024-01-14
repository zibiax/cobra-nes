import pygame
from pygame.locals import QUIT, KEYDOWN
import sys
import random
# from bus import Bus
#from cartridge import Rom
from cpu import CPU
from opcodes import *
from trace import *


# Colors in 8bit
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (128, 128, 128)
RED = (255, 0 , 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

# Color mapping
def color(byte):
    return {
            0: BLACK,
            1: WHITE,
            2: GREY,
            9: GREY,
            3: RED,
            10: RED,
            4: GREEN,
            11: GREEN,
            5: BLUE,
            12: BLUE,
            6: MAGENTA,
            13: MAGENTA,
            7: YELLOW,
            14: YELLOW,
            }.get(byte, CYAN)

# read screen state function
def read_screen_state(cpu, frame):
    update = False
    frame_idx = 0
    for i in range(0x0200, 0x600):
        color_idx = cpu.mem_read(i)
        b1, b2, b3 = color(color_idx)
        if frame[frame_idx] != b1 or frame[frame_idx + 1] != b2 or frame[frame_idx + 2] != b3:
            frame[frame_idx] = b1
            frame[frame_idx + 1] = b2
            frame[frame_idx + 2] = b3
            update = True
        frame_idx += 3
    return update

# handle user input
def handle_user_input(cpu, events):
    if event in events:
        if event.type == QUIT:
            pygame.quit()
            sys.exit(0)
        elif event.type == KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys,exit(0)
            elif event.key == pygame.K_w:
                cpu.mem_write(0xff, ord('w'))
            elif event.key == pygame.K_s:
                cpu.mem_write(0xff, ord('s'))
            elif event.key == pygame.K_a:
                cpu.mem_write(0xff, ord('a'))
            elif event.key == pygame.K_d:
                cpu.mem_write(0xff, ord('d'))

def main():
    pygame.init()
    window = pygame.display.set_mode((320, 320))
    pygame.display.set_caption("Snake Game")
    clock = pygame.time.Clock()

    # load game function
    with open("snake.nes", "rb") as f:
        bytes = f.read()
    rom = Rom(bytes)
    bus = Bus(rom)
    cpu = CPU(bus)
    cpu.reset()

    screen_state = [0] * (32 * 3 * 32)
    running = True

    # game loop
    while running:
        events = pygame.event.get()
        handle_user_input(cpu, events)

        cpu.mem_write(0xfe, random.randint(1, 15))

        if read_screen_state(cpu, screen_state):
            # update the display with new screen state
            pygame.surfarray.blit_array(window, screen_state)

        pygame.display.flip()
        clock.tick(60)
        pygame.time.delay(70)

    pygame.quit()

if __name__ == "__main__":
    main()
