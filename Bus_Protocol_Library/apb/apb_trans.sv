// APB transaction item skeleton
//
// Encodes a single APB read or write transfer.

import uvm_pkg::*;

class apb_trans extends uvm_sequence_item;

    // APB address (12 bits in interface, can be specialised per design)
    rand bit [11:0] addr;

    // APB write data (32 bits)
    rand bit [31:0] wdata;

    // APB read data (32 bits)
    bit  [31:0] rdata;

    // APB read/write control (1 = write, 0 = read)
    rand bit       write;

    `uvm_object_utils_begin(apb_trans)
        `uvm_field_int(addr,  UVM_ALL_ON)
        `uvm_field_int(wdata, UVM_ALL_ON)
        `uvm_field_int(rdata, UVM_ALL_ON)
        `uvm_field_int(write, UVM_ALL_ON)
    `uvm_object_utils_end

    function new(string name = "apb_trans");
        super.new(name);
    endfunction

endclass : apb_trans


