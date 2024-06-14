import pygame
import sys
import random
from bus import Bus
from cartridge import Rom
from cpu import CPU

# Colors in 8bit
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

# Color mapping function
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

# Function to read the screen state from the CPU memory
def read_screen_state(cpu, screen_surface):
    update = False
    frame_idx = 0
    pixel_array = pygame.surfarray.pixels3d(screen_surface)
    try:
        for y in range(32):
            for x in range(32):
                addr = 0x0200 + y * 32 + x
                color_idx = cpu.mem_read(addr)
                b1, b2, b3 = color(color_idx)
                if (pixel_array[x, y] != (b1, b2, b3)).any():
                    pixel_array[x, y] = (b1, b2, b3)
                    update = True
                    print(f"Pixel updated at ({x}, {y}) with color ({b1}, {b2}, {b3})")
                frame_idx += 1
    except IndexError:
        print(f"Error reading screen state at index {frame_idx}")
    return update

# Function to handle user input
def handle_user_input(cpu, events):
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)
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
    pygame.display.set_caption("NES Emulator Test")
    clock = pygame.time.Clock()

    # Load the game ROM
    try:
        with open("snake.nes", "rb") as f:
            bytes = f.read()
        rom = Rom.new(bytes)
    except FileNotFoundError:
        print("The file snake.nes was not found.")
        return
    except ValueError as e:
        print(f"Failed to load ROM: {e}")
        return
    
    bus = Bus(rom)
    cpu = CPU(bus)
    cpu.reset()

    screen_surface = pygame.Surface((32, 32))

    running = True

    def cpu_step(cpu):
        # Add custom debugging or break conditions here if necessary
        pass

    # Game loop
    while running:
        events = pygame.event.get()
        handle_user_input(cpu, events)

        # Execute a single instruction using the CPU's run_with_callback method
        cpu.run_with_callback(cpu_step)
        
        cpu.mem_write(0xfe, random.randint(1, 15))
        print(f"Memory written: {cpu.mem_read(0xfe)}")

        # Read screen state from CPU memory and update the surface
        if read_screen_state(cpu, screen_surface):
            # Scale the 32x32 surface to 320x320 window
            scaled_surface = pygame.transform.scale(screen_surface, window.get_size())
            window.blit(scaled_surface, (0, 0))
            pygame.display.flip()
            print("Screen updated with CPU memory data")

        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

