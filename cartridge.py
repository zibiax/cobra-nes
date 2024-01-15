NES_TAG = b'NES\x1A'
PRG_ROM_PAGE_SIZE = 16384
CHR_ROM_PAGE_SIZE = 8192

class Mirroring:
    VERTICAL = 1
    HORIZONTAL = 2
    FOUR_SCREEN = 3


class Rom:
    def __init__(self, prg_rom, chr_rom, mapper, screen_mirroring):
        self.prg_rom = prg_rom
        self.chr_rom = chr_rom
        self.mapper = mapper
        self.screen_mirroring = screen_mirroring

    @staticmethod
    def new(raw):
        if raw[0:4] != NES_TAG:
            raise ValueError("File is not in iNES file format")

        mapper = (raw[7] & 0b1111_0000) | (raw[6] >> 4)
    
        ines_ver = (raw[7] >> 2) & 0b11
        if ines_ver != 0:
            raise ValueError("NES2.0 format is not supported")

        four_screen = raw[6] & 0b1000 != 0
        vertical_mirroring = raw[6] & 0b1 != 0
        if four_screen:
            screen_mirroring = Mirroring.FOUR_SCREEN
        elif vertical_mirroring:
            screen_mirroring = Mirroring.VERTICAL
        else:
            screen_mirroring = Mirroring.HORIZONTAL

        prg_rom_size = raw[4] * PRG_ROM_PAGE_SIZE
        chr_rom_size = raw[5] * CHR_ROM_PAGE_SIZE

        skip_trainer = raw[6] & 0b100 != 0
        prg_rom_start = 16 + (512 if skip_trainer else 0)
        chr_rom_start = prg_rom_start + prg_rom_size

        return Rom(
            prg_rom = raw[prg_rom_start:prg_rom_start + prg_rom_size],
            chr_rom = raw[chr_rom_start:chr_rom_start + chr_rom_size],
            mapper=mapper,
            screen_mirroring=screen_mirroring
            )


