############################################################
set top "top"
open_project hls.prj
set_top $top

add_files main.cpp
add_files -tb main.cpp

open_solution "solution1" -reset
config_interface -expose_global

set_part {xc7z020clg484-1}
create_clock -period 5

set_directive_interface -mode ap_hs $top ac.req
set_directive_interface -mode ap_hs $top ac.resp
set_directive_interface -mode ap_hs $top mem.req
set_directive_interface -mode ap_hs $top mem.resp
set_directive_interface -mode ap_hs $top g_dtu_iface.req
set_directive_interface -mode ap_hs $top g_dtu_iface.resp

csynth_design

cosim_design -rtl systemc -coverage -trace_level all

#export_design -evaluate verilog

file copy -force hls.prj/solution1/.autopilot/db/a.o.2.ll a.o.2.orig.ll
file copy -force hls.prj/solution1/sim/systemc/top_sc_trace_0.vcd top_sc_trace_0.vcd

exit