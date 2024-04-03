import subprocess
import sys
from base.option_descriptor import OptionDescriptor
from base.input_program import InputProgram
from platforms.desktop.desktop_service import DesktopService
from specializations.dlv2.dlv2_answer_sets import DLV2AnswerSets
from io import StringIO, TextIOWrapper
from threading import Thread
from time import sleep

class IncrementalDLV2DesktopService(DesktopService):
    def __init__(self, exe_path):
        super(IncrementalDLV2DesktopService, self).__init__(exe_path)
        self.error = ""
        self._stdout=""
        self._stderr=""
        self.solver_process = None
        self.stop=False
        self.run_grounder_process()

    def run_grounder_process(self):
        try:
            option = ""
            '''
            for o in options:
                if o is not None:
                    option += o.options
                    option += o.separator
                else:
                    print("Warning : wrong", type(OptionDescriptor).__name__, file=sys.stderr)
            '''
            option += "--stdin"
            print(self._exe_path)
            self.solver_process = subprocess.Popen([self._exe_path], 
                                                   stdin=subprocess.PIPE,
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE,
                                                   universal_newlines=True)
            self.solver_process.stdin.write(option)
            Thread(target=self.proc_errors).start()
            Thread(target=self.proc_output).start()
        except subprocess.CalledProcessError as e:
            print(e)
        except OSError as e:
            print(e)

    def proc_errors(self):
        while not self.stop:
            self._stderr+=self.solver_process.stderr.readline()
            print(self._stderr)
    
    def proc_output(self):
        while not self.stop:
            self._stdout+=self.solver_process.stdout.readline()
            print(self._stdout)

    def load_program(self, program, background):
        try:
            if program is not None:
                writer = self.solver_process.stdin
                if program.get_files_paths():
                    print("loading",program.get_files_paths()[0])
                    to_print = "<load path=\"" + program.get_files_paths()[0] + "\""
                    if background:
                        to_print += " background=\"true\""
                    writer.write(to_print + "/>\n")
            else:
                print("Warning : wrong", type(InputProgram).__name__, file=sys.stderr)
        except Exception as ex:
            print("failed loading")
            print(ex)

    def get_output(self, output, error):
        return DLV2AnswerSets(output, error)

    def start_sync(self, programs, options):
        writer = self.solver_process.stdin
        solver_output = ""
        solver_error = ""

        try:
            if programs:
                writer.write("<run/>\n")
                writer.flush()

            while not self._stderr and "<END>\n" not in self._stdout and not self.solver_process.poll():
                continue
            print("poll",self.solver_process.poll())

            solver_error = self._stderr
            if solver_error:
                print("error")
                print(solver_error)
            elif self.solver_process.poll() is not None:
                return self.get_output("", "") 
            return self.get_output(solver_output, solver_error)
        except Exception as e:
            print("Error in start sync")
            print(e)

        return self.get_output("", "")

    def stop_grounder_process(self):
        try:
            self.stop=True
            if self.solver_process.poll() is not None:
                return
            print("exiting")
            writer = self.solver_process.stdin
            writer.write("<exit/>")
        except subprocess.CalledProcessError as e:
            print(e)
        except OSError as e:
            print(e)
