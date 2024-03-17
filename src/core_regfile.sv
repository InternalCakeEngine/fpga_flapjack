`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 16.03.2024 23:20:15
// Design Name: 
// Module Name: core_regfile
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


module flapjack_regfile #(
            parameter WIDTH=16,
            parameter COUNT=8
        ) (
        input wire logic             clk,
        input wire logic [WIDTH-1:0] read_index1,
        output     logic [WIDTH-1:0] read_value1,
        input wire logic [WIDTH-1:0] read_index2,
        output     logic [WIDTH-1:0] read_value2,
        input wire logic [WIDTH-1:0] write_index,
        input wire logic [WIDTH-1:0] write_value,
        input wire logic             write_strobe
    );
    
    // Actual storage.
    logic   [WIDTH-1:0] regs [0:COUNT-1];
    
    // Read up to two values.
    always_ff @(clk) begin
        read_value1 <= regs[read_index1];
        read_value2 <= regs[read_index2];
    end
    
    // Write one value.
    always_ff @(clk) begin
        if( write_strobe ) begin
            regs[write_index] <= write_value;
        end
    end
    
endmodule
