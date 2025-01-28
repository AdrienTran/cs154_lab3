import pyrtl
import pyrtl.simulation

# ucsbcs154lab3
# All Rights Reserved
# Copyright (c) 2023 Regents of the University of California
# Distribution Prohibited


# Initialize your memblocks here: 
i_mem = pyrtl.MemBlock(bitwidth=32, addrwidth=36, name='i_mem')
d_mem = pyrtl.MemBlock(bitwidth=32, addrwidth=36, name='d_mem', asynchronous=True)
rf    = pyrtl.MemBlock(bitwidth=32, addrwidth=36, name='rf', asynchronous=True)

# When working on large designs, such as this CPU implementation, it is
# useful to partition your design into smaller, reusable, hardware
# blocks. We have indicated where you should put different hardware blocks 
# to help you get write your CPU design. You have already worked on some 
# parts of this logic in prior labs, like the decoder and alu.

## DECODER
# decode the instruction
PC = pyrtl.Register(bitwidth=32)

data = pyrtl.WireVector(bitwidth=32, name='data')
data <<= i_mem[PC]

op = pyrtl.WireVector(bitwidth=6, name='op')
rs = pyrtl.WireVector(bitwidth=5, name='rs')
rt = pyrtl.WireVector(bitwidth=5, name='rt')
rd = pyrtl.WireVector(bitwidth=5, name='rd')
sh = pyrtl.WireVector(bitwidth=5, name='sh')
func = pyrtl.WireVector(bitwidth=6, name='func')
imm = pyrtl.WireVector(bitwidth=16, name='imm')
addr = pyrtl.WireVector(bitwidth=26, name='addr')

imm_se = imm.sign_extended(32)
imm_ze = imm.zero_extended(32)

op <<= data[26:32]
rs <<= data[21:26]
rt <<= data[16:21]
rd <<= data[11:16]
sh <<= data[6:11]
func <<= data[0:6]
imm <<= data[0:16]
addr <<= data[0:26]

## CONTROLLER
# define control signals for the following instructions
# add, and, addi, lui, ori, slt, lw, sw, beq
control_signals = pyrtl.WireVector(bitwidth=10, name='control_signals')
with pyrtl.conditional_assignment:
   with op == 0:
      with func == 0x20: #add
         control_signals |= 0x280
      with func == 0x24: #and
         control_signals |= 0x281
      with func == 0x2a: #slt
         control_signals |= 0x284
   with op == 0x8: #addi
      control_signals |= 0x140
   with op == 0xf: #lui
      control_signals |= 0x182
   with op == 0xd: #ori
      control_signals |= 0x183
   with op == 0x23: #lw
      control_signals |= 0x148
   with op == 0x2b: #sw
      control_signals |= 0x60
   with op == 0x4: #beq
      control_signals |= 0x105
   
reg_dst = control_signals[9:10]
mem_to_reg = control_signals[3:4]

## WRITE REGISTER mux
# create the mux to choose among rd and rt for the write register
reg_write = pyrtl.WireVector(bitwidth=1, name='reg_write')
with pyrtl.conditional_assignment:
   with control_signals == 0x60:
      reg_write |= 0
   with control_signals == 0x105:
      reg_write |= 0
   with pyrtl.conditional.otherwise:
      reg_write |= 1

## READ REGISTER VALUES from the register file
# read the values of rs and rt registers from the register file
data1 = rf[rs]
data2 = rf[rt]

## ALU INPUTS
# define the ALU inputs after reading values of rs and rt registers from
# the register file
# Hint: Think about ALU inputs for instructions that use immediate values 
input1 = data1
input2 = data2
with pyrtl.conditional_assignment:
   with reg_dst == 0:
      with control_signals == 0x183:
         input2 = imm_ze
      with pyrtl.conditional.otherwise:
        input2 = imm_se
      
      
## FIND ALU OUTPUT
# find what the ALU outputs are for the following instructions:
# add, and, addi, lui, ori, slt, lw, sw, beq
# Hint: you want to find both ALU result and zero. Refer the figure in the
# lab document
alu_out = pyrtl.WireVector(bitwidth=32, name='alu_out')
zero = pyrtl.WireVector(bitwidth=32, name='zero')

