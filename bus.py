from cpu import CPU  # Importing the CPU class which contains Mem functions

RAM = 0x0000
RAM_MIRRORS_END = 0x1FFF
PPU_REGISTERS = 0x2000
PPU_REGISTERS_MIRRORS_END = 0x3FFF

class Bus:
    def __init__(self, rom):
        self.cpu_vram = [0] * 2048
        self.rom = rom

    def read_prg_rom(self, addr):
        addr -= 0x8000
        if len(self.rom.prg_rom) == 0x4000 and addr >= 0x4000:
            # Mirror if needed
            addr %= 0x4000
        return self.rom.prg_rom[addr]

    def mem_read(self, addr):
        if RAM <= addr <= RAM_MIRRORS_END:
            mirror_down_addr = addr & 0b00000111_11111111
            return self.cpu_vram[mirror_down_addr]
        elif PPU_REGISTERS <= addr <= PPU_REGISTERS_MIRRORS_END:
            mirror_down_addr = addr & 0b00100000_00000111
            # PPU is not supported yet
            raise NotImplementedError("PPU is not supported yet")
        elif 0x8000 <= addr <= 0xFFFF:
            return self.read_prg_rom(addr)
        else:
            print(f"Ignoring mem access at {addr}")
            return 0

    def mem_write(self, addr, data):
        if RAM <= addr <= RAM_MIRRORS_END:
            mirror_down_addr = addr & 0b11111111111
            self.cpu_vram[mirror_down_addr] = data
        elif PPU_REGISTERS <= addr <= PPU_REGISTERS_MIRRORS_END:
            mirror_down_addr = addr & 0b00100000_00000111
            # PPU is not supported yet
            raise NotImplementedError("PPU is not supported yet")
        elif 0x8000 <= addr <= 0xFFFF:
            raise Exception("Attempt to write to Cartridge ROM space")
        else:
            print(f"Ignoring mem write-access at {addr}")
