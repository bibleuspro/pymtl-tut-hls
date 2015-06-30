############################################################
set top "FindIfUnitHLS"
set prj "findif.prj"
open_project $prj
set_top $top

add_files $top\.cpp
add_files -tb $top\.cpp

open_solution "solution1" -reset
config_interface -expose_global

set_part {xc7z020clg484-1}
create_clock -period 5

set_directive_interface -mode ap_ctrl_none $top
set_directive_interface -mode ap_hs $top ac.req
set_directive_interface -mode ap_hs $top ac.resp
set_directive_interface -mode ap_hs $top mem.req
set_directive_interface -mode ap_hs $top mem.resp
set_directive_interface -mode ap_hs $top g_dstu_iface.req
set_directive_interface -mode ap_hs $top g_dstu_iface.resp

set_directive_data_pack $top ac.req
set_directive_data_pack $top ac.resp
set_directive_data_pack $top mem.req
set_directive_data_pack $top mem.resp
set_directive_data_pack $top g_dstu_iface.req
set_directive_data_pack $top g_dstu_iface.resp

csynth_design

#cosim_design -rtl systemc

#export_design -evaluate verilog

#file copy -force $prj\/solution1/.autopilot/db/a.o.2.ll a.o.2.orig.ll

set fout [open ./$top\.v w]
fconfigure $fout -translation binary
set vfiles [glob -nocomplain -type f $prj/solution1/syn/verilog/*.v]
foreach vfile $vfiles {
  set fin [open $vfile r]
  fconfigure $fin -translation binary
  fcopy $fin $fout
  close $fin
}

# add verilator lint off and on pragmas
seek $fout 0
puts -nonewline $fout "/* verilator lint_off WIDTH */\n\n//"
seek $fout -1 end
puts $fout "\n\n/* lint_on */"

close $fout

exit