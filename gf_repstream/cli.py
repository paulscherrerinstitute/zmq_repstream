import argparse
import logging
import os
import sys
import pkgutil
from functools import partial
from threading import Thread
from collections import deque
from time import time, sleep

from gf_repstream import __version__
from gf_repstream.receiver import Receiver
from gf_repstream.streamer import Streamer
# from gf_repstream.custom_queue import PriorityQueue

Log_Format = "%(levelname)s %(asctime)s - %(message)s"

logging.basicConfig(format=Log_Format, level=logging.ERROR, stream = sys.stdout)
logger = logging.getLogger(__name__)


def main():
    """The gf stream send command line interface.
    This is a tool to receive the incoming gigafrost stream and replicate it
    to external components.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))

    # Prepare argument parser
    parser = argparse.ArgumentParser(
        prog="gf_repstream", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    parser.add_argument(
        "--in-address",
        metavar="PROTOCOL://HOST:PORT",
        type=str,
        default="tcp://xbl-daq-23:9990",
        help="an address string for zmq socket",
    )

    parser.add_argument(
        "--out-init-port",
        metavar="PROTOCOL://HOST:PORT",
        type=int,
        default="9610",
        help="the initial port for the output streams (increased by 1 for every other stream)",
    )

    parser.add_argument(
        "--io-threads",
        type=int,
        default=1,
        help="the size of the zmq thread pool to handle I/O operations",
    )

    parser.add_argument(
        "--buffer-size",
        type=int,
        default=100,
        help="a number of last received zmq messages to keep in memory",
    )

    parser.add_argument(
        "--n-output-streams",
        type=int,
        default=0,
        help="number of output streams to be generated",
    )
    
    parser.add_argument(
        "--send-every-nth",
        nargs='+',
        type=int,
        help="list containing the frequency of each output stream to be generated",
    )


    args = parser.parse_args()

    _sentinel = object()

    q_list = []
    streamer_list = []
    receiver_tuples = []

    if args.n_output_streams == 0:
        raise RuntimeError("Number of output streams must be greater than zero. Halting execution of gf_repstream.")
    if args.n_output_streams != len(args.send_every_nth):
        raise RuntimeError("Number of output streams must be identical to the length of the send_every_nth list. Halting execution of gf_repstream.")



    for i in range(args.n_output_streams):
        # deque for each output stream
        q_list.append(deque(maxlen=args.buffer_size))
        # stramer outputs the replicated zmq stream 
        streamer_list.append(Streamer(name=f'output_{i}', deque=q_list[-1]))
        receiver_tuples.append((q_list[-1], args.send_every_nth[i]))
    # Receiver gets messages via zmq stream
    receiver = Receiver(tuples_list=receiver_tuples, sentinel=_sentinel)


    # streamer_writer = Streamer(name='writer', deque=q_writer)
    # streamer_preview = Streamer(name='preview', deque=q_preview)
    # streamer_analysis = Streamer(name='analysis', deque=q_analysis)
    

    # receiver
    start_receiver = partial(receiver.start, args.io_threads, args.in_address)
    r = Thread(target=start_receiver, daemon=True)
    
    list_threads = []
    init_port = args.out_init_port
    for i in range(args.n_output_streams):
        start_streamer_thread = partial(streamer_list[i].start, args.io_threads, 'tcp://*:'+str(init_port))
        init_port += 1
        list_threads.append(Thread(target=start_streamer_thread, daemon=True))

    # streamer writer
    # start_streamer_writer = partial(streamer_writer.start, args.io_threads, 'tcp://*:9610')
    # s_writer = Thread(target=start_streamer_writer, daemon=True)
    
    # # streamer live preview
    # start_streamer_preview = partial(streamer_preview.start, args.io_threads, 'tcp://*:9611')
    # s_preview = Thread(target=start_streamer_preview, daemon=True)

    # # streamer analysis
    # start_streamer_analysis = partial(streamer_analysis.start, args.io_threads, 'tcp://*:9612')
    # s_analysis = Thread(target=start_streamer_analysis, daemon=True)

    # Main application - starting receiver and streamers
    r.start()
    for i in range(args.n_output_streams):
        list_threads[i].start()
    # s_writer.start()
    # s_preview.start()
    # s_analysis.start()


    try:
        while True:
            pass
    except KeyboardInterrupt:
        _sentinel = None
        sleep(1)
        logger.info('^C pressed... exiting gf_repstream')
        print('^C pressed... exiting gf_repstream')

    # finishes the application
    r.join()
    for i in range(args.n_output):
        list_threads[i].join()
    # s_writer.join()
    # s_preview.join()
    # s_analysis.join()

if __name__ == "__main__":
    main()