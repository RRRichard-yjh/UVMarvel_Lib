// File: apb_if.sv
interface apb_if (
    input  logic        pclk,
    input  logic        presetn
);

    logic        psel;
    logic        penable;
    logic        pwrite;
    logic [11:0] paddr;
    logic [31:0] pwdata;
    logic [31:0] prdata;

    // Driver clocking block: for driving signals to DUT
    clocking driver_cb @(posedge pclk);
        default input #1step output #1step;

        output psel;
        output penable;
        output pwrite;
        output paddr;
        output pwdata;

        input  prdata;
        input  presetn;
    endclocking

    // Monitor clocking block: for sampling signals from DUT
    clocking monitor_cb @(posedge pclk);
        default input #1step output #1step;

        input  psel;
        input  penable;
        input  pwrite;
        input  paddr;
        input  pwdata;
        input  prdata;
        input  presetn;
    endclocking

endinterface : apb_if




// File: apb_trans.sv
import uvm_pkg::*;

// APB transaction item
class apb_trans extends uvm_sequence_item;

    // APB address (12 bits in interface, 32 bits for UVM compatibility)
    rand bit [11:0] addr;

    // APB write data (32 bits)
    rand bit [31:0] wdata;

    // APB read data (32 bits)
    bit [31:0] rdata;

    // APB read/write control (1=write, 0=read)
    rand bit       write;

    // UVM automation
    `uvm_object_utils_begin(apb_trans)
        `uvm_field_int(addr,  UVM_ALL_ON)
        `uvm_field_int(wdata, UVM_ALL_ON)
        `uvm_field_int(rdata, UVM_ALL_ON)
        `uvm_field_int(write, UVM_ALL_ON)
    `uvm_object_utils_end

    // Constructor
    function new(string name = "apb_trans");
        super.new(name);
    endfunction

endclass : apb_trans



// File: apb_driver.sv
class apb_driver extends uvm_driver #(apb_trans);

    `uvm_component_utils(apb_driver)

    virtual {apb_interface_name} vif;

    function new(string name = "apb_driver", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(virtual {apb_interface_name})::get(this, "", "apb_vif", vif)) begin
            `uvm_fatal("APB_DRV_IF", $sformatf("[%s] Cannot get virtual interface 'vif' from config DB", get_full_name()))
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
        vif.paddr   <= addr;
        vif.pwdata  <= wdata;
        vif.pwrite  <= 1'b1;
        vif.psel    <= 1'b1;
        vif.penable <= 1'b0;
        @(posedge vif.pclk);

        vif.penable <= 1'b1;
        @(posedge vif.pclk);

        vif.psel    <= 1'b0;
        vif.penable <= 1'b0;
        vif.paddr   <= '0;
        vif.pwrite  <= 1'b0;
        vif.pwdata  <= '0;
    endtask

    task apb_read(input bit [11:0] addr, output bit [31:0] rdata);
        vif.paddr   <= addr;
        vif.pwrite  <= 1'b0;
        vif.psel    <= 1'b1;
        vif.penable <= 1'b0;
        vif.pwdata  <= '0;
        @(posedge vif.pclk);

        vif.penable <= 1'b1;
        @(posedge vif.pclk);

        rdata = vif.prdata;

        vif.psel    <= 1'b0;
        vif.penable <= 1'b0;
        vif.paddr   <= '0;
        vif.pwrite  <= 1'b0;
        vif.pwdata  <= '0;
    endtask

    // Main run phase
    virtual task run_phase(uvm_phase phase);
        apb_trans tr;
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


// File: apb_sequencer.sv
class apb_sequencer extends uvm_sequencer #(apb_trans);
  `uvm_component_utils(apb_sequencer)
  
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass : apb_sequencer


// File: apb_monitor.sv
class apb_monitor extends uvm_monitor;

    `uvm_component_utils(apb_monitor)

    virtual {apb_interface_name} vif;

    uvm_analysis_port #(apb_trans) ap;

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(virtual {apb_interface_name})::get(this, "", "apb_vif", vif)) begin
            `uvm_fatal("APB_MON_NO_VIF", $sformatf("Virtual interface must be set for: %s", get_full_name()))
        end
    endfunction

    // Main run phase: monitor APB transactions
    virtual task run_phase(uvm_phase phase);
        apb_trans tr;
        bit [11:0] addr;
        bit [31:0] wdata;
        bit [31:0] rdata;
        bit        write;

        forever begin
            @(posedge vif.pclk);
            if (!vif.presetn) begin
                do @(posedge vif.pclk); while (!vif.presetn);
                `uvm_info("APB_MON", "Reset deasserted", UVM_MEDIUM)
                continue;
            end

            if (vif.psel && !vif.penable) begin
                addr  = vif.paddr;
                wdata = vif.pwdata;
                write = vif.pwrite;

                @(posedge vif.pclk);
                
                if (!(vif.psel && vif.penable)) begin
					`uvm_error("APB_MON_ERR", $sformatf("APB protocol violation: expected psel && penable at enable phase"))
                    continue; 
                end

                if (!write) begin
                    rdata = vif.prdata;
                end else begin
                    rdata = '0;
                end

                tr = apb_trans::type_id::create("tr", this);
                tr.addr  = addr;
                tr.wdata = wdata;
                tr.write = write;
                tr.rdata = rdata;

                // Send transaction to analysis port
                ap.write(tr);
                `uvm_info("APB_MON", $sformatf("Observed transaction:\n%s", tr.sprint()), UVM_HIGH)

                do @(posedge vif.pclk);
                while (vif.psel && vif.penable);
            end
        end
    endtask
 
endclass : apb_monitor


// File: apb_agent.sv
class apb_agent extends uvm_agent;

    `uvm_component_utils(apb_agent)

    apb_driver      drv;
    apb_monitor     mon;
    apb_sequencer   seqr;

    virtual {apb_interface_name} vif;

    uvm_active_passive_enum is_active;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db#(virtual {apb_interface_name})::get(this, "", "apb_vif", vif)) begin
            `uvm_fatal("APB_AGENT_NO_VIF", $sformatf("Virtual interface must be set for: %s", get_full_name()))
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
