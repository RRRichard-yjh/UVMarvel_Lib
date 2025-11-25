// APB monitor skeleton
//
// Observes APB transfers on the bus and reconstructs apb_trans
// items with simple protocol checks on the two-phase handshake.

import uvm_pkg::*;

class apb_monitor extends uvm_monitor;

    `uvm_component_utils(apb_monitor)

    // NOTE:
    //   The type placeholder `{apb_interface_name}` is expected to be
    //   replaced by a concrete virtual interface type (optionally with
    //   modport) when adapting the skeleton to a DUT.
    virtual {apb_interface_name} vif;

    uvm_analysis_port #(apb_trans) ap;

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(virtual {apb_interface_name})::get(this, "", "apb_vif", vif)) begin
            `uvm_fatal("APB_MON_NO_VIF",
                       $sformatf("Virtual interface must be set for: %s",
                                 get_full_name()))
        end
    endfunction

    // Main run phase: monitor APB transactions
    virtual task run_phase(uvm_phase phase);
        apb_trans    tr;
        bit [11:0]   addr;
        bit [31:0]   wdata;
        bit [31:0]   rdata;
        bit          write;

        forever begin
            // Wait for clock edge and check reset
            @(posedge vif.pclk);
            if (!vif.presetn) begin
                do @(posedge vif.pclk); while (!vif.presetn);
                `uvm_info("APB_MON", "Reset deasserted", UVM_MEDIUM)
                continue;
            end

            // Detect setup phase (psel high, penable low)
            if (vif.psel && !vif.penable) begin
                addr  = vif.paddr;
                wdata = vif.pwdata;
                write = vif.pwrite;

                @(posedge vif.pclk);
                
                // Strict protocol checking for enable phase
                if (!(vif.psel && vif.penable)) begin
                    `uvm_error("APB_MON_ERR",
                               $sformatf("APB protocol violation: expected psel && penable at enable phase"))
                    continue; 
                end

                if (!write) begin
                    rdata = vif.prdata;
                end else begin
                    rdata = '0;
                end

                // Create and populate transaction
                tr = apb_trans::type_id::create("tr", this);
                tr.addr  = addr;
                tr.wdata = wdata;
                tr.write = write;
                tr.rdata = rdata;

                // Send transaction to analysis port
                ap.write(tr);
                `uvm_info("APB_MON",
                          $sformatf("Observed transaction:\n%s",
                                    tr.sprint()),
                          UVM_HIGH)

                // Wait for end of transfer (psel or penable low)
                do @(posedge vif.pclk);
                while (vif.psel && vif.penable);
            end
        end
    endtask
 
endclass : apb_monitor


