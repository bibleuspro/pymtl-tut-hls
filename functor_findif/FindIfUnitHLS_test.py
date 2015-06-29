#=============================================================================
# FindIfUnitHLS_test.py
#=============================================================================
# XXX: Check accel-id returned in responses

import pytest
import struct

from pymtl      import *
from pclib.test import TestSource, TestSink, mk_test_case_table

from dstu.MemMsgFuture              import MemMsg
from dstu.TestMemoryOpaque          import TestMemory
from dstu.IteratorTranslationUnitFL import IteratorTranslationUnitFL as ITU
from dstu.IteratorMsg               import IteratorMsg
from dstu.XcelMsg                   import XcelMsg
from dstu.UserTypes                 import Point

from poly_findif.FindIfUnitFL_test  import *
from FindIfUnitHLS                  import FindIfUnitHLS
from EqZero                         import EqZero

#------------------------------------------------------------------------------
# TestHarness
#------------------------------------------------------------------------------
class TestHarness( Model ):

  def __init__( s, FindIfUnit, TranslationUnit, ProcessingElement,
                src_msgs,  sink_msgs,
                src_delay, sink_delay,
                stall_prob, latency,
                dump_vcd=False ):

    # Interfaces
    asu_cfg_ifc = XcelMsg()
    asu_itu_ifc = IteratorMsg (32)
    itu_cfg_ifc = XcelMsg()
    mem_ifc     = MemMsg (8,32,32)

    # Go bit
    s.go = Wire( 1 )

    # Instantiate Models
    s.src = TestSource( asu_cfg_ifc.req, src_msgs, src_delay )
    s.asu = FindIfUnit( )
    s.itu = TranslationUnit( itu_cfg_ifc, asu_itu_ifc, mem_ifc )
    s.pe  = ProcessingElement ( )
    s.sink = TestSink( asu_cfg_ifc.resp, sink_msgs, sink_delay )
    s.mem = TestMemory( mem_ifc, 2, stall_prob, latency )

    # Connect

    # src <-> asu
    s.connect( s.src.out.msg, s.asu.cfgreq.msg )
    s.connect( s.asu.cfgresp, s.sink.in_ )

    # asu <-> mem
    #s.connect( s.asu.memreq,   s.mem.reqs[0] )
    s.connect( s.asu.memreq.val,   s.mem.reqs[0].val )
    s.connect( s.asu.memreq.rdy,   s.mem.reqs[0].rdy )
    s.connect( s.asu.memresp,  s.mem.resps[0] )

    # asu <-> itu
    #s.connect( s.asu.itureq,   s.itu.xcelreq ) 
    s.connect( s.asu.ituresp, s.itu.xcelresp  )
    s.connect( s.asu.itureq.val, s.itu.xcelreq.val)
    s.connect( s.asu.itureq.rdy, s.itu.xcelreq.rdy)

    # asu <-> pe
    s.connect( s.asu.pereq,  s.pe.xcelreq )
    s.connect( s.asu.peresp, s.pe.xcelresp )

    # itu <-> mem
    s.connect( s.itu.memreq,   s.mem.reqs[1]  )
    s.connect( s.itu.memresp,  s.mem.resps[1] )

    # asu -> itu convert Bits to BitStruct
    @s.combinational
    def convert():
      s.itu.xcelreq.msg.value = asu_itu_ifc.req.unpck( s.asu.itureq.msg )
      s.mem.reqs[0].msg.value = mem_ifc.req.unpck( s.asu.memreq.msg )

    # testbench -> asu request bundle var/rdy signals
    @s.combinational
    def logic():
      s.asu.cfgreq.val.value = s.src.out.val & s.go
      s.src.out.rdy.value    = s.asu.cfgreq.rdy & s.go

  def done( s ):
    return s.src.done and s.sink.done

  def line_trace( s ):
            #s.itu.line_trace() + " > " + \
    return  s.src.line_trace() + " > " + \
            s.asu.line_trace() + " > " + \
            s.mem.line_trace() + " > " + \
            s.sink.line_trace() + " > "

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table )
def test( test_params, dump_vcd ):

  run_asu_test( TestHarness(  FindIfUnitHLS,
                              ITU,
                              EqZero,
                              test_params.msgs[::2],
                              test_params.msgs[1::2],
                              test_params.src,
                              test_params.sink,
                              test_params.stall,
                              test_params.lat ),
                test_params.mem,
                test_params.ds,
                dump_vcd )