with pyrtl.conditional_assignment:
    with control_signals == 0x280: #add
        alu_out |= input1 + input2
    with control_signals == 0x281: #and
        alu_out |= input1 & input2
    with control_signals == 0x140: #addi
        alu_out |= input1 + input2
    with control_signals == 0x182: #lui
        alu_out |= pyrtl.corecircuits.shift_left_logical(input2, pyrtl.Const(16))
    with control_signals == 0x183: #ori
        alu_out |= input1 | input2
    with control_signals == 0x284: #slt
        alu_out |= pyrtl.corecircuits.signed_lt(input1, input2)
    with control_signals == 0x148: #lw
        alu_out |= d_mem[input1 + input2]
    with control_signals == 0x60: #sw
        alu_out |= data2
    with control_signals == 0x105: #beq
        alu_out |= input1 - data2
        with alu_out == 0:
            zero |= 1
        with pyrtl.conditional.otherwise:
            zero |= 0

## DATA MEMORY WRITE
# perform the write operation in the data memory. Think about which 
# instructions will need to write to the data memory
with pyrtl.conditional_assignment:
   with control_signals == 0x60:
      d_mem[input1 + input2] |= data2

## REGISTER WRITEBACK
# Create the mux to select between ALU result and data memory read.
# Writeback the selected value to the register file in the 
# appropriate write register 
with pyrtl.conditional_assignment:
   with reg_write == 1:
      with reg_dst == 1:
         rf[rd] |= alu_out
      with reg_dst == 0:
         rf[rt] |= alu_out
      
## PC UPDATE
# finally update the program counter. Pay special attention when updating 
# the PC in the case of a branch instruction. 

nextPC = pyrtl.WireVector(bitwidth=32, name="nextPC")
with pyrtl.conditional_assignment:
   with zero == 1:
      nextPC |= PC + 1 + imm_se
      print("zero: ", nextPC)
   with zero == 0:
      nextPC |= PC + 1
    #   print("zero: ", nextPC)
PC.next <<= nextPC

# PC.next <<= PC + 1

if __name__ == '__main__':

    """

    Here is how you can test your code.
    This is very similar to how the autograder will test your code too.

    1. Write a MIPS program. It can do anything as long as it tests the
       instructions you want to test.

    2. Assemble your MIPS program to convert it to machine code. Save
       this machine code to the "i_mem_init.txt" file. You can use the 
       "mips_to_hex.sh" file provided to assemble your MIPS program to 
       corresponding hexadecimal instructions.  
       You do NOT want to use QtSPIM for this because QtSPIM sometimes
       assembles with errors. Another assembler you can use is the following:

       https://alanhogan.com/asu/assembler.php

    3. Initialize your i_mem (instruction memory).

    4. Run your simulation for N cycles. Your program may run for an unknown
       number of cycles, so you may want to pick a large number for N so you
       can be sure that all instructions of the program are executed.

    5. Test the values in the register file and memory to make sure they are
       what you expect them to be.

    6. (Optional) Debug. If your code didn't produce the values you thought
       they should, then you may want to call sim.render_trace() on a small
       number of cycles to see what's wrong. You can also inspect the memory
       and register file after every cycle if you wish.

    Some debugging tips:

        - Make sure your assembly program does what you think it does! You
          might want to run it in a simulator somewhere else (SPIM, etc)
          before debugging your PyRTL code.

        - Test incrementally. If your code doesn't work on the first try,
          test each instruction one at a time.

        - Make use of the render_trace() functionality. You can use this to
          print all named wires and registers, which is extremely helpful
          for knowing when values are wrong.

        - Test only a few cycles at a time. This way, you don't have a huge
          500 cycle trace to go through!

    """

    # Start a simulation trace
    sim_trace = pyrtl.SimulationTrace()

    # Initialize the i_mem with your instructions.
    i_mem_init = {}
    with open('i_mem_init.txt', 'r') as fin:
        i = 0
        for line in fin.readlines():
            i_mem_init[i] = int(line, 16)
            i += 1

    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
        i_mem : i_mem_init
    })

    
    # Run for an arbitrarily large number of cycles.
    for cycle in range(500):
        # print(nextPC)
        sim.step({})
        # print(PC.data)

    # Use render_trace() to debug if your code doesn't work.
    # sim_trace.render_trace()

    # You can also print out the register file or memory like so if you want to debug:
    # print(sim.inspect_mem(i_mem))
    # print(sim.inspect_mem(d_mem))
    # print(sim.inspect_mem(rf))

    # Perform some sanity checks to see if your program worked correctly
    assert(sim.inspect_mem(d_mem)[0] == 10)
    assert(sim.inspect_mem(rf)[8] == 10)    # $v0 = rf[8]
    print('Passed!')