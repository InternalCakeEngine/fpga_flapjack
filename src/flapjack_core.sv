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
    /*
    always_ff @(posedge clk_sys) begin
        if( out_char_strobe ) begin
            char_x <= write_x;
            char_y <= write_y;
            char_chr <= out_char;
            char_str <= 1;  // Assert strobe for only 1 cycle.
            if( write_x == 79 ) begin
                write_x <= 0;
                if( write_y == 29 ) begin
                    write_y <= 0;
                end else begin
                    write_y += 1;
                end
             end else begin
                write_x += 1;
             end
        end
    end
    */
    
    
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
    localparam REGCOUNT = 8;
    logic [REGWIDTH-1:0] regs[REGCOUNT];
    localparam REG_IP = 7;
    localparam REG_FLAGS = 6;

    // A register file and access
    // Having this behind an interface doesn't make much sense atm.
    /*
    logic [15:0] regfile_read_index1;
    logic [15:0] regfile_read_value1;
    logic [15:0] regfile_read_index2;
    logic [15:0] regfile_read_value2;
    logic [15:0] regfile_write_index;
    logic [15:0] regfile_write_value;
    logic        regfile_write_strobe;
    flapjack_regfile #(
        .WIDTH(16),
        .COUNT(8)
    ) regfile (
        .clk(clk_sys),
        .read_index1(regfile_read_index1),
        .read_value1(regfile_read_value1),
        .read_index2(regfile_read_index2),
        .read_value2(regfile_read_value2),
        .write_index(regfile_write_index),
        .write_value(regfile_write_value),
        .write_strobe(regfile_write_strobe),
        .rawr0(rawr0),
        .rawr1(rawr1),
        .rawr2(rawr2),
        .rawr3(rawr3),
        .rawr4(rawr4),
        .rawr5(rawr5),
        .rawr6(rawr6),
        .rawr7(rawr7)
    );
    */
    
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
        STEP                    // Move to the next instr (for non-branching).
    } core_state=RESET;
    
    // Decoding parts.
    logic [15:0] instr;
    logic [15:0] ro_flags;
    logic [4:0] raw_opcode;
    logic [2:0] raw_op1;
    logic [2:0] raw_op2;
    logic [4:0] raw_cond;
    logic [15:0] op1;
    logic [15:0] op2;
    logic condtrue;
    logic [15:0] ip_current;
    
    always_comb begin
        raw_core_state = core_state;
    end
    
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
                    raw_op1 <= mem_word_read[10:8];
                    op1 <= regs[mem_word_read[10:8]];
                    raw_op2 <= mem_word_read[7:5];
                    op2 <= regs[mem_word_read[7:5]];
                    raw_opcode <= mem_word_read[15:11];
                    raw_cond <= mem_word_read[4:0];
                    core_state <= DECODE;
                end
                DECODE: begin
                    condtrue <= ( raw_cond[4] ? raw_cond[3:0]&ro_flags[3:0] : raw_cond[3:0]&~ro_flags[3:0] ) != 0;
                    case( raw_opcode )
                        OP_NOP: begin
                            core_state <= HALT;
                        end
                        OP_JP: begin
                            core_state <= DO_JP;
                        end
                        OP_BR: begin
                            core_state <= STEP;
                        end
                        OP_LD: begin
                            core_state <= DO_LD_1;
                        end
                        OP_ST: begin
                            core_state <= DO_ST;
                        end
                        OP_ADD: begin
                            core_state <= DO_ADD;
                        end
                        OP_SUB: begin
                            core_state <= STEP;
                        end
                        OP_CMP: begin
                            core_state <= DO_CMP;
                        end
                        OP_OUT: begin
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
                    if( condtrue ) begin
                        mem_addr_read <= op1;
                        core_state <= DO_LD_2;
                    end else begin
                        core_state <= STEP;
                    end
                end
                DO_LD_2: begin
                    if( condtrue ) begin
                        regs[raw_op2] <= mem_word_read;
                        core_state <= STEP;
                    end
                end
                DO_ST: begin
                    if( condtrue ) begin
                        mem_word_write <= op1;
                        mem_addr_write <= op2;
                        mem_strobe <= 1;
                    end
                    core_state <= STEP;
                end
                DO_CMP: begin
                    regs[REG_FLAGS] <= { ro_flags[15:4],
                                         1'b0,
                                         op1>op2,
                                         op1==op2,
                                         1'b1 };
                    core_state <= STEP;                                        
                end
                DO_CONST: begin
                    regs[raw_op1] <={8'b0,instr[7:0]};
                    core_state <= STEP;                            
                end
                DO_ADD: begin
                    regs[raw_op2] = op1+op2;
                    core_state <= STEP;
                end
                DO_OUT: begin
                    out_char <= op1[7:0];
                    //out_char_strobe <= 1;
                    core_state <= STEP;                                        
                end
                STEP: begin     // Only for instructions which step one forward!
                    regs[REG_IP] <= regs[REG_IP]+1;
                    core_state <= IFETCH_SETUP;
                end
            endcase
        end
    end
    logic [15:0] raw_core_state;
    logic [8:0] showstate = 0;
    always_ff @(posedge clk_sys) begin
        char_str <= 0;
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
            default: begin end
        endcase
        if( showstate == 100 ) begin
           showstate <= 0;
        end else begin
            showstate <= showstate+1;
        end
    end

endmodule
