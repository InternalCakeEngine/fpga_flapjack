`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 20.04.2024 17:20:44
// Design Name: 
// Module Name: fpga_flapjack_sd
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


module flapjack_sdcard(
        // Housekeeping
        input wire  logic clk_sys,       // 125 MHz systemclock
        output      logic reset,         // Reset when high.
        // Hardware interface
        output      logic sd_cs,
        output      logic sd_mosi,
        input wire  logic sd_miso,
        output      logic sd_clk,
        input wire  logic sd_cd,
        input wire  logic sd_wp,
        // Data in/out interface
        input wire  logic [8:0]  sd_buffaddr,
        input wire  logic [15:0] sd_bufdata_in,
        output      logic [15:0] sd_bufdata_out,
        input wire  logic        sd_writestrobe,
        // Command interface
        output      logic [7:0] sd_status,
        input wire  logic [7:0] sd_cmd,
        input wire  logic [7:0] sd_cmddata
    );
        
    enum {
        CMDREADY,                  // Awaiting a command.
        STARTING_WORK,             // Waiting for the shifter to start.
        WORKING                    // Waiting for the shift to complete
    } cmdstate=CMDREADY;
    
    logic clk_sd;
    logic clk_counter;
    always_ff @(posedge clk_sys) begin
        if( clk_counter==624 ) begin
            clk_sd <= 1;
            clk_counter = 0;
        end else begin
            clk_sd <= 0;
            clk_counter <= clk_counter+1;
        end
    end
    
    always_comb begin
        if( reset ) begin
            clk_counter = 0;
            cmdstate = CMDREADY;
        end
    end
    
    // Outshifting and collecting state machine.
    logic shift_busy;
    logic start_shifting;
    logic       shifting_phase;
    logic [7:0] shifting_pre_count;
    logic [7:0] shifting_out_count;
    logic [7:0] shifting_in_count;
    logic [47:0] shiftreg;      // Both out and in.
    logic [3:0] waitcount;
    
    enum {
        HALTED,         // Doing nothing.
        CLOCKING,       // Clocking without sending data.
        SHIFTING_OUT,   // Shifting out from the shift register.
        WAITING,        // Clocking between shifting out and shifting in.
        SHIFTING_IN,    // Shifting in a response.
        FINISHING       // Tidying up
    } shiftstate = HALTED;
    
    always_comb begin
        shift_busy = shiftstate != HALTED;
    end
    
    always_ff @(posedge clk_sd ) begin
        case( shiftstate )
            HALTED: begin
                if( start_shifting ) begin
                    if( shifting_pre_count > 0 ) begin
                        shiftstate <= CLOCKING;
                    end else begin
                        shiftstate <= SHIFTING_OUT;
                    end
                    shifting_phase <= 0;
                    sd_cs <= 0;
                end else begin
                    sd_cs <= 1;
                    sd_mosi <= 1;
                    sd_clk <= 0;
                end
            end
            CLOCKING: begin
                if( shifting_phase ) begin
                    sd_clk <= 1;
                    shifting_phase <= 1;
                end else begin
                    sd_clk <= 0;
                    if( shifting_pre_count == 1 ) begin
                        sd_cs <= 0;
                        shiftstate <= SHIFTING_OUT;
                    end else begin
                        shifting_pre_count <= shifting_pre_count-1;
                    end
                    shifting_phase <= 0;
                end
                shiftstate <= HALTED;
            end
            SHIFTING_OUT: begin
                if( shifting_phase ) begin
                    sd_mosi <= shiftreg[47];
                    shiftreg <= {shiftreg[46:0],1'b0};
                    sd_clk <= 1;
                    shifting_phase <= 1;
                end else begin
                    sd_clk <= 0;
                    if( shifting_out_count == 1 ) begin
                        shiftstate <= WAITING;
                        waitcount <= 0;
                        sd_mosi <= 1;
                    end else begin
                        shifting_out_count <= shifting_out_count-1;
                    end
                    shifting_phase <= 0;
                end
            end
            WAITING: begin
                if( shifting_phase ) begin
                    sd_clk <= 1;
                    shifting_phase <= 1;
                    if( waitcount==15 ) begin
                        shiftstate <= HALTED;
                        // TODO: This is an error case which we need to signal.
                    end else begin
                        waitcount <= waitcount+1;
                    end
                end else begin
                    sd_clk <= 0;
                    shifting_phase <= 0;
                    if( sd_miso ) begin
                        shiftreg <= 0;
                        shiftstate = SHIFTING_IN;
                    end
                end
            end
            SHIFTING_IN: begin
                if( shifting_phase ) begin
                    sd_clk <= 1;
                    shifting_phase <= 1;
                end else begin
                    sd_clk <= 0;
                    shifting_phase <= 0;
                    shiftreg = {shiftreg[47:1],sd_miso};
                    if( shifting_in_count <= 1 ) begin
                        shiftstate <= HALTED;
                    end else begin
                        shifting_in_count <= shifting_in_count-1;
                    end
                end
            end
        endcase
    end

    always_ff @(posedge clk_sys) begin
        case( cmdstate )
            CMDREADY: begin
                if( sd_cmd == 1 ) begin
                    shifting_pre_count = 100;
                    shifting_out_count = 48;
                    shifting_in_count = 40;
                    shiftreg = 48'b01_000000_00000000_00000000_00000000_00000000_1001010_1;
                    start_shifting <= 1;
                    cmdstate = STARTING_WORK;
                end
            end
            STARTING_WORK: begin
                if( shiftstate != HALTED ) begin
                    cmdstate <= WORKING;
                end
            end
            WORKING: begin
                if( shiftstate == HALTED ) begin
                    sd_status <= shiftreg[7:0];
                    cmdstate <= CMDREADY;
                end
            end
        endcase
    end
    
endmodule
