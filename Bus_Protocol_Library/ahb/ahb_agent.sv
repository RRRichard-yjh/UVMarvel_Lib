// AHB agent skeleton
//
// Combines driver, sequencer and monitor into a reusable UVM agent.

import uvm_pkg::*;

class ahb_agent extends uvm_agent;
  `uvm_component_utils(ahb_agent)

  ahb_driver    drv;
  ahb_monitor   mon;
  ahb_sequencer seqr;

  // See note in ahb_driver about the interface placeholder.
  virtual {ahb_interface_name} vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    if (!uvm_config_db#(virtual {ahb_interface_name})::get(this, "", "ahb_vif", vif)) begin
      `uvm_fatal("AHB_AGENT_NO_VIF",
                 $sformatf("Virtual interface must be set for: %s",
                           get_full_name()))
    end

    mon = ahb_monitor::type_id::create("mon", this);

    if (get_is_active() == UVM_ACTIVE) begin
      drv  = ahb_driver::type_id::create("drv", this);
      seqr = ahb_sequencer::type_id::create("seqr", this);
    end
  endfunction

  function void connect_phase(uvm_phase phase);
    if (get_is_active() == UVM_ACTIVE)
      drv.seq_item_port.connect(seqr.seq_item_export);
  endfunction

endclass : ahb_agent


