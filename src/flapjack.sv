`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 16.03.2024 19:37:49
// Design Name: 
// Module Name: flapjack
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


// Collect the pins needed for the whole systems.
module flapjack(
    input  wire logic clk_100m,     // 100 MHz clock
    input  wire logic btn_rst_n,    // reset button
    output      logic vga_hsync,    // VGA horizontal sync
    output      logic vga_vsync,    // VGA vertical sync
    output      logic [3:0] vga_r,  // 4-bit VGA red
    output      logic [3:0] vga_g,  // 4-bit VGA green
    output      logic [3:0] vga_b   // 4-bit VGA blue
    );
    
    // generate system clock
    logic clk_sys;
    logic clk_sys_locked;
    logic rst_sys;
    clock_sys clock_sys_inst (
        .clk_100m,
        .rst(!btn_rst_n),  // reset button is active low
        .clk_sys,
        .clk_sys_locked
    );
    always_ff @(posedge clk_sys) rst_sys <= !clk_sys_locked;  // wait for clock lock

    // Instantiate a screen for transient output.
    vga_textmode textmode (
        .clk_100m,     // 100 MHz clock (will be used to generate VGA clock)
        .clk_sys,      // A system clock shared between components.
        .btn_rst_n,    // reset button
        .vga_hsync,    // VGA horizontal sync
        .vga_vsync,    // VGA vertical sync
        .vga_r,         // 4-bit VGA red
        .vga_g,         // 4-bit VGA green
        .vga_b,         // 4-bit VGA blue
        .char_x,        // Write location x
        .char_y,        // Write location y
        .char_chr,      // Write character
        .char_str       // Write strobe.
    );
    
    // Control link between core and display.
    logic [6:0] char_x;
    logic [5:0] char_y;
    logic [8:0] char_chr;
    logic char_str;
    
    logic reset;
    always_comb begin
        reset = ~btn_rst_n;
    end
    
    flapjack_core core (
        .clk_sys,       // 125 MHz system clock
        .reset,         // Reset when high.
        .char_x,        // Write location x
        .char_y,        // Write location y
        .char_chr,      // Write character
        .char_str       // Write strobe.
    );

endmodule
