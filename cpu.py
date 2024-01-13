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
            hi = (data >> 8) & 0xff
            lo = data & 0xff
            self.mem_write(pos, lo)
            self.mem_write(pos + 1, hi)

    def get_absolute_address(self, mode, addr):
        if mode == AddressingMode.ZeroPage:
            return self.mem_read(addr)

        if mode == AddressingMode.Absolute:
            return self.mem_read_u16(addr)

        if mode == AddressingMode.ZeroPage_X:
            pos = self.mem_read(addr)
            return (pos + self.register_x) & 0xff
            
        if mode == AddressingMode.ZeroPage_Y:
            pos = self.mem_read(addr)
            return (pos + self.register_y) & 0xff

        if mode == AddressingMode.Absolute_X:
            base = self.mem_read_u16(addr)
            return (base + self.register_x) & 0xFFFF

        if mode == AddressingMode.Absolute_Y:
            base = self.mem_read_u16(addr)
            return (base + self.register_y) & 0xFFFF

        if mode == AddressingMode.Indirect_X:
            base = self.mem_read(addr)
            ptr = (base + self.register_x) & 0xff
            lo = self.mem_read(ptr)
            hi = self.mem_read(ptr + 1) & 0xff
            return (hi << 8) | lo

        if mode == AddressingMode.Indirect_Y:
            base = self.mem_read(addr)
            lo = self.mem_read(base)
            hi = self.mem_read((base + 1) & 0xff)
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
        self.set_register_a(data & self.register_a)

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
        self.register_x = (self.register_x + 1) & 0xff
        self.update_zero_and_negative_flags(self.register_x)

    def iny(self):
        self.register_y = (self.register_y + 1) & 0xff
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
        carry = sum_ > 0xff

        if carry:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        result = sum_ & 0xff

        if ((data ^ result) & (result ^ self.register_a) & 0x80) != 0:
            self.status |= CpuFlags.OVERFLOW
        else:
            self.status &= ~CpuFlags.OVERFLOW

        self.set_register_a(result)

    def sbc(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        self.add_to_register_a((data ^ 0xff) + 1) & 0xff

    def adc(self, mode):
        addr = self.get_operand_address(mode)
        value = self.mem_read(addr)
        self.add_to_register_a(value)

    def stack_pop(self):
        self.stack_pointer = (self.stack_pointer + 1) & 0xff
        return self.mem_read(STACK + self.stack_pointer)

    def stack_push(self, data):
        self.mem_write(STACK + self.stack_pointer, data)
        self.stack_pointer = (self.stack_pointer - 1) & 0xff

    def stack_push_u16(self, data):
        hi = (data >> 8) & 0xff
        lo = data & 0xff
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

        self.register_a = (self.register_a << 1) & 0xff
        self.update_zero_and_negative_flags(self.register_a)

    def asl(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        if data & 0x80:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        data = (data << 1) & 0xff
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

    def rol(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        old_carry = self.status & CpuFlags.CARRY

        if data & 0x80:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        data = (data << 1) & 0xff
        if old_carry:
            data |= 0x01

        self.mem_write(addr, data)
        self.update_negative_flags(data)
        return data

    def rol_accumulator(self):
        old_carry = self.status & CpuFlags.CARRY

        if self.register_a & 0x80:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        self.register_a = (self.register_a << 1) & 0xff
        if old_carry:
            self.register_a |= 0x01
        self.update_zero_and_negative_flags(self.register_a)
    
    def ror(self, mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        old_carry = self.status & CpuFlags.CARRY

        if data & 1:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        data = (data >> 1) & 0xff
        if old_carry:
            data |= 0x80
        self.mem_write(addr, data)
        self.update_negative_flags(data)
        return data

    def ror_accumulator(self):
        data = self.register_a
        old_carry = self.status & CpuFlags.CARRY

        if data & 1:
            self.status |= CpuFlags.CARRY
        else:
            self.status &= ~CpuFlags.CARRY

        data = (data >> 1) & 0xff
        if old_carry:
            data |= 0x80
        self.set_register_a(data)

    def inc(self,mode):
        addr = self.get_operand_address(mode)
        data = self.mem_read(addr)
        data = (data + 1) & 0xff
        self.mem_write(addr, data)
        self.update_zero_and_negative_flags(data)
        return data

    def dey(self):
       self.register_y = (self.register_y - 1) & 0xff
       self.update_zero_and_negative_flags(self.register_y)

    def dex(self):
       self.register_x = (self.register_x - 1) & 0xff
       self.update_zero_and_negative_flags(self.register_x)

    def dec(self, mode):
       addr = self.get_operand_address(mode)
       data = self.mem_read(addr)
       data = (data - 1) & 0xff
       self.mem_write(addr, data)
       self.update_zero_and_negative_flags(data)
       return data

    def pla(self):
       data = self.stack_pop()
       self.set_register_a(data)

    def plp(self):
       self.status = self.stack_pop()
       self.status &= ~CpuFlags.BREAK
       self.status |= CpuFlags.BREAK2

    def php(self):
       flags = self.status
       flags |= CpuFlags.BREAK
       flags |= CpuFlags.BREAK2
       self.stack_push(flags)

    def bit(self, mode):
       addr = self.get_operand_address(mode)
       data = self.mem_read(addr)
       and_result = self.register_a & data

       if and_result == 0:
           self.status |= CpuFlags.ZERO
       else:
           self.status &= ~CpuFlags.ZERO

       if data & 0x80:
           self.status |= CpuFlags.NEGATIVE
       else:
           self.status &= ~CpuFlags.NEGATIVE

       if data & 0x40:
           self.status |= CpuFlags.OVERFLOW
       else:
           self.status &= ~CpuFlags.OVERFLOW

    def compare(self, mode, compare_with):
       addr = self.get_operand_address(mode)
       data = self.mem_read(addr)

       if data <= compare_with:
           self.status |= CpuFlags.CARRY
       else:
           self.status &= ~CpuFlags.CARRY

       self.update_zero_and_negative_flags(compare_with - data)

    def branch(self, condition):
       if condition:
           jump = self.mem_read(self.program_counter)
           jump_addr = (self.program_counter + 1 + jump) & 0xFFFF
           self.program_counter = jump_addr

    def run(self):
       # Assuming run_with_callback is defined elsewhere
       self.run_with_callback(lambda _: None)
    
    def run_with_callback(self, callback):
        opcodes = opcodes.OPCODES_MAP

        while True:
            code = self.mem_read(self.program_counter)
            self.program_counter += 1
            program_counter_state = self.program_counter

            opcode = opcodes.get(code)
            if opcode is None:
                raise ValueError(f"OpCode {hex(code)} is not recognized")

            match code:
                case 0xa9 | 0xa5 | 0xb5 | 0xad | 0xbd | 0xb9 | 0xa1 | 0xb1:
                    self.lda(opcode.mode)
                case 0xAA:
                    self.tax()
                case 0xe8:
                    self.inx()
                case 0x00:
                    return
                case 0xd8:
                    self.status.remove(CpuFlags.DECIMAL_MODE)
                case 0x58:
                    self.status.remove(CpuFlags.INTERRUPT_DISABLE)
                case 0xb8:
                    self.status.remove(CpuFlags.OVERFLOW)
                case 0x18:
                    self.clear_carry_flag()
                case 0x38:
                    self.set_carry_flag()
                case 0x78:
                    self.status.insert(CpuFlags.INTERRUPT_DISABLE)
                case 0xf8:
                    self.status.insert(CpuFlags.DECIMAL_MODE)
                case 0x48:
                    self.stack_push(self.register_a)
                case 0x68:
                    self.pla()
                case 0x08:
                    self.php()
                case 0x28:
                    self.plp()
                case 0x69 | 0x65 | 0x75 | 0x6d | 0x7d | 0x79 | 0x61 | 0x71:
                    self.adc(opcode.mode)
                case 0xe9 | 0xe5 | 0xf5 | 0xed | 0xfd | 0xf9 | 0xe1 | 0xf1:
                    self.sbc(opcode.mode)
                case 0x29 | 0x25 | 0x35 | 0x2d | 0x3d | 0x39 | 0x21 | 0x31:
                    self.and_(opcode.mode)
                case 0x49 | 0x45 | 0x55 | 0x4d | 0x5d | 0x59 | 0x41 | 0x51:
                    self.eor(opcode.mode)
                case 0x09 | 0x05 | 0x15 | 0x0d | 0x1d | 0x19 | 0x01 | 0x11:
                    self.ora(opcode.mode)
                case 0x4a:
                    self.lsr_accumulator()
                case 0x46 | 0x56 | 0x4e | 0x5e:
                    self.lsr(opcode.mode)
                case 0x0a:
                    self.asl_accumulator()
                case 0x06 | 0x16 | 0x0e | 0x1e:
                    self.asl(opcode.mode)
                case 0x2a:
                    self.rol_accumulator()
                case 0x26 | 0x36 | 0x2e | 0x3e:
                    self.rol(opcode.mode)
                case 0x6a:
                    self.ror_accumulator()
                case 0x66 | 0x76 | 0x6e | 0x7e:
                    self.ror(opcode.mode)
                case 0xe6 | 0xf6 | 0xee | 0xfe:
                    self.inc(opcode.mode)
                case 0xc8:
                    self.iny()
                case 0xc6 | 0xd6 | 0xce | 0xde:
                    self.dec(opcode.mode)
                case 0xca:
                    self.dex()
                case 0x88:
                    self.dey()
                case 0xc9 | 0xc5 | 0xd5 | 0xcd | 0xdd | 0xd9 | 0xc1 | 0xd1:
                    self.compare(opcode.mode, self.register_a)
                case 0xc0 | 0xc4 | 0xcc:
                    self.compare(opcode.mode, self.register_y)
                case 0xe0 | 0xe4 | 0xec:
                    self.compare(opcode.mode, self.register_x)
                case 0x4c:
                    mem_address = self.mem_read_u16(self.program_counter)
                    self.program_counter = mem_address
                case 0x6c:
                    mem_address = self.mem_read_u16(self.program_counter)
                    indirect_ref = self.mem_read_u16(mem_address)
                    self.program_counter = indirect_ref
                case 0x20:
                    self.stack_push_u16(self.program_counter + 2 - 1)
                    target_address = self.mem_read_u16(self.program_counter)
                    self.program_counter = target_address
                case 0x60:
                    self.program_counter = self.stack_pop_u16() + 1
                case 0x40:
                    self.status.bits = self.stack_pop()
                    self.status.remove(CpuFlags.BREAK)
                    self.status.insert(CpuFlags.BREAK2)
                    self.program_counter = self.stack_pop_u16()
                case 0xd0:
                    self.branch(not self.status.contains(CpuFlags.ZERO))
                case 0x70:
                    self.branch(self.status.contains(CpuFlags.OVERFLOW))
                case 0x50:
                    self.branch(not self.status.contains(CpuFlags.OVERFLOW))
                case 0x10:
                    self.branch(not self.status.contains(CpuFlags.NEGATIVE))
                case 0x30:
                    self.branch(self.status.contains(CpuFlags.NEGATIVE))
                case 0xf0:
                    self.branch(self.status.contains(CpuFlags.ZERO))
                case 0xb0:
                    self.branch(self.status.contains(CpuFlags.CARRY))
                case 0x90:
                    self.branch(not self.status.contains(CpuFlags.CARRY))
                case 0x24 | 0x2c:
                    self.bit(opcode.mode)
                case 0x85 | 0x95 | 0x8d | 0x9d | 0x99 | 0x81 | 0x91:
                    self.sta(opcode.mode)
                case 0x86 | 0x96 | 0x8e:
                    addr = self.get_operand_address(opcode.mode)
                    self.mem_write(addr, self.register_x)
                case 0x84 | 0x94 | 0x8c:
                    addr = self.get_operand_address(opcode.mode)
                    self.mem_write(addr, self.register_y)
                case 0xa2 | 0xa6 | 0xb6 | 0xae | 0xbe:
                    self.ldx(opcode.mode)
                case 0xa0 | 0xa4 | 0xb4 | 0xac | 0xbc:
                    self.ldy(opcode.mode)
                case 0xa8:
                    self.register_y = self.register_a
                    self.update_zero_and_negative_flags(self.register_y)
                case 0xba:
                    self.register_x = self.stack_pointer
                    self.update_zero_and_negative_flags(self.register_x)
                case 0x8a:
                    self.register_a = self.register_x
                    self.update_zero_and_negative_flags(self.register_a)
                case 0x9a:
                    self.stack_pointer = self.register_x
                case 0x98:
                    self.register_a = self.register_y
                    self.update_zero_and_negative_flags(self.register_a)
                case _:
                    raise ValueError(f"OpCode {hex(code)} is not recognized")

            if program_counter_state == self.program_counter:
                self.program_counter += (opcode.len - 1)

            callback(self)

