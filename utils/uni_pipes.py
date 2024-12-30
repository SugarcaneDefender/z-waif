# This is our state manager. It can have a list of many options to control IO. Options are as follows;
# "Init" = Being Created
# "Idle" = Nothing is happening
# "TTS Process" = TTS Processing Message
# "RAG Process" = RAG Running and Processing
# "Thinking" = LLM Work
# "Speaking" = TTS Output
# "BAKED" = Done, delete process
#
# Pipe type respresents a variety of actions, such as "Talk", "Picture", "Discord Message"
#
# Comes with [current pipeflow spot, next pipeflow spot, pipe ID, pipe type, is_main_pipe]
# Pipes are not stored in a list, but simply passed as objects

import time
import API.Oogabooga_Api_Support
import main
import threading

import utils.settings

pipe_counter = 0 # This is just the total number of pipes created this session. Appends as pipe id
main_pipe_running = False

def start_new_pipe(desired_process, is_main_pipe):
    global pipe_counter, main_pipe_running
    pipe_counter += 1

    # Make our pipe
    this_pipe = ["Init", "None", pipe_counter, desired_process, is_main_pipe]
    if is_main_pipe:
        main_pipe_running = True

    # Make it and run in another thread for us
    new_pipe = threading.Thread(target=pipe_loop(this_pipe))
    new_pipe.daemon = True
    new_pipe.start()


# This is what continually runs a pipe. It will run, until the desired pipe reaches "BAKED"
def pipe_loop(this_pipe):
    global main_pipe_running

    # while not finished
    while this_pipe[0] != "BAKED":

        # Beeg switch for our next processes

        #
        # Main Functions
        if this_pipe[3] == "Main-Chat":
            main.main_converse()
            this_pipe[0] = "BAKED"

        elif this_pipe[3] == "Main-Next":
            main.main_next()
            this_pipe[0] = "BAKED"

        elif this_pipe[3] == "Main-Redo":
            main.main_undo()
            this_pipe[0] = "BAKED"

        elif this_pipe[3] == "Main-Soft-Reset":
            main.main_soft_reset()
            this_pipe[0] = "BAKED"

        elif this_pipe[3] == "Main-Alarm":
            main.main_alarm_message()
            this_pipe[0] = "BAKED"

        elif this_pipe[3] == "Main-View-Image":
            main.main_view_image()
            this_pipe[0] = "BAKED"

        elif this_pipe[3] == "Main-Blank":
            main.main_send_blank()
            this_pipe[0] = "BAKED"


        #
        # Hangout Mode
        elif this_pipe[3] == "Hangout-Loop":

            #
            # Run various parts for the hangout loop. Should have a main "deciding" function
            #

            # Breakout of this if we have ended hangout mode
            if not utils.settings.hangout_mode:
                this_pipe[0] = "BAKED"

        # Minirest for loop
        time.sleep(0.01)

    # Remove the fact that the main pipe is running; it is no longer doing so
    if this_pipe[4] == True:
        main_pipe_running = False

    # End the operation once the pipe is done baking
    return


def pipe_api_request(this_pipe):
    # Sleep on this while any other request is running

    while API.Oogabooga_Api_Support.is_in_api_request:
        time.sleep(0.03)


