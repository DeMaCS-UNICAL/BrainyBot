from platforms.desktop.desktop_handler import DesktopHandler


class IncrementalDLV2DesktopHandler(DesktopHandler):
    """Handler specialization for desktop platforms."""

    def __init__(self, service):
        super(IncrementalDLV2DesktopHandler, self).__init__(service)
        self.__service = service

    def add_program(self, program, background=False):
        last_index=len(self._programs)
        self._programs[last_index]=program
        self.__service.load_program(program,background)
        return last_index
    
    def quit(self):
        self.__service.stop_grounder_process()

    def stop_process(self):
        try:
            if self.__service.solver_process!= None and self.__service.solver_process.start_time!=None and not self.__service.solver_process.has_exited:
                self.__service.solver_process.kill()
        except Exception as e:
            print(e)