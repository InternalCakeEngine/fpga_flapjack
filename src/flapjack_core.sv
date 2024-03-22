`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 16.03.2024 20:01:21
// Design Name: 
// Module Name: flapjack_core
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module flapjack_core(
        input  wire  logic   clk_sys,           // 125 MHz system clock
        input  wire  logic   reset,             // Reset when high.
        output       logic   [6:0] char_x,      // Write location x
        output       logic   [5:0] char_y,      // Write location y
        output       logic   [8:0] char_chr,    // Write character
        output       logic   char_str           // Write strobe.
    );
    
    // Super simple output device that should really be somewhere else.
    logic [8:0] write_x = 0;
    logic [8:0] write_y = 0;
    logic [8:0] out_char = 0;
    logic out_char_strobe = 0;
        
    // Build a ticker at a reasonable rate (1ms).
    localparam TICK_MINOR_LIMIT = 125_000;
    localparam TICK_MINOR_WIDTH = $clog2(TICK_MINOR_LIMIT);
    logic [TICK_MINOR_WIDTH-1:0] tick_minor = 0;
    localparam TICK_MAJOR_WIDTH = 32;
    logic [TICK_MAJOR_WIDTH-1:0] tick_major = 0;
    always_ff @(posedge clk_sys) begin
        if( tick_minor == TICK_MINOR_LIMIT-1 ) begin
            tick_minor <= 0;
            tick_major += 1;
        end else begin
            tick_minor += 1;
        end
    end
    
    // Give ourselves some memory.
    localparam MEM_WIDTH = 16;
    localparam MEM_EXTENT = 65536;
    localparam MEM_ADDRW = $clog2(MEM_EXTENT);
    localparam MEM_INITIAL = "boot.mem";
    logic [MEM_ADDRW-1:0] mem_addr_read;
    logic [MEM_WIDTH-1:0] mem_word_read;
    logic [MEM_ADDRW-1:0] mem_addr_write;
    logic [MEM_WIDTH-1:0] mem_word_write;
    logic mem_strobe = 0;
    bram_sdp #(
        .WIDTH(MEM_WIDTH),
        .DEPTH(MEM_EXTENT),
        .INIT_F(MEM_INITIAL)
    ) bram_memory (
        .clk_write(clk_sys),
        .clk_read(clk_sys),
        .we(mem_strobe),
        .addr_write(mem_addr_write),
        .addr_read(mem_addr_read),
        .data_in(mem_word_write),
        .data_out(mem_word_read)
    );
    
    
    localparam REGWIDTH = 16;
    localparam REGCOUNT = 16;
    logic [REGWIDTH-1:0] regs[REGCOUNT];
    localparam REG_IP = 15;
    localparam REG_FLAGS = 13;

    // Give opcodes names
    localparam OP_NOP = 0;
    localparam OP_JP = 1;
    localparam OP_BR = 2;
    localparam OP_LD = 3;
    localparam OP_ST = 4;
    localparam OP_ADD = 5;
    localparam OP_SUB = 6;
    localparam OP_CMP = 7;
    localparam OP_OUT = 8;
    localparam OP_CONST = 9;
    localparam OP_AND = 10;
    localparam OP_MOV = 11;
    localparam OP_SHR = 12;
    
    // Set of states for the core.
    enum {
        HALT,                   // Stop, permanently.
        RESET,                  // Do nothing but reset the IP.
        IFETCH_SETUP,           // Fetch IP from the register file and the flags.
        IFETCH_READ_SETUP,      // Start memory fetch for an instruction.
        IFETCH_READ,            // Read the instruction, and setup op fetching.
        DECODE,                 // Read the op values, condition and decide what to do with the opcode.
        DO_JP,                  // Do the work of jumping.
        DO_LD_1,                // Loading from memory: setup the memory read address.
        DO_LD_2,                // Loading from memory: transfer from memory result to register.
        DO_ST,                  // Storing to memory.
        DO_CMP,                 // Do the compare and set the flags.
        DO_OUT,                 // Poke device.
        DO_CONST,               // Transfer bits from the instruction.
        DO_ADD,                 // Arith.
        DO_AND,                 // Arith.
        DO_MOV,                 // Arith.
        DO_SHR,                 // Arith.
        STEP                    // Move to the next instr (for non-branching).
    } core_state=RESET;
    
    // Decoding parts.
    logic [15:0] instr;
    logic [15:0] ro_flags;
    logic [3:0] raw_opcode;
    logic [3:0] raw_op1;
    logic [3:0] raw_op2;
    logic [3:0] raw_cond;
    logic [15:0] op1;
    logic [15:0] op2;
    logic condtrue;
    logic opmode;
    logic [15:0] ip_current;
    
    // We run the whole thing at half speed to sidestep some latency issues.    
    logic skip_tick;
    logic proc_tick;
    always_ff @(posedge clk_sys) begin
        if( skip_tick ) begin
            proc_tick ^= 1;
        end
        skip_tick ^= 1;
    end
    
    always_ff @(posedge proc_tick) begin
        mem_strobe <= 0;                // One cycle only.
        out_char_strobe <= 0;
        if( reset ) begin
            core_state <= RESET;
        end else begin
            case( core_state )
                RESET: begin
                    if( reset ) begin
                        regs[REG_IP] <= 0;
                        core_state <= RESET;
                    end else begin
                        core_state <= IFETCH_SETUP;
                    end
                end
                HALT: begin
                    core_state <= HALT;
                end
                IFETCH_SETUP: begin
                    ip_current <= regs[REG_IP];
                    mem_addr_read <= regs[REG_IP];
                    ro_flags <= regs[REG_FLAGS];
                    core_state <= IFETCH_READ;
                end
                IFETCH_READ: begin
                    instr <= mem_word_read;
                    raw_op1 <= mem_word_read[11:8];
                    op1 <= regs[mem_word_read[11:8]];
                    raw_op2 <= mem_word_read[7:4];
                    op2 <= regs[mem_word_read[7:4]];
                    raw_opcode <= mem_word_read[15:12];
                    raw_cond <= mem_word_read[3:0];
                    core_state <= DECODE;
                end
                DECODE: begin
                    case( raw_opcode )
                        OP_NOP: begin
                            core_state <= HALT;
                        end
                        OP_JP: begin
                            condtrue <= ( raw_cond[3] ? raw_cond[2:0]&{ro_flags[2:1],1'b1} : raw_cond[2:0]&~{ro_flags[2:0],1'b1} ) != 0;
                            core_state <= DO_JP;
                        end
                        OP_BR: begin
                            condtrue <= ( raw_cond[3] ? raw_cond[2:0]&{ro_flags[2:1],1'b1} : raw_cond[2:0]&~{ro_flags[2:0],1'b1} ) != 0;
                            core_state <= STEP;
                        end
                        OP_LD: begin
                            opmode <= raw_cond[3];
                            core_state <= DO_LD_1;
                        end
                        OP_ST: begin
                            opmode <= raw_cond[3];
                            core_state <= DO_ST;
                        end
                        OP_ADD: begin
                            opmode <= raw_cond[3];
                            core_state <= DO_ADD;
                        end
                        OP_SUB: begin
                            opmode <= raw_cond[3];
                            core_state <= STEP;
                        end
                        OP_AND: begin
                            opmode <= raw_cond[3];
                            core_state <= DO_AND;
                        end
                        OP_SHR: begin
                            opmode <= raw_cond[3];
                            core_state <= DO_SHR;
                        end
                        OP_MOV: begin
                            opmode <= raw_cond[3];
                            core_state <= DO_MOV;
                        end
                        OP_CMP: begin
                            opmode <= raw_cond[3];
                            core_state <= DO_CMP;
                        end
                        OP_OUT: begin
                            opmode <= raw_cond[3];
                            core_state <= DO_OUT;
                        end
                        OP_CONST: begin
                            core_state <= DO_CONST;
                        end                    
                        default: core_state <= STEP;
                    endcase
                end
                DO_JP: begin
                    if( condtrue ) begin
                        regs[REG_IP] <= op1;
                    end else begin
                        regs[REG_IP] <= op2;
                    end
                    core_state <= IFETCH_SETUP;    // Not STEP!
                end
                DO_LD_1: begin
                    if( opmode ) begin
                        regs[raw_op2] <= raw_op1;
                        core_state <= STEP;
                    end else begin
                        mem_addr_read <= op1;
                        core_state <= DO_LD_2;
                    end
                end
                DO_LD_2: begin
                    regs[raw_op2] <= mem_word_read;
                    core_state <= STEP;
                end
                DO_ST: begin
                    if( opmode ) begin
                        mem_word_write <= raw_op1;
                    end else begin
                        mem_word_write <= op1;
                    end
                    mem_addr_write <= op2;
                    mem_strobe <= 1;
                    core_state <= STEP;
                end
                DO_CMP: begin
                    if( opmode ) begin
                        regs[REG_FLAGS] <= { ro_flags[15:3],
                                             raw_op1>op2,
                                             raw_op1==op2,
                                             1'b1 };
                    end else begin
                        regs[REG_FLAGS] <= { ro_flags[15:3],
                                             op1>op2,
                                             op1==op2,
                                             1'b1 };
                    end
                    core_state <= STEP;                                        
                end
                DO_CONST: begin
                    regs[raw_op1] <= {regs[raw_op1][7:0],instr[7:0]};
                    core_state <= STEP;
                end
                DO_ADD: begin
                    if( opmode ) begin
                        regs[raw_op2] = raw_op1+op2;
                    end else begin
                        regs[raw_op2] = op1+op2;
                    end
                    core_state <= STEP;
                end
                DO_AND: begin
                    if( opmode ) begin
                        regs[raw_op2] = raw_op1&op2;
                    end else begin
                        regs[raw_op2] = op1&op2;
                    end
                    core_state <= STEP;
                end
                DO_SHR: begin
                    if( opmode ) begin
                        regs[raw_op2] = op2>>raw_op1;
                    end else begin
                        regs[raw_op2] = op2>>op1;
                    end
                    core_state <= STEP;
                end
                DO_MOV: begin
                    if( opmode ) begin
                        regs[raw_op2] = raw_op1;
                    end else begin
                        regs[raw_op2] = op1;
                    end
                    core_state <= STEP;
                end
                DO_OUT: begin
                    if( opmode ) begin
                        out_char <= {4'b0,raw_op1};
                    end else begin
                        out_char <= op1[7:0];
                    end
                    write_x <= op2[15:8];
                    write_y <= op2[7:0];
                    out_char_strobe <= 1;
                    core_state <= STEP;                                        
                end
                STEP: begin     // Only for instructions which step one forward!
                    regs[REG_IP] <= regs[REG_IP]+1;
                    core_state <= IFETCH_SETUP;
                end
            endcase
        end
    end
    
    // Debug output
    logic [15:0] raw_core_state;
    always_comb begin
        raw_core_state = core_state;
    end
    logic [8:0] showstate = 0;
    always_ff @(posedge clk_sys) begin
        char_str <= 0;
        if( out_char_strobe ) begin
            char_x <= write_x;
            char_y <= write_y;
            char_chr <= out_char;
            char_str <= 1;
        end else begin
            case(showstate)
                0: begin char_x <= 0; char_y <= 0; char_chr <= out_char; char_str <= 1; end
                1: begin char_x <= 1; char_y <= 0; char_chr <= reset? 8'h52 : 8'h66 ; char_str <= 1; end
                2: begin char_x <= 2; char_y <= 0; char_chr <= raw_core_state+48; char_str <= 1; end
                3: begin char_x <= 3; char_y <= 0; char_chr <= regs[0][15:12]+48; char_str <= 1; end
                4: begin char_x <= 4; char_y <= 0; char_chr <= regs[0][11:8]+48; char_str <= 1; end
                5: begin char_x <= 5; char_y <= 0; char_chr <= regs[0][7:4]+48; char_str <= 1; end
                6: begin char_x <= 6; char_y <= 0; char_chr <= regs[0][3:0]+48; char_str <= 1; end
                7: begin char_x <= 3; char_y <= 1; char_chr <= regs[1][15:12]+48; char_str <= 1; end
                8: begin char_x <= 4; char_y <= 1; char_chr <= regs[1][11:8]+48; char_str <= 1; end
                9: begin char_x <= 5; char_y <= 1; char_chr <= regs[1][7:4]+48; char_str <= 1; end
                10: begin char_x <= 6; char_y <= 1; char_chr <= regs[1][3:0]+48; char_str <= 1; end
                11: begin char_x <= 3; char_y <= 2; char_chr <= regs[2][15:12]+48; char_str <= 1; end
                12: begin char_x <= 4; char_y <= 2; char_chr <= regs[2][11:8]+48; char_str <= 1; end
                13: begin char_x <= 5; char_y <= 2; char_chr <= regs[2][7:4]+48; char_str <= 1; end
                14: begin char_x <= 6; char_y <= 2; char_chr <= regs[2][3:0]+48; char_str <= 1; end
                15: begin char_x <= 3; char_y <= 3; char_chr <= regs[3][15:12]+48; char_str <= 1; end
                16: begin char_x <= 4; char_y <= 3; char_chr <= regs[3][11:8]+48; char_str <= 1; end
                17: begin char_x <= 5; char_y <= 3; char_chr <= regs[3][7:4]+48; char_str <= 1; end
                18: begin char_x <= 6; char_y <= 3; char_chr <= regs[3][3:0]+48; char_str <= 1; end
                19: begin char_x <= 3; char_y <= 4; char_chr <= regs[4][15:12]+48; char_str <= 1; end
                20: begin char_x <= 4; char_y <= 4; char_chr <= regs[4][11:8]+48; char_str <= 1; end
                21: begin char_x <= 5; char_y <= 4; char_chr <= regs[4][7:4]+48; char_str <= 1; end
                22: begin char_x <= 6; char_y <= 4; char_chr <= regs[4][3:0]+48; char_str <= 1; end
                23: begin char_x <= 3; char_y <= 5; char_chr <= regs[5][15:12]+48; char_str <= 1; end
                24: begin char_x <= 4; char_y <= 5; char_chr <= regs[5][11:8]+48; char_str <= 1; end
                25: begin char_x <= 5; char_y <= 5; char_chr <= regs[5][7:4]+48; char_str <= 1; end
                26: begin char_x <= 6; char_y <= 5; char_chr <= regs[5][3:0]+48; char_str <= 1; end
                27: begin char_x <= 3; char_y <= 6; char_chr <= regs[6][15:12]+48; char_str <= 1; end
                28: begin char_x <= 4; char_y <= 6; char_chr <= regs[6][11:8]+48; char_str <= 1; end
                29: begin char_x <= 5; char_y <= 6; char_chr <= regs[6][7:4]+48; char_str <= 1; end
                30: begin char_x <= 6; char_y <= 6; char_chr <= regs[6][3:0]+48; char_str <= 1; end
                31: begin char_x <= 3; char_y <= 7; char_chr <= regs[7][15:12]+48; char_str <= 1; end
                32: begin char_x <= 4; char_y <= 7; char_chr <= regs[7][11:8]+48; char_str <= 1; end
                33: begin char_x <= 5; char_y <= 7; char_chr <= regs[7][7:4]+48; char_str <= 1; end
                34: begin char_x <= 6; char_y <= 7; char_chr <= regs[7][3:0]+48; char_str <= 1; end
    
                35: begin char_x <= 3; char_y <= 8; char_chr <= regs[8][15:12]+48; char_str <= 1; end
                36: begin char_x <= 4; char_y <= 8; char_chr <= regs[8][11:8]+48; char_str <= 1; end
                37: begin char_x <= 5; char_y <= 8; char_chr <= regs[8][7:4]+48; char_str <= 1; end
                38: begin char_x <= 6; char_y <= 8; char_chr <= regs[8][3:0]+48; char_str <= 1; end
                39: begin char_x <= 3; char_y <= 9; char_chr <= regs[9][15:12]+48; char_str <= 1; end
                40: begin char_x <= 4; char_y <= 9; char_chr <= regs[9][11:8]+48; char_str <= 1; end
                41: begin char_x <= 5; char_y <= 9; char_chr <= regs[9][7:4]+48; char_str <= 1; end
                42: begin char_x <= 6; char_y <= 9; char_chr <= regs[9][3:0]+48; char_str <= 1; end
                43: begin char_x <= 3; char_y <= 10; char_chr <= regs[10][15:12]+48; char_str <= 1; end
                44: begin char_x <= 4; char_y <= 10; char_chr <= regs[10][11:8]+48; char_str <= 1; end
                45: begin char_x <= 5; char_y <= 10; char_chr <= regs[10][7:4]+48; char_str <= 1; end
                46: begin char_x <= 6; char_y <= 10; char_chr <= regs[10][3:0]+48; char_str <= 1; end
                47: begin char_x <= 3; char_y <= 11; char_chr <= regs[11][15:12]+48; char_str <= 1; end
                48: begin char_x <= 4; char_y <= 11; char_chr <= regs[11][11:8]+48; char_str <= 1; end
                49: begin char_x <= 5; char_y <= 11; char_chr <= regs[11][7:4]+48; char_str <= 1; end
                50: begin char_x <= 6; char_y <= 11; char_chr <= regs[11][3:0]+48; char_str <= 1; end
                51: begin char_x <= 3; char_y <= 12; char_chr <= regs[12][15:12]+48; char_str <= 1; end
                52: begin char_x <= 4; char_y <= 12; char_chr <= regs[12][11:8]+48; char_str <= 1; end
                53: begin char_x <= 5; char_y <= 12; char_chr <= regs[12][7:4]+48; char_str <= 1; end
                54: begin char_x <= 6; char_y <= 12; char_chr <= regs[12][3:0]+48; char_str <= 1; end
                55: begin char_x <= 3; char_y <= 13; char_chr <= regs[13][15:12]+48; char_str <= 1; end
                56: begin char_x <= 4; char_y <= 13; char_chr <= regs[13][11:8]+48; char_str <= 1; end
                57: begin char_x <= 5; char_y <= 13; char_chr <= regs[13][7:4]+48; char_str <= 1; end
                58: begin char_x <= 6; char_y <= 13; char_chr <= regs[13][3:0]+48; char_str <= 1; end
                59: begin char_x <= 3; char_y <= 14; char_chr <= regs[14][15:12]+48; char_str <= 1; end
                60: begin char_x <= 4; char_y <= 14; char_chr <= regs[14][11:8]+48; char_str <= 1; end
                61: begin char_x <= 5; char_y <= 14; char_chr <= regs[14][7:4]+48; char_str <= 1; end
                62: begin char_x <= 6; char_y <= 14; char_chr <= regs[14][3:0]+48; char_str <= 1; end
                63: begin char_x <= 3; char_y <= 15; char_chr <= regs[15][15:12]+48; char_str <= 1; end
                64: begin char_x <= 4; char_y <= 15; char_chr <= regs[15][11:8]+48; char_str <= 1; end
                65: begin char_x <= 5; char_y <= 15; char_chr <= regs[15][7:4]+48; char_str <= 1; end
                66: begin char_x <= 6; char_y <= 15; char_chr <= regs[15][3:0]+48; char_str <= 1; end
    
    
                default: begin end
            endcase
            if( showstate == 100 ) begin
               showstate <= 0;
            end else begin
                showstate <= showstate+1;
            end
        end
    end

endmodule
