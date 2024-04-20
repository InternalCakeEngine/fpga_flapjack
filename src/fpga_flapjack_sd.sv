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
        output      logic [7:0] sd_status,
        // Hardware interface
        output      logic sd_cs,
        output      logic sd_mosi,
        input wire  logic sd_miso,
        input wire  logic sd_clk,
        input wire  logic sd_cd,
        input wire  logic sd_wp,
        // Data in/out interface
        input wire  logic [8:0]  sd_buffaddr,
        input wire  logic [15:0] sd_bufdata_in,
        output      logic [15:0] sd_bufdata_out,
        input wire  logic        sd_writestrobe,
        // Command interface
        input wire  logic [7:0] sd_cmd,
        input wire  logic [7:0] sd_cmddata
    );
        
    enum {
        RESET                  // Do nothing but reset.
    } sd_state=RESET;

    always_ff @(posedge clk_sys) begin
    end
    
endmodule
