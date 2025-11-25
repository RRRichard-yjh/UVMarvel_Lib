// APB bus interface skeleton
//
// This skeleton captures a simple APB-style two-phase (setup/access)
// handshake. When adapting, keep the overall structure intact but
// specialise signal names, widths and modports as needed.

interface apb_if (
    input  logic        pclk,
    input  logic        presetn
);

    // Request / control signals
    logic        psel;
    logic        penable;
    logic        pwrite;
    logic [11:0] paddr;

    // Data channel
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


