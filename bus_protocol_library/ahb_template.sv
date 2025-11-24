// File: ahb_if.sv
interface ahb_if (
	input logic clk, 
	input logic reset_n
);
  
  logic                   hsel;
  logic [11:0]            haddr;
  logic [1:0]             htrans;
  logic [2:0]             hsize;
  logic                   hwrite;
  logic                   hready;
  logic [31:0]            hwdata;
  
  logic                   hreadyout;
  logic                   hresp;
  logic [31:0]            hrdata;
  
  clocking driver_cb @(posedge clk);
    default input #1ns output #1ns;
    output hsel, haddr, htrans, hsize, hwrite, hready, hwdata;
    input hreadyout, hresp, hrdata;
  endclocking
  
  clocking monitor_cb @(posedge clk);
    default input #1ns output #1ns;
    input hsel, haddr, htrans, hsize, hwrite, hready, hwdata;
    input hreadyout, hresp, hrdata;
  endclocking
  
endinterface : ahb_if


//File: ahb_trans.sv

import uvm_pkg::*;
class ahb_trans extends uvm_sequence_item;

  typedef enum bit [1:0] {
    IDLE  = 2'b00,
    BUSY  = 2'b01,
    NONSEQ = 2'b10,
    SEQ   = 2'b11
  } trans_t;
  
  trans_t htrans = IDLE;  

  logic               hsel;
  logic [11:0]        haddr;   
  //logic [1:0]         htrans;
  logic [2:0]         hsize;
  logic               hwrite;
  logic               hready;
  logic [31:0]        hwdata;
  
  // Output signals 
  logic               hreadyout;
  logic               hresp;
  logic [31:0]        hrdata;


   
  `uvm_object_utils_begin(ahb_trans)
    `uvm_field_int(hsel,     UVM_ALL_ON)
    `uvm_field_int(haddr,    UVM_ALL_ON)
    //`uvm_field_int(htrans,   UVM_ALL_ON)
    `uvm_field_enum(trans_t, htrans, UVM_ALL_ON)
    `uvm_field_int(hsize,    UVM_ALL_ON)
    `uvm_field_int(hwrite,   UVM_ALL_ON)
    `uvm_field_int(hready,   UVM_ALL_ON)
    `uvm_field_int(hwdata,   UVM_ALL_ON)
    `uvm_field_int(hreadyout,UVM_ALL_ON)
    `uvm_field_int(hresp,    UVM_ALL_ON)
    `uvm_field_int(hrdata,   UVM_ALL_ON)
  `uvm_object_utils_end
  
  function new(string name = "ahb_trans");
    super.new(name);
  endfunction

endclass : ahb_trans


// File: ahb_driver.sv

class ahb_driver extends uvm_driver #(ahb_trans);
  `uvm_component_utils(ahb_driver)
  
  virtual {ahb_interface_name} vif;
  
  rand bit   enable_backpressure = 0;  // Enable internal backpressure in Driver
  rand int   backpressure_cycles = 1;  // Number of backpressure cycles
  rand int   backpressure_delay = 1;   // Backpressure trigger delay
    
  function new(string name = "ahb_driver", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if(!uvm_config_db#(virtual {ahb_interface_name})::get(this, "", "ahb_vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface not set");
  endfunction
  
  task run_phase(uvm_phase phase);
    reset_signals();
    forever begin
      if(vif.reset_n) begin
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
    
    // Phase 1: Drive address phase
    @(posedge vif.clk);
    vif.hsel    <= 1'b1;
    vif.haddr   <= tr.haddr;
    vif.htrans  <= (tr.htrans == ahb_trans::IDLE) ? 
                             ahb_trans::IDLE : 
                             ahb_trans::NONSEQ;
    vif.hsize   <= tr.hsize;
    vif.hwrite  <= tr.hwrite;
    vif.hwdata  <= tr.hwdata;
    vif.hready  <= 1'b1; // Initially in ready state

    // Phase 2: Backpressure control and transfer waiting
	this.randomize() with {
        enable_backpressure dist { 1:=30, 0:=70 };
        backpressure_delay inside {[0:2]};
	    backpressure_cycles inside {[1:3]};
	
	};
    `uvm_info("DRV", $sformatf("Starting transfer with backpressure=%b", enable_backpressure), UVM_HIGH)
    
    fork
      begin : backpressure_thread
        if(enable_backpressure) begin
          repeat(backpressure_delay) @(posedge vif.clk);
          `uvm_info("DRV", "Asserting backpressure", UVM_MEDIUM)
          vif.hready <= 1'b0;
          
          repeat(backpressure_cycles) @(posedge vif.clk);
          `uvm_info("DRV", "Releasing backpressure", UVM_MEDIUM)
          vif.hready <= 1'b1;
        end
      end
      
      begin : transfer_thread
        do begin
          @(posedge vif.clk);
          if(!vif.hreadyout) begin
            vif.htrans <= 2'b00; // Insert BUSY state
          end
        end while(!vif.hreadyout);
      end
    join
    
	// Phase 3: Transfer completion	
	wait (vif.hreadyout == 1'b1);
    repeat(2)@(posedge vif.pclk);

	if (!tr.hwrite) begin
        tr.hrdata = vif.hrdata;
        `uvm_info("AHB_DRIVER", $sformatf("Sampled hrdata=0x%0h", tr.hrdata), UVM_HIGH)
    end

	vif.hsel   <= 1'b0;
    vif.htrans <= 2'b00;
    vif.hready <= 1'b1;
    
    tr.hresp = vif.hresp;
    
    `uvm_info("DRV", "Transfer completed", UVM_HIGH)
  endtask

 endclass : ahb_driver

 
// File: ahb_sequencer.sv
class ahb_sequencer extends uvm_sequencer #(ahb_trans);
  `uvm_component_utils(ahb_sequencer)
  
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

endclass : ahb_sequencer


// File: ahb_monitor.sv

class ahb_monitor extends uvm_monitor;
  `uvm_component_utils(ahb_monitor)
  
  virtual {ahb_interface_name} vif;
  uvm_analysis_port #(ahb_trans) ap;
  
  function new(string name, uvm_component parent);
    super.new(name, parent);
    ap = new("ap", this);
  endfunction
  
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if(!uvm_config_db#(virtual {ahb_interface_name})::get(this, "", "ahb_vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface not set");
  endfunction
  
  task run_phase(uvm_phase phase);
    forever begin
      monitor_transfer();
    end
  endtask
  
  task monitor_transfer();
    ahb_trans tr;
    
    wait(vif.hsel && 
        (vif.htrans inside {2'b10,2'b11}) &&
         vif.hready);
    
    tr = ahb_trans::type_id::create("tr");
    
    tr.haddr  = vif.haddr;
    tr.hsize  = vif.hsize;
    tr.hwrite = vif.hwrite;
    
    fork
        begin : timeout_protect
            #20us;
            `uvm_error("MON", "AHB timeout violation")
        end
        
        begin : transfer_tracking
            while(vif.htrans != 2'b00) begin
                @(posedge vif.clk);
                
                if(!vif.hready) begin
                    if(vif.haddr != tr.haddr || 
                       vif.hsize != tr.hsize)
                        `uvm_error("MON", "Protocol violation: Signals changed while HREADY=0")
                end
                
            end
            
            while(!vif.hreadyout) @(posedge vif.clk);
            
            tr.hrdata = vif.hrdata;
            tr.hresp  = vif.hresp;
        end
    join_any
    disable fork;
    
    if(tr.hwrite && tr.hwdata != vif.hwdata)
        `uvm_error("MON", "Write data changed during transfer")
    
    ap.write(tr);
  endtask
endclass : ahb_monitor


// File: ahb_agent.sv

class ahb_agent extends uvm_agent;
  `uvm_component_utils(ahb_agent)
  
  ahb_driver     drv;
  ahb_monitor    mon;
  ahb_sequencer  seqr;
    
  virtual {ahb_interface_name} vif;
  
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
  
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

	if (!uvm_config_db#(virtual {ahb_interface_name})::get(this, "", "ahb_vif", vif)) begin
            `uvm_fatal("AHB_AGENT_NO_VIF", $sformatf("Virtual interface must be set for: %s", get_full_name()))
    end

     
    mon = ahb_monitor::type_id::create("mon", this);
    
    if(get_is_active() == UVM_ACTIVE) begin
      drv = ahb_driver::type_id::create("drv", this);
      seqr = ahb_sequencer::type_id::create("seqr", this);
    end
  endfunction
  
  function void connect_phase(uvm_phase phase);
    if(get_is_active() == UVM_ACTIVE)
      drv.seq_item_port.connect(seqr.seq_item_export);
  endfunction

endclass : ahb_agent


