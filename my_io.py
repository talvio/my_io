import time
import difflib
import os
import re

if "PYTEST_VERSION" in os.environ:
    MESSAGE_FLASH_TIME: Final = 0
    PYTEST_RUNNING:     Final = True
    STEP_DELAY = 0
else:
    MESSAGE_FLASH_TIME: Final = 2
    PYTEST_RUNNING:     Final = False
    STEP_DELAY = 0.1

UPDATE:                 Final = ("U","u","Update","update")

## Directories and files
MY_IO_DIR:              Final = "./" #"/Users/talvio/Nextcloud/projects/my_io/"
TEST_DATA_DIR:          Final = MY_IO_DIR + "test_data/"
IO_RECORDING_FILE = TEST_DATA_DIR + "my_io_recorded"
DIFF_FILE_EXTENSION = ".diff"

## Default behaviour when imported
RUN_RECORDED_SESSION = True
RECORD_ADDITIONAL_IO = False
RERECORD_OUTPUT = False


""" InputOutputAndTest captures all print and input commands. 
    For testing, it can 
    1. record all inputs and outputs to a file io_recording_file when record_additional_io = True
       If there was already previous session recorded to that file, this will append additional IO to the end of the file
    2. When run_recorded = True, rather than ask the user for input, the InputOutputAndTest will run the previous recorded
       session from io_recording_file and compare to the output in that previous recording. If the output does not match, 
       it will result in a RuntimeError. If record_additional_io = True and the previous session does not end in program exit, 
       user can continue recording more.
    3. When the program changes and the previously recorded output no longer matches the recorded output, you can set 
       rerecord_output = True and re-record the output with the previous session inputs. Then you can naturally use the new
       output for testing again, set erecord_output = False and run_recorded = True

    All of this makes testing the UserInterface code with pytest possible. 
    You can have several library_file and io_recording_file combinations to divide testing the program to smaller and different
    test sessions. Rerunning them automatically after every change is then trivial. 

    The recording file format is simple. Every input starts with I: Every following output line starts with O: and is a reaction 
    to the previous input up to the next input line, starting with I: again. 
"""


