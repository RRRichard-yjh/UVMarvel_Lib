// APB agent skeleton
//
// Combines driver, sequencer and monitor into a reusable UVM agent.

import uvm_pkg::*;

class apb_agent extends uvm_agent;

    `uvm_component_utils(apb_agent)

    apb_driver      drv;
    apb_monitor     mon;
    apb_sequencer   seqr;

    // See note in apb_driver about the interface placeholder.
    virtual {apb_interface_name} vif;

    uvm_active_passive_enum is_active;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db#(virtual {apb_interface_name})::get(this, "", "apb_vif", vif)) begin
            `uvm_fatal("APB_AGENT_NO_VIF",
                       $sformatf("Virtual interface must be set for: %s",
                                 get_full_name()))
        end

        if (!uvm_config_db#(uvm_active_passive_enum)::get(this, "", "is_active", is_active))
            is_active = UVM_ACTIVE;

        if (is_active == UVM_ACTIVE) begin
            seqr = apb_sequencer::type_id::create("seqr", this);
            drv  = apb_driver::type_id::create("drv", this);
        end
        mon = apb_monitor::type_id::create("mon", this);
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        // Connect sequencer to driver
        if (is_active == UVM_ACTIVE) begin
            drv.seq_item_port.connect(seqr.seq_item_export);
        end
    endfunction

endclass : apb_agent


