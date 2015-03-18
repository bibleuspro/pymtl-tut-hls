#==============================================================================
# IteratorTranslationUnitFL_test
#==============================================================================

import pytest

from pymtl      import *
from pclib.test import TestSource, TestSink, TestMemory, mk_test_case_table
from pclib.ifcs import mem_msgs, MemMsg

from IteratorTranslationUnitFL import IteratorTranslationUnitFL as ITU
from IteratorMsg               import IteratorMsg
from CoprocessorMsg            import CoprocessorMsg

#------------------------------------------------------------------------------
# TestHarness
#------------------------------------------------------------------------------
class TestHarness( Model ):

  def __init__( s, TranslationUnit,
                src_msgs,  sink_msgs,
                src_delay, sink_delay,
                mem_delay ):

    # Local Parameters
    s.memreq_params  = mem_msgs.MemReqParams ( 32, 32 )
    s.memresp_params = mem_msgs.MemRespParams(     32 )

    # Interfaces
    cfg_ifc          = CoprocessorMsg(  5, 32, 32 )
    accel_ifc        = IteratorMsg   (         32 )
    mem_ifc          = MemMsg        (     32, 32 )

    # Go bit
    s.go             = Wire( 1 )

    # Instantiate Models
    s.src            = TestSource     ( accel_ifc.req.nbits, src_msgs, src_delay        )
    s.itu            = TranslationUnit( cfg_ifc, accel_ifc, mem_ifc                     )
    s.sink           = TestSink       ( accel_ifc.resp.nbits, sink_msgs, sink_delay     )
    s.mem            = TestMemory     ( s.memreq_params, s.memresp_params, 1, mem_delay )

    # Connect
    s.connect( s.src.out.msg,            s.itu.accel_ifc.req_msg )

    s.connect( s.itu.accel_ifc.resp_msg, s.sink.in_.msg          )
    s.connect( s.itu.accel_ifc.resp_val, s.sink.in_.val          )
    s.connect( s.itu.accel_ifc.resp_rdy, s.sink.in_.rdy          )

    s.connect( s.itu.mem_ifc.req_msg,    s.mem.reqs[0].msg       )
    s.connect( s.itu.mem_ifc.req_val,    s.mem.reqs[0].val       )
    s.connect( s.itu.mem_ifc.req_rdy,    s.mem.reqs[0].rdy       )

    s.connect( s.mem.resps[0].msg,       s.itu.mem_ifc.resp_msg  )
    s.connect( s.mem.resps[0].val,       s.itu.mem_ifc.resp_val  )
    s.connect( s.mem.resps[0].rdy,       s.itu.mem_ifc.resp_rdy  )

    @s.combinational
    def logic():
      s.itu.accel_ifc.req_val.value = s.src.out.val & s.go
      s.src.out.rdy.value           = s.itu.accel_ifc.req_rdy & s.go

  def done( s ):
    return s.src.done and s.sink.done

  def line_trace( s ):
    return  s.src.line_trace() + " > " + \
            s.itu.line_trace() + " > " + \
            s.sink.line_trace()

#------------------------------------------------------------------------------
# run_itu_test
#------------------------------------------------------------------------------
def run_itu_test( model, vec_base_addr, mem_array=None, dump_vcd = None ):

  # Elaborate
  model.vcd_file = dump_vcd
  model.elaborate()

  # Create a simulator
  sim = SimulationTool( model )

  # Load the memory
  if mem_array:
    model.mem.load_memory( mem_array )

  # Run simulation
  sim.reset()
  print

  # Start itu configuration
  sim.cycle()
  sim.cycle()

  # Init data structure
  model.itu.cfg_ifc.req_val.next      = 1
  model.itu.cfg_ifc.req_msg.data.next = vec_base_addr
  model.itu.cfg_ifc.req_msg.addr.next = 2
  model.itu.cfg_ifc.req_msg.id.next   = 1

  sim.cycle()
  sim.cycle()

  # End itu configuration
  model.itu.cfg_ifc.req_val.next      = 0

  sim.cycle()
  sim.cycle()

  # Allow source to inject messages
  model.go.next = 1

  while not model.done() and sim.ncycles < 80:
    sim.print_line_trace()
    sim.cycle()
  sim.print_line_trace()
  assert model.done()

  # Add a couple extra ticks so that the VCD dump is nicer
  sim.cycle()
  sim.cycle()
  sim.cycle()

#------------------------------------------------------------------------------
# mem_array_32bit
#------------------------------------------------------------------------------
# Utility function for creating arrays formatted for memory loading.
from itertools import chain
def mem_array_32bit( base_addr, data ):
  return [base_addr,
          list( chain.from_iterable([ [x,0,0,0] for x in data ] ))
         ]

#------------------------------------------------------------------------------
# Test src/sink messages
#------------------------------------------------------------------------------

req  = IteratorMsg( 32 ).req.mk_req
resp = IteratorMsg( 32 ).resp.mk_resp

def req_wr( ds_id, index, data ):
  return req( 1, ds_id, index, data )

def req_rd( ds_id, index, data ):
  return req( 0, ds_id, index, data )

def resp_wr( data ):
  return resp( 1, data )

def resp_rd(  data ):
  return resp( 0, data )

# preload the memory to known values
preload_mem_array = mem_array_32bit( 8, [1,2,3,4] )

# messages that assume memory is preloaded and test for the case using the
# data structure with an id value to be 1
basic_msgs = [
  req_rd( 1, 0, 0 ), resp_rd( 0x00000001 ),
  req_rd( 1, 1, 0 ), resp_rd( 0x00000002 ),
  req_rd( 1, 2, 0 ), resp_rd( 0x00000003 ),
  req_rd( 1, 3, 0 ), resp_rd( 0x00000004 ),
  req_wr( 1, 0, 7 ), resp_wr( 0x00000000 ),
  req_rd( 1, 0, 0 ), resp_rd( 0x00000007 ),
]

#-------------------------------------------------------------------------
# Test Case Table
#-------------------------------------------------------------------------

test_case_table = mk_test_case_table([
  (               "msgs       src_delay sink_delay vec_base"),
  [ "basic_0x0",  basic_msgs, 0,        0,         8 ],
  [ "basic_5x0",  basic_msgs, 5,        0,         8 ],
  [ "basic_0x5",  basic_msgs, 0,        5,         8 ],
  [ "basic_3x9",  basic_msgs, 3,        9,         8 ],
])

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table )
def test( test_params, dump_vcd ):

  run_itu_test( TestHarness(  ITU,
                              test_params.msgs[::2],
                              test_params.msgs[1::2],
                              test_params.src_delay,
                              test_params.sink_delay, 0 ),
                test_params.vec_base,
                preload_mem_array,
                dump_vcd )