import threading

from core.processor.processor_server import ProcessorServer

if __name__ == '__main__':
    server = ProcessorServer()

    threading.Thread(target=server.start_processor_server).start()
    server.loop_process()
