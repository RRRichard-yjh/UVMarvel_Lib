// APB driver skeleton
//
// Implements the standard APB two-phase transfer (setup + access)
// using the apb_trans sequence item.

import uvm_pkg::*;

class apb_driver extends uvm_driver #(apb_trans);

    `uvm_component_utils(apb_driver)

    // NOTE:
    //   The type placeholder `{apb_interface_name}` is expected to be
    //   replaced by a concrete virtual interface type (optionally with
    //   modport) when adapting the skeleton to a DUT.
    virtual {apb_interface_name} vif;

    function new(string name = "apb_driver", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(virtual {apb_interface_name})::get(this, "", "apb_vif", vif)) begin
            `uvm_fatal("APB_DRV_IF",
                       $sformatf("[%s] Cannot get virtual interface 'vif' from config DB",
                                 get_full_name()))
        end
    endfunction

    task wait_for_reset_release();
        // Hold safe state during reset
        while (vif.presetn === 1'b0) begin
            vif.psel    <= 1'b0;
            vif.penable <= 1'b0;
            vif.paddr   <= '0;
            vif.pwrite  <= 1'b0;
            vif.pwdata  <= '0;
            @(posedge vif.pclk);
        end
        repeat (2) @(posedge vif.pclk);
    endtask

    // APB two-phase transfer: setup and access
    task apb_write(input bit [11:0] addr, input bit [31:0] wdata);
        // Setup phase
        vif.paddr   <= addr;
        vif.pwdata  <= wdata;
        vif.pwrite  <= 1'b1;
        vif.psel    <= 1'b1;
        vif.penable <= 1'b0;
        @(posedge vif.pclk);

        // Access phase
        vif.penable <= 1'b1;
        @(posedge vif.pclk);

        // End transfer
        vif.psel    <= 1'b0;
        vif.penable <= 1'b0;
        vif.paddr   <= '0;
        vif.pwrite  <= 1'b0;
        vif.pwdata  <= '0;
    endtask

    task apb_read(input bit [11:0] addr, output bit [31:0] rdata);
        // Setup phase
        vif.paddr   <= addr;
        vif.pwrite  <= 1'b0;
        vif.psel    <= 1'b1;
        vif.penable <= 1'b0;
        vif.pwdata  <= '0;
        @(posedge vif.pclk);

        // Access phase
        vif.penable <= 1'b1;
        @(posedge vif.pclk);

        // Sample read data
        rdata = vif.prdata;

        // End transfer
        vif.psel    <= 1'b0;
        vif.penable <= 1'b0;
        vif.paddr   <= '0;
        vif.pwrite  <= 1'b0;
        vif.pwdata  <= '0;
    endtask

    // Main run phase
    virtual task run_phase(uvm_phase phase);
        apb_trans tr;

        // Initial safe state
        vif.psel    <= 1'b0;
        vif.penable <= 1'b0;
        vif.paddr   <= '0;
        vif.pwrite  <= 1'b0;
        vif.pwdata  <= '0;

        forever begin
            wait_for_reset_release();

            seq_item_port.get_next_item(tr);

            if (tr.write) begin
                apb_write(tr.addr, tr.wdata);
            end else begin
                apb_read(tr.addr, tr.rdata);
            end

            seq_item_port.item_done();
        end
    endtask

endclass : apb_driver


