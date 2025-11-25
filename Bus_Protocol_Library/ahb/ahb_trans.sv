// AHB transaction item skeleton
//
// Allowed modifications:
//   - Field names and widths
//   - UVM field automation macros
//
// Avoid changing:
//   - The presence of an enum for HTRANS phases
//   - The separation between request and response fields

import uvm_pkg::*;

class ahb_trans extends uvm_sequence_item;

  // Encoded HTRANS phase
  typedef enum bit [1:0] {
    IDLE   = 2'b00,
    BUSY   = 2'b01,
    NONSEQ = 2'b10,
    SEQ    = 2'b11
  } trans_t;

  // Request-side fields
  trans_t          htrans = IDLE;
  logic            hsel;
  logic [11:0]     haddr;
  logic [2:0]      hsize;
  logic            hwrite;
  logic            hready;
  logic [31:0]     hwdata;

  // Response-side fields
  logic            hreadyout;
  logic            hresp;
  logic [31:0]     hrdata;

  `uvm_object_utils_begin(ahb_trans)
    `uvm_field_int(hsel,      UVM_ALL_ON)
    `uvm_field_int(haddr,     UVM_ALL_ON)
    `uvm_field_enum(trans_t,  htrans, UVM_ALL_ON)
    `uvm_field_int(hsize,     UVM_ALL_ON)
    `uvm_field_int(hwrite,    UVM_ALL_ON)
    `uvm_field_int(hready,    UVM_ALL_ON)
    `uvm_field_int(hwdata,    UVM_ALL_ON)
    `uvm_field_int(hreadyout, UVM_ALL_ON)
    `uvm_field_int(hresp,     UVM_ALL_ON)
    `uvm_field_int(hrdata,    UVM_ALL_ON)
  `uvm_object_utils_end

  function new(string name = "ahb_trans");
    super.new(name);
  endfunction

endclass : ahb_trans


