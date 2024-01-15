NES_TAG = [0x4E, 0x45, 0x53, 0x1A]
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

# Test functions
def create_rom(test_rom):
    result = []
    result.extend(test_rom['header'])
    if test_rom.get('trainer'):
        result.extend(test_rom['trainer'])
    result.extend(test_rom['pgp_rom'])
    result.extend(test_rom['chr_rom'])
    return result

def test_rom():
    test_rom_data = create_rom({
        'header': [0x4E, 0x45, 0x53, 0x1A, 0x02, 0x01, 0x31, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'trainer': None,
        'pgp_rom': [1] * (2 * PRG_ROM_PAGE_SIZE),
        'chr_rom': [2] * (1 * CHR_ROM_PAGE_SIZE),
    })
    return Rom.new(test_rom_data)

# Example usage
rom = test_rom()
print(rom.prg_rom)
print(rom.chr_rom)
print(rom.mapper)
print(rom.screen_mirroring)
