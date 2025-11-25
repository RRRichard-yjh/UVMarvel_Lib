// AHB sequencer skeleton
//
// Thin wrapper sequencer for ahb_trans items.

import uvm_pkg::*;

class ahb_sequencer extends uvm_sequencer #(ahb_trans);
  `uvm_component_utils(ahb_sequencer)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

endclass : ahb_sequencer


