// APB sequencer skeleton
//
// Thin wrapper sequencer for apb_trans items.

import uvm_pkg::*;

class apb_sequencer extends uvm_sequencer #(apb_trans);
  `uvm_component_utils(apb_sequencer)
  
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

endclass : apb_sequencer


