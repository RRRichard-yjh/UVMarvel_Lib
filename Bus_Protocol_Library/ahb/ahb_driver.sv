// AHB driver skeleton
//
// This driver implements a simple two-phase AHB-style transfer with
// optional internal backpressure. When specialising, keep the overall
// control flow and handshake rules, but feel free to tune backpressure
// behaviour and logging.

import uvm_pkg::*;

class ahb_driver extends uvm_driver #(ahb_trans);
  `uvm_component_utils(ahb_driver)

  // NOTE:
  //   The type placeholder `{ahb_interface_name}` is expected to be
  //   replaced by a concrete virtual interface type (optionally with
  //   modport) when adapting the skeleton to a DUT.
  virtual {ahb_interface_name} vif;

  rand bit enable_backpressure = 0;
  rand int backpressure_cycles = 1;
  rand int backpressure_delay  = 1;

  function new(string name = "ahb_driver", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual {ahb_interface_name})::get(this, "", "ahb_vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface not set");
  endfunction

  task run_phase(uvm_phase phase);
    reset_signals();
    forever begin
      if (vif.reset_n) begin
        seq_item_port.get_next_item(req);
        drive_transfer(req);
        seq_item_port.item_done();
      end
      else begin
        @(posedge vif.reset_n);
        reset_signals();
      end
    end
  endtask

  task reset_signals();
    vif.hsel    <= 0;
    vif.haddr   <= 0;
    vif.htrans  <= 0;
    vif.hsize   <= 3'b010;
    vif.hwrite  <= 0;
    vif.hwdata  <= 0;
    vif.hready  <= 1;
  endtask

  task drive_transfer(ahb_trans tr);
    // Phase 1: drive address phase
    @(posedge vif.clk);
    vif.hsel    <= 1'b1;
    vif.haddr   <= tr.haddr;
    vif.htrans  <= (tr.htrans == ahb_trans::IDLE) ?
                    ahb_trans::IDLE :
                    ahb_trans::NONSEQ;
    vif.hsize   <= tr.hsize;
    vif.hwrite  <= tr.hwrite;
    vif.hwdata  <= tr.hwdata;
    vif.hready  <= 1'b1;

    // Phase 2: optional backpressure and wait for readyout
    this.randomize() with {
      enable_backpressure dist { 1 := 30, 0 := 70 };
      backpressure_delay  inside {[0:2]};
      backpressure_cycles inside {[1:3]};
    };
    `uvm_info("DRV",
              $sformatf("Starting transfer with backpressure=%b",
                        enable_backpressure),
              UVM_HIGH)

    fork
      begin : backpressure_thread
        if (enable_backpressure) begin
          repeat (backpressure_delay) @(posedge vif.clk);
          `uvm_info("DRV", "Asserting backpressure", UVM_MEDIUM)
          vif.hready <= 1'b0;

          repeat (backpressure_cycles) @(posedge vif.clk);
          `uvm_info("DRV", "Releasing backpressure", UVM_MEDIUM)
          vif.hready <= 1'b1;
        end
      end

      begin : transfer_thread
        do begin
          @(posedge vif.clk);
          if (!vif.hreadyout) begin
            vif.htrans <= 2'b00; // BUSY / IDLE insertion when slave not ready
          end
        end while (!vif.hreadyout);
      end
    join

    // Phase 3: transfer completion
    wait (vif.hreadyout == 1'b1);
    repeat (2) @(posedge vif.pclk);

    if (!tr.hwrite) begin
      tr.hrdata = vif.hrdata;
      `uvm_info("AHB_DRIVER",
                $sformatf("Sampled hrdata=0x%0h", tr.hrdata),
                UVM_HIGH)
    end

    vif.hsel   <= 1'b0;
    vif.htrans <= 2'b00;
    vif.hready <= 1'b1;

    tr.hresp = vif.hresp;
    `uvm_info("DRV", "Transfer completed", UVM_HIGH)
  endtask

endclass : ahb_driver


