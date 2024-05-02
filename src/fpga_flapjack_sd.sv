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
        input wire  logic reset,         // Reset when high.
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
        output      logic [8:0] sd_status,
        input wire  logic [7:0] sd_cmd,
        input wire  logic [15:0] sd_cmddata
    );
         
    enum {
        CMDWAITING,                // Awaiting a command.
        CMDREADY,                  // Setting up a command.
        STARTING_WORK,             // Waiting for the shifter to start.
        WORKING                    // Waiting for the shift to complete
    } cmdstate=CMDREADY;
    
    // Initial values for when moving out of HALTED state.
    logic [7:0] new_shifting_pre_count;
    logic [7:0] new_shifting_out_count;
    logic [7:0] new_shifting_in_count;
    logic [47:0] new_shiftreg;      // Both out and in.

    
    // Outshifting and collecting state machine.
    logic start_shifting;
    logic       shifting_phase;
    logic [7:0] shifting_pre_count;
    logic [7:0] shifting_out_count;
    logic [7:0] shifting_in_count;
    logic       collect_block;
    logic [47:0] shiftreg;      // Both out and in.
    logic [7:0] collect_lead;
    logic [3:0] waitcount;
    logic [13:0] collected_count;
    
    enum {
        HALTED,          // Doing nothing.
        CLOCKING,        // Clocking without sending data.
        SHIFTING_OUT,    // Shifting out from the shift register.
        WAITING,         // Clocking between shifting out and shifting in.
        SHIFTING_IN,     // Shifting in a response.
        COLLECTING_WAIT, // Wait for an incoming block of data
        COLLECTING       // Collecting a block of data
    } shiftstate = HALTED;
    
    logic [10:0] clk_counter = 0;    
    always_ff @(posedge clk_sys ) begin
        if( clk_counter == 312 ) begin
            clk_counter <= 0;
        end else begin
            clk_counter <= clk_counter+1;
            if( clk_counter == 0 ) begin
                case( shiftstate )
                    HALTED: begin
                        if( start_shifting ) begin
                            shifting_pre_count <= new_shifting_pre_count;
                            shifting_out_count <= new_shifting_out_count;
                            shifting_in_count <=  new_shifting_in_count;
                            shiftreg <= new_shiftreg;
                            if( new_shifting_pre_count > 0 ) begin
                                shiftstate <= CLOCKING;
                                sd_cs <= 1;
                                sd_mosi <= 1;
                            end else begin
                                shiftstate <= SHIFTING_OUT;
                                sd_cs <= 0;
                                sd_mosi <= 1;
                            end
                            shifting_phase <= 0;
                        end else begin
                            sd_cs <= 1;
                            sd_mosi <= 1;
                        end
                    end
                    CLOCKING: begin
                        if( shifting_phase ) begin
                            sd_clk <= 1;
                            shifting_phase <= 0;
                        end else begin
                            sd_clk <= 0;
                            if( shifting_pre_count == 1 ) begin
                                sd_cs <= 0;
                                sd_mosi <= shiftreg[47];
                                shiftreg <= {shiftreg[46:0],1'b0};
                                shiftstate <= SHIFTING_OUT;
                            end else begin
                                shifting_pre_count <= shifting_pre_count-1;
                            end
                            shifting_phase <= 1;
                        end
                    end
                    SHIFTING_OUT: begin
                        if( shifting_phase ) begin
                            sd_clk <= 1;
                            shifting_phase <= 0;
                        end else begin
                            sd_clk <= 0;
                            sd_mosi <= shiftreg[47];
                            shiftreg <= {shiftreg[46:0],1'b0};
                            if( shifting_out_count == 1 ) begin
                                shiftstate <= WAITING;
                                waitcount <= 0;
                                sd_mosi <= 1;
                            end else begin
                                shifting_out_count <= shifting_out_count-1;
                            end
                            shifting_phase <= 1;
                        end
                    end
                    WAITING: begin
                        if( shifting_phase ) begin
                            sd_clk <= 1;
                            shifting_phase <= 0;
                            if( sd_miso == 0 ) begin
                                shiftreg <= 0;
                                shiftstate <= SHIFTING_IN;
                            end else begin
                                if( waitcount==32 ) begin
                                    shiftstate <= HALTED;
                                    // TODO: This is an error case which we need to signal.
                                end else begin
                                    waitcount <= waitcount+1;
                                end
                            end
                        end else begin
                            sd_clk <= 0;
                            shifting_phase <= 1;
                        end
                    end
                    SHIFTING_IN: begin
                        if( shifting_phase ) begin
                            sd_clk <= 1;
                            shifting_phase <= 0;
                            shiftreg <= {shiftreg[46:0],sd_miso};
                            if( shifting_in_count <= 2 ) begin
                                if( collect_block ) begin
                                    collect_lead <= 0;
                                    shiftstate <= COLLECTING_WAIT;
                                end else begin
                                    shiftstate <= HALTED;
                                end
                            end else begin
                                shifting_in_count <= shifting_in_count-1;
                            end
                        end else begin
                            sd_clk <= 0;
                            shifting_phase <= 1;
                        end
                    end
                    COLLECTING_WAIT: begin
                        if( shifting_phase ) begin
                            sd_clk <= 1;
                            shifting_phase <= 0;
                            collect_lead <= {collect_lead[6:0],sd_miso};
                        end else begin
                            sd_clk <= 0;
                            shifting_phase <= 1;
                            if( collect_lead == 8'hfe ) begin
                                collected_count <= 0;
                                shiftstate <= COLLECTING;
                            end
                        end
                    end
                    COLLECTING: begin
                        if( shifting_phase ) begin
                            sd_clk <= 1;
                            shifting_phase <= 0;
                            collected_count <= collected_count+1;
                        end else begin
                            sd_clk <= 0;
                            shifting_phase <= 1;
                            if( collected_count == 4096 ) begin
                                shiftstate <= HALTED;
                            end
                        end
                    end
                    default: begin
                        shiftstate <= HALTED;
                    end
                endcase
            end
        end
    end

    logic [7:0] running_cmd;
    logic [47:0] checkreg;
    logic [31:0] cmdaddr;
    logic        docheck;

    always_ff @(posedge clk_sys) begin
        case( cmdstate )
            CMDWAITING: begin
                if( sd_cmd != running_cmd ) begin
                    running_cmd <= sd_cmd;
                    cmdstate <= CMDREADY;
                end
            end
            CMDREADY: begin
                case( running_cmd )
                    1: begin // CMD_0  0x00
                        new_shifting_pre_count <= 100;
                        new_shifting_out_count <= 48;
                        new_shifting_in_count <= 8;
                        new_shiftreg <= 48'b01_000000_00000000_00000000_00000000_00000000_1001010_1;
                        checkreg <= 8'b00000001;
                        docheck <= 1;
                        collect_block <= 0;
                        start_shifting <= 1;
                        sd_status <= 0;
                        cmdstate <= STARTING_WORK;
                    end
                    2: begin // CMD_8  0x08
                        new_shifting_pre_count <= 0;
                        new_shifting_out_count <= 48;
                        new_shifting_in_count <= 40;
                        new_shiftreg <= 48'b01_001000_00000000_00000000_00000001_10101010_1000011_1;
                        checkreg <= 40'b00000001_00000000_00000000_00000001_10101010;
                        docheck <= 1;
                        collect_block <= 0;
                        start_shifting <= 1;
                        sd_status <= 0;
                        cmdstate <= STARTING_WORK;
                    end
                    3: begin // CMD_58  0x3A
                        new_shifting_pre_count <= 0;
                        new_shifting_out_count <= 48;
                        new_shifting_in_count <= 40;
                        new_shiftreg <= 48'b01_111010_00000000_00000000_00000000_00000000_0000000_1;
                        docheck <= 0;
                        collect_block <= 0;
                        start_shifting <= 1;
                        sd_status <= 0;
                        cmdstate <= STARTING_WORK;
                    end
                    4: begin // CMD_55  0x37
                        new_shifting_pre_count <= 0;
                        new_shifting_out_count <= 48;
                        new_shifting_in_count <= 8;
                        new_shiftreg <= 48'b01_110111_00000000_00000000_00000000_00000000_0000000_1;
                        checkreg <= 8'b00000001;
                        docheck <= 1;
                        collect_block <= 0;
                        start_shifting <= 1;
                        sd_status <= 0;
                        cmdstate <= STARTING_WORK;
                    end
                    5: begin // CMD_41   0x29
                        new_shifting_pre_count <= 0;
                        new_shifting_out_count <= 48;
                        new_shifting_in_count <= 8;
                        new_shiftreg <= 48'b01_101001_01000000_00000000_00000000_00000000_0000000_1;
                        checkreg <= 8'b00000000;
                        docheck <= 1;
                        collect_block <= 0;
                        start_shifting <= 1;
                        sd_status <= 0;
                        cmdstate <= STARTING_WORK;
                    end
                    6: begin // CMD_58   0x3a
                        new_shifting_pre_count <= 0;
                        new_shifting_out_count <= 48;
                        new_shifting_in_count <= 40;
                        new_shiftreg <= 48'b01_111010_00000000_00000000_00000000_00000000_0000000_1;
                        checkreg <= 40'b00000000_11000000_11111111_10000000_00000000;
                        docheck <= 1;
                        collect_block <= 0;
                        start_shifting <= 1;
                        sd_status <= 0;
                        cmdstate <= STARTING_WORK;
                    end
                    7: begin // CMD_17 (read block)   0x11
                        new_shifting_pre_count <= 0;
                        new_shifting_out_count <= 48;
                        new_shifting_in_count <= 8;
                        new_shiftreg <= {8'b01_010001,cmdaddr,8'b0000000_1};
                        checkreg <= 8'b00000000;
                        docheck <= 1;
                        collect_block <= 1;
                        start_shifting <= 1;
                        sd_status <= 0;
                        cmdstate <= STARTING_WORK;
                    end
                    /* Pair of commands to build up 32 bits of address data. */
                    32: begin cmdaddr <= {cmdaddr[31:16],sd_cmddata}; sd_status<=9'b1_0000_0001; cmdstate<=CMDWAITING; end
                    33: begin cmdaddr <= {sd_cmddata,cmdaddr[15:0]}; sd_status<=9'b1_0000_0001; cmdstate<=CMDWAITING; end
                    default: begin
                        sd_status <= 0;
                        cmdstate <= CMDWAITING;
                    end
                endcase
            end
            STARTING_WORK: begin
                if( shiftstate != HALTED ) begin
                    start_shifting <= 0;
                    cmdstate <= WORKING;
                end
            end
            WORKING: begin
                if( shiftstate == HALTED ) begin
                    if( docheck ) begin
                        if( shiftreg == checkreg ) begin
                            sd_status <= 9'b1_0000_0001;
                        end else begin
                            sd_status <= 9'b1_0000_0000;
                        end
                    end else begin
                        sd_status <= 9'b1_0000_0001;
                    end
                    cmdstate <= CMDWAITING;
                end
            end
        endcase
    end
    
endmodule