class InputOutputAndTest:
    def __init__(self, io_recording_file = IO_RECORDING_FILE, run_recorded = RUN_RECORDED_SESSION, record_additional_io = RECORD_ADDITIONAL_IO, rerecord_output = RERECORD_OUTPUT):
        self.io_recording_file = io_recording_file
        self.run_recorded = run_recorded
        self.record_additional_io = record_additional_io
        self.rerecord_output = rerecord_output
        self.input_count = 0

        self.my_input_fifo = []
        self.my_observed_output = [""]
        self.my_recorded_output = [""]
        self.recorded_input = None

        if self.run_recorded:
            self.load_recorded_io()
            self.diff_file = io_recording_file + DIFF_FILE_EXTENSION
            self.restart_diff_file()
        if self.rerecord_output:
            self.restart_recording_file()

    def load_recorded_io(self):
        if not os.path.isfile(self.io_recording_file): 
            with open(self.io_recording_file, 'w') as f:
                f.close
        with open(self.io_recording_file, 'r') as f:
            line = None
            line = f.readline()
            while line != "":
                line_no_eol = line[:-1]
                if line_no_eol[0] == "I":
                    input_length = re.match(r"^I\([0-9]+\):",line_no_eol)
                    if input_length:
                        input_length = input_length.end()
                    else:
                        input_length = 2
                    print(line_no_eol)
                    print(line_no_eol[input_length:])
                    self.my_input_fifo.append(line_no_eol[input_length:])
                    self.my_recorded_output.append("")
                elif line_no_eol[0] == "O": 
                    self.my_recorded_output[-1] += line_no_eol[2:] + "\n"
                else:
                    raise RuntimeError("Recorded IO file is corrupted!")
                line = f.readline()
        
    def restart_recording_file(self):
        with open(self.io_recording_file, 'w') as f:
            f.close

    def restart_diff_file(self):
        with open(self.diff_file, 'w') as f:
            f.close

    def my_print(self, string = ""):
            print(string)
            self.my_observed_output[-1] += string + "\n"
            if (self.record_additional_io and self.my_input_fifo == []) or self.rerecord_output:
                string = string.replace("\n","\nO:")
                with open(self.io_recording_file, 'a', encoding="utf-8") as f:
                    f.write("O:" + string + "\n")
                f.close

    def update_recording(self, input_count, recorded_input, latest_observed_output):
        new_input = input(f"Change the input or press ENTER to keep the old [{recorded_input}]") or recorded_input
        self.io_recording_file
        self.input_count
        with open(self.io_recording_file, 'r') as f:
            line = None
            line = f.readline()
            while line != "":
                line_no_eol = line[:-1]
                line = f.readline()
        f.close
        return

    def compare_output(self, recorded_input = None):
        latest_recorded_output = self.my_recorded_output.pop(0)
        if latest_recorded_output not in self.my_observed_output[-2]:
            os.system('clear')
            print("OUTPUT does not match RECORDED output!")
            print("Difference: ")
            difference_all = difflib.ndiff(latest_recorded_output.splitlines(keepends=True), self.my_observed_output[-2].splitlines(keepends=True))
            difference_to_show = ""
            for diff in difference_all:
            #   print(diff)
                if diff[:2] != "  ":
            #       print("Line: " + diff, end="")
                    difference_to_show += diff
            if PYTEST_RUNNING:
                raise RuntimeError(f"Output does not match recorded output!\nDIFFERENCE:\n{difference_to_show}\nRECORDED:\n{latest_recorded_output}\nOBSERVED:\n{self.my_observed_output[-2]}<-")
            else:
                with open(self.diff_file, 'a') as f:
                    self.my_observed_output[-2] = self.my_observed_output[-2].rstrip("\n")
                    self.my_observed_output[-2] = self.my_observed_output[-2].replace("\n","\nO:")
                    latest_recorded_output = latest_recorded_output.rstrip("\n")
                    latest_recorded_output = latest_recorded_output.replace("\n","\nR:")
                    f.write(f"INPUT({self.input_count}):{recorded_input}\n")
                    f.write(f"DIFFERENCE:\n{difference_to_show}\nRECORDED:\nR:{latest_recorded_output}\nOBSERVED:\n{self.my_observed_output[-2]}")
                    print(f"INPUT({self.input_count}):{recorded_input}\n")
                    print(f"DIFFERENCE:\n{difference_to_show}\nRECORDED:\nR:{latest_recorded_output}\nOBSERVED:\nO:{self.my_observed_output[-2]}")
                    time.sleep(STEP_DELAY)
                f.close
                what_next = input("Press ENTER to continue | (U)pdate recorded output to observed | Q + Enter to exit! ") or False
                if what_next in UPDATE:
                    self.update_recording(self.input_count, recorded_input, self.my_observed_output[-2])
                elif what_next == False:
                    exit()

    def my_input(self, question = "", default_input = (None, None)):
        self.my_observed_output[-1] = self.my_observed_output[-1] + question + "\n"
        self.my_observed_output.append("")
        if (self.rerecord_output or self.run_recorded) and self.my_input_fifo != []:
            if self.rerecord_output != True: 
                self.compare_output(self.recorded_input)
            self.recorded_input = self.my_input_fifo.pop(0)
            print(question + self.recorded_input)
            time.sleep(STEP_DELAY)
            answer = self.recorded_input
        else:
            if default_input == (None, None):
                answer =  input(question)
            else:
                answer =  input(question) or default_input
        question = question.replace("\n","\nO:")
        self.input_count += 1
        if (self.record_additional_io and self.my_input_fifo == []) or self.rerecord_output:
            with open(self.io_recording_file, 'a', encoding="utf-8") as f:
                f.write("O:" + question + "\n")
                f.write(f"I({self.input_count}):" + answer + "\n")
            f.close
        return answer


