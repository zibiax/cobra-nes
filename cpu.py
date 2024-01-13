from enum import IntFlag, auto, Enum
from typing import List, Tuple

class CpuFlags(IntFlag):
    CARRY = auto()
    ZERO = auto()
    INTERRUPT_DISABLE = auto()
    DECIMAL_MODE = auto()
    BREAK = auto()
    BREAK2 = auto()
    OVERFLOW = auto()
    NEGATIVE = auto()

STACK = 0x0100
STACK_RESET = 0xfd

class AddressingMode(Enum):
        Immediate = auto()
        ZeroPage = auto()
        ZeroPage_X = auto()
        ZeroPage_Y = auto()
        Absolute = auto()
        Absolute_X = auto()
        Absolute_Y = auto()
        Indirect_X = auto()
        Indirect_Y = auto()
        NoneAddressing = auto()

class CPU:
    def __init__(self, bus):
        self.register_a = 0
        self.register_x = 0
        self.register_y = 0
        self.status = CpuFlags(0b100100)
        self.program_counter = 0
        self.stack_pointer = STACK_RESET
        self.bus = bus

    def mem_read(self, addr):
            return self.bus.mem_read(addr)
        
    def mem_write(self, addr, data):
            return self.bus.mem_write(addr, data)

    def mem_read_u16(self, pos):
            lo = self.mem_read(pos)
            hi = self.mem_read(pos + 1)
            return (hi << 8) | lo

    def mem_write_u16(self, pos, data):
            hi = (data >> 8) & 0xFF
            lo = data & 0xFF
            self.mem_write(pos, lo)
            self.mem_write(pos + 1, hi)

    def get_absolute_address(self, mode, addr):
        if mode == AddressingMode.ZeroPage:
            return self.mem_read(addr)

        if mode == AddressingMode.Absolute:
            return self.mem_read_u16(addr)

        if mode == AddressingMode.ZeroPage_X:
            pos = self.mem_read(addr)
            return (pos + self.register_x) & 0xFF
            
        if mode == AddressingMode.ZeroPage_Y:
            pos = self.mem_read(addr)
            return (pos + self.register_y) & 0xFF

        if mode == AddressingMode.Absolute_X:
            base = self.mem_read_u16(addr)
            return (base + self.register_x) & 0xFFFF

        if mode == AddressingMode.Absolute_Y:
            base = self.mem_read_u16(addr)
            return (base + self.register_y) & 0xFFFF

        if mode == AddressingMode.Indirect_X:
            base = self.mem_read(addr)
            ptr = (base + self.register_x) 0xFF
            lo = self.mem_read(ptr)
            hi = self.mem_read(ptr +1) & 0xFF)
            return (hi << 8) | lo

        if mode == AddressingMode.Indirect_Y:
            base = self.mem_read(addr)
            lo = self.mem_read(base)
            hi = self.mem_read((base + 1) & 0xFF)
            deref_base = (hi << 8) | lo
            return (deref_base + self.register_y) & 0xFFFF

        raise ValueError(f"Mode {mode} is not supported")

    def get_operand_address(self, mode):
        if mode == AddressingMode.Immediate:
            return self.program_counter
        else:
            return self.get_absolute_address(mode, self.program_counter)

    def ldy(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        self.register_y = data
        self.update_zero_and_negative_flags(self.register_y)

    def ldx(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        self.register_x = data
        self.update_zero_and_negative_flags(self.register_x)

    def lda(self, mode):
        addr = self.get_operand_address(mode)
        value = self.mem_read(addr)
        self.set_register_a(value)

    def sta(self, mode):
        addr = self.get_operand_address(mode)
        self.mem_write(addr, self.register_a)

    def set_register_a(self, value):
        self.register_a = value
        self.update_zero_and_negative_flags(self.register_a)

    def and_(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        self.set_register(data & self.register_a)

    def eor(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        self.set_register_a(data ^ self.register_a)

    def ora(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        self.set_register_a(data | self. register_a)

    def tax(self):
        self.register_x = self.register_a
        self.update_zero_and_negative_flags(self.register_x)

    def update_zero_and_negative_flags(self, result):
        if result == 0:
            self.status |= CpuFlags.ZERO
        else:
            self.status &= ~CpuFlags.ZERO

        if result >> 7 == 1:
            self.status |= CpuFlags.NEGATIVE

        else:
            self.status &= ~CpuFlags.NEGATIVE

    def update_negative_flags(self, result):
        if result >> 7 == 1:
            self.status |= CpuFlags.ZERO
        else:
            self.status &= ~CpuFlags.NEGATIVE

    def inx(self):
        self.register_x = (self.register_x + 1) & 0xFF
        self.update_zero_and_negative_flags(self.register_x)

    def iny(self):
        self.register_y = (self.register_y + 1) & 0xFF
        self.update_zero_and_negative_flags(self.register_y)

    def load_and_run(self, program):
        self.load(program)
        self.reset()
        self.run()

    def load(self, program):
        for i, byte in enumerate(program):
            self.mem_write(0x8600 + i, byte)
        self.mem_write_u16(0xFFFC, 0x8600)

    def reset(self):
        self.register_a = 0
        self.register_x = 0
        self.register_y = 0
        self.stack_pointer = STACK_RESET
        self.status = CpuFlags.ZERO | CpuFlags.BREAK2
        self.program_counter = self.mem_read_u16(0xFFFC)

    def set_carry_flag(self):
        self.status |= CpuFlags.CARRY
    
    def clear_carry_flag(self):
        self.status &= ~CpuFlags.CARRY

    def add_to_register_a(self, data):
        sum_ = self.register_a + (1 if self.status & CpuFlags.CARRY else 0)
        carry = sum_ > 0xFF

        if carry:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        result = sum_ & 0xFF

        if ((data ^ result) & (result ^ self.register_a) & 0x80) != 0:
            self.status |= CpuFlags.OVERFLOW
        else:
            self.status &= ~CpuFlags.OVERFLOW

        self.set_register_a(result)

    def sbc(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        self.add_to_register_a(data ^ 0xFF) + 1) & 0xFF)

    def adc(self, mode):
        addr = self.get_operand_address(mode)
        value = self.mem_read(addr)
        self.add_to_register_a(value)

    def stack_pop(self):
        self.stack_pointer = (self.stack_pointer + 1) & 0xFF
        return self.mem_read(STACK + self.stack_pointer)

    def stack_push(self, data):
        self.mem_write(STACK + self.stack_pointer, data)
        self.stack_pointer = (self.stack_pointer - 1) & 0xFF

    def stack_push_u16(self, data):
        hi = (data >> 8) & 0xFF
        lo = data & 0xFF
        self.stack_push(hi)
        self.stack_push(lo)

    def stack_pop_u16(self):
        lo = self.stack_pop()
        hi = self.stack_pop()
        return hi << 8 | lo

    def asl_accumulator(self):
        if self.register_a & 0x80:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        self.register_a = (self.register_a << 1) & 0xFF
        self.update_zero_and_negative_flags(self.register_a)

    def asl(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        if data & 0x80:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        data = (data << 1) & 0xFF
        self.mem_write(addr, data)
        self.update_zero_and_negative_flags(data)
        return data

    def lsr_accumulator(self):
        if self.register_a & 0x01:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        self.register_a = self.register_a << 1
        self.update_zero_and_negative_flags(self.register_a)

    def lsr(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        if data & 0x01:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        data = data >> 1
        self.mem_write(addr, data)
        self.update_zero_and_negative_flags(data)
        return data

    fn rol(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        old_carry = self.status & CpuFlags.CARRY

        if data & 0x80:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        data = (data << 1) & 0xFF
        if old_carry:
            data |= 0x01

        self.mem_write(addr, data)
        self.update_negative_flags(data)
        return data

    rol_accumulator(self):
        old_carry = self.status & CpuFlags.CARRY

        if self.register_a & 0x80:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        self.register_a = (self.register_a << 1) & 0xFF
        if old_carry:
            self.register_a |= 0x01
        self.update_zero_and_negative_flags(self.register_a)
        

