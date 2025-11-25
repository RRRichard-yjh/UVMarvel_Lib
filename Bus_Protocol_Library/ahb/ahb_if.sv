// AHB bus interface skeleton
//
// This skeleton captures the stable request/response and timing
// structure of a simple AHB-like bus. When adapting it to a DUT,
// keep the handshake/control behaviour the same and only change
// signal names, widths and modports as needed.
//
// Allowed modification region:
//   - Port list (signal names and widths)
//   - Internal logic declarations
//   - Clocking block signal lists and delays
//
// Avoid changing:
//   - The overall presence of separate driver_cb/monitor_cb blocks
//   - The basic separation of request/response signals

interface ahb_if (
	input  logic clk,
	input  logic reset_n
);

  // Request channel
  logic                   hsel;
  logic [11:0]            haddr;
  logic [1:0]             htrans;
  logic [2:0]             hsize;
  logic                   hwrite;
  logic                   hready;
  logic [31:0]            hwdata;

  // Response channel
  logic                   hreadyout;
  logic                   hresp;
  logic [31:0]            hrdata;

  // Clocking block for the driver
  clocking driver_cb @(posedge clk);
    default input #1ns output #1ns;
    output hsel, haddr, htrans, hsize, hwrite, hready, hwdata;
    input  hreadyout, hresp, hrdata;
  endclocking

  // Clocking block for the monitor
  clocking monitor_cb @(posedge clk);
    default input #1ns output #1ns;
    input  hsel, haddr, htrans, hsize, hwrite, hready, hwdata;
    input  hreadyout, hresp, hrdata;
  endclocking

endinterface : ahb_if


