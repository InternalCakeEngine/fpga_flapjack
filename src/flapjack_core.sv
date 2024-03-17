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
        input  wire  logic   clk_sys,       // 125 MHz system clock
        output       logic   [6:0] char_x,        // Write location x
        output       logic   [5:0] char_y,        // Write location y
        output       logic   [8:0] char_chr,      // Write character
        output       logic   char_str       // Write strobe.
    );
    
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
    localparam MEM_INITIAL = "core.mem";
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
    
    // A register file and access
    // Having this behind an interface doesn't make much sense atm.
    localparam REG_IP = 7;
    localparam REG_FLAGS = 6;
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
        .write_strobe(regfile_write_strobe)
    );
    
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
    
    // Set of states for the core.
    enum {
        IFETCH_SETUP,           // Fetch IP from the register file and the flags.
        IFETCH_READ_SETUP,      // Start memory fetch for an instruction.
        IFETCH_READ,            // Read the instruction, and setup op fetching.
        DECODE,                 // Read the op values, condition and decide what to do with the opcode.
        DO_JP,                  // Do the work of jumping.
        DO_LD_1,                // Loading from memory: setup the memory read address.
        DO_LD_2,                // Loading from memory: transfer from memory result to register.
        DO_ST,                  // Storing to memory.
        WRITE,
        STEP
    } core_state, core_state_next;
    always_ff @(posedge clk_sys) begin
        core_state = core_state_next;
    end
    
    // Decoding parts.
    logic [15:0] instr;
    logic [15:0] flags;
    logic [4:0] opcode;
    logic [2:0] op1;
    logic [2:0] op2;
    logic [4:0] cond;
    assign opcode = instr[15:11];
    assign op1 = instr[10:8];
    assign op2 = instr[7:5];
    assign cond = instr[4:0];
    logic [15:0] op1;
    logic [15:0] op2;
    logic condtrue;
    logic [15:0] ip_current;
    
    always_ff @(posedge clk_sys) begin
        regfile_write_strobe <<= 0;     // Make sure it's one cycle only.
        mem_strobe <= 0;                // One cycle only.
        case( core_state )
            IFETCH_SETUP: begin
                regfile_read_index1 <= REG_IP;
                regfile_read_index2 <= REG_FLAGS;
                core_state_next <= IFETCH_READ;
            end
            IFETCH_READ_SETUP: begin
                ip_current <= regfile_read_value1;
                mem_addr_read <= regfile_read_value1;
                flags <= regfile_read_value2;
                core_state_next <= IFETCH_READ;
            end
            IFETCH_READ: begin
                instr <= mem_word_read;
                regfile_read_index1 <= mem_word_read[10:8];
                regfile_read_index2 <= mem_word_read[7:5];
                core_state_next <= DECODE;
            end
            DECODE: begin
                op1 <= regfile_read_value1;
                op2 <= regfile_read_value2;
                condtrue <= ( cond[4] ? cond[3:0]&flags[3:0] : cond[3:0]&~flags[3:0] ) != 0;
                case( opcode )
                    OP_NOP: begin
                        core_state_next <= STEP;
                    end
                    OP_JP: begin
                        core_state_next <= DO_JP;
                    end
                    OP_BR: begin
                    end
                    OP_LD: begin
                        core_state_next <= DO_LD_1;
                    end
                    OP_ST: begin
                        core_state_next <= DO_ST;
                    end
                    OP_ADD: begin
                    end
                    OP_SUB: begin
                    end
                    OP_CMP: begin
                    end                    
                    default: core_state_next <= STEP;
                endcase
            end
            DO_JP: begin
                regfile_write_index = REG_IP;
                if( condtrue ) begin
                    regfile_write_value = op1;
                end else begin
                    regfile_write_value = op2;
                end
                regfile_write_strobe <= 1;
                core_state_next <= IFETCH_SETUP;    // Not STEP!
            end
            DO_LD_1: begin
                if( condtrue ) begin
                    mem_addr_read <= op1;
                    core_state_next <= DO_LD_2;
                end else begin
                    core_state_next <= STEP;
                end
            end
            DO_LD_2: begin
                regfile_write_index <= op2;
                regfile_write_value <= mem_word_read;
                regfile_write_strobe <= 1;
                core_state_next <= STEP;
            end
            DO_ST: begin
                if( condtrue ) begin
                    mem_word_write <= op1;
                    mem_addr_write <= op2;
                    mem_strobe <= 1;
                end
                core_state_next <= STEP;
            end
            WRITE: begin
            end
            STEP: begin     // Only for insttructions which step one forward!
                regfile_write_index = REG_IP;
                regfile_write_value = ip_current+1;
                regfile_write_strobe <<= 1;
            end
            default: begin
                core_state_next <= IFETCH_SETUP;
            end
        endcase
    end
    
    // Do something to the screen on every slow tick, for testing
    // interdace to the screen.
    /*
    logic [8:0] write_x = 0;
    logic [8:0] write_y = 0;
    always_ff @(posedge clk_sys) begin
        if( tick_minor == 0 ) begin
            char_x <= write_x;
            char_y <= write_y;
            char_chr <= write_x+write_y+32+tick_major;
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
        end else begin
            char_str <= 0;
        end
    end
    */
    
endmodule
