// AHB monitor skeleton
//
// Observes transfers on the AHB interface and reconstructs ahb_trans
// items, performing a few lightweight protocol checks.

import uvm_pkg::*;

class ahb_monitor extends uvm_monitor;
  `uvm_component_utils(ahb_monitor)

  // See note in ahb_driver about the interface placeholder.
  virtual {ahb_interface_name} vif;
  uvm_analysis_port #(ahb_trans) ap;

  function new(string name, uvm_component parent);
    super.new(name, parent);
    ap = new("ap", this);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual {ahb_interface_name})::get(this, "", "ahb_vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface not set");
  endfunction

  task run_phase(uvm_phase phase);
    forever begin
      monitor_transfer();
    end
  endtask

  task monitor_transfer();
    ahb_trans tr;

    // Wait for a valid transfer start
    wait (vif.hsel &&
          (vif.htrans inside {2'b10, 2'b11}) &&
          vif.hready);

    tr = ahb_trans::type_id::create("tr");

    // Capture address phase
    tr.haddr  = vif.haddr;
    tr.hsize  = vif.hsize;
    tr.hwrite = vif.hwrite;

    fork
      begin : timeout_protect
        #20us;
        `uvm_error("MON", "AHB timeout violation")
      end

      begin : transfer_tracking
        // Address/control must remain stable while HREADY is low
        while (vif.htrans != 2'b00) begin
          @(posedge vif.clk);

          if (!vif.hready) begin
            if (vif.haddr != tr.haddr ||
                vif.hsize != tr.hsize)
              `uvm_error("MON",
                         "Protocol violation: Signals changed while HREADY=0")
          end
        end

        // Wait for data completion
        while (!vif.hreadyout) @(posedge vif.clk);

        tr.hrdata = vif.hrdata;
        tr.hresp  = vif.hresp;
      end
    join_any
    disable fork;

    // Simple data stability check
    if (tr.hwrite && tr.hwdata != vif.hwdata)
      `uvm_error("MON", "Write data changed during transfer")

    ap.write(tr);
  endtask

endclass : ahb_monitor


