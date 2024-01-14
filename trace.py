from cpu import AddressingMode
from cpu import CPU
from opcodes import OpCode, CPU_OPS_CODES

def trace(cpu: CPU) -> str:
    opcodes = CPU_OPS_CODES
    code = cpu.mem_read(cpu.program_counter)
    ops = opcodes.get(code)
    if ops is None:
        raise ValueError(f"Unknown opcode {code}")
    begin = cpu.program_counter
    hex_dump = [code]
    match ops.mode:
        case AddressingMode.Immediate | AddressingMode.NoneAddressing:
            mem_addr, stored_value = 0, 0
        case _:
            addr = cpu.get_absolute_address(ops.mode, begin + 1)
            mem_addr, stored_value = addr, cpu.mem_read(addr)

    tmp = ""
    match ops.len:
        case 1:
            match ops.code:
                case 0x0a | 0x4a | 0x2a | 0x6a:
                    tmp = "A "
        case 2:
            address = cpu.mem_read(begin + 1)
            hex_dump.append(address)
            match ops.mode:
                case AddressingMode.Immediate:
                    tmp = f"#${address:02X}"
                case AddressingMode.ZeroPage:
                    tmp = f"${mem_addr:02X} = {stored_value:02X}"
                case AddressingMode.ZeroPage_X:
                    tmp = f"${address:02X},X @ ${mem_addr:02X} = {stored_value:02X}"
                case AddressingMode.ZeroPage_Y:
                    tmp = f"${address:02X},Y @ ${mem_addr:02X} = {stored_value:02X}"
                case AddressingMode.Indirect_X:
                    tmp = f"(${address:02X},X) @ ${(address + cpu.register_x):02X} = {mem_addr:04X} = {stored_value:02X}"
                case AddressingMode.Indirect_Y:
                    tmp = f"(${address:02X}),Y = ${mem_addr - cpu.register_y:04X} @ ${mem_addr:04X} = {stored_value:02X}"
                case AddressingMode.NoneAddressing:
                    address = (begin + 2) + address
                    tmp = f"${address:04X}"
                case _:
                    raise Exception(f"Unexpected addressing mode {ops.mode} has ops-len 2. code {ops.code:02X}")
        case 3:
            address_lo = cpu.mem_read(begin + 1)
            address_hi = cpu.mem_read(begin + 2)
            hex_dump.extend([address_lo, address_hi])
            address = cpu.mem_read_u16(begin + 1)
            match ops.mode:
                case AddressingMode.NoneAddressing:
                    if ops.code == 0x6c:
                        jmp_addr = cpu.mem_read_u16(address)
                        tmp = f"(${address:04X}) = ${jmp_addr:04X}"
                    else:
                        tmp = f"${address:04X}"
                case AddressingMode.Absolute:
                    tmp = f"${mem_addr:04X} = {stored_value:02X}"
                case AddressingMode.Absolute_X:
                    tmp = f"${address:04X},X @ ${mem_addr:04X} = {stored_value:02X}"
                case AddressingMode.Absolute_Y:
                    tmp = f"${address:04X},Y @ ${mem_addr:04X} = {stored_value:02X}"
                case _:
                    raise Exception(f"Unexpected addressing mode {ops.mode} has ops-len 3. code {ops.code:02X}")
        case _:
            pass  # Handle other cases or do nothing

    hex_str = ' '.join(f"{byte:02X}" for byte in hex_dump)
    asm_str = f"{begin:04X} {hex_str:8} {ops.mnemonic:>4} {tmp}".strip()

    return f"{asm_str:47} A:{cpu.register_a:02X} X:{cpu.register_x:02X} Y:{cpu.register_y:02X} P:{cpu.status:02X} SP:{cpu.stack_pointer:02X}".upper()


