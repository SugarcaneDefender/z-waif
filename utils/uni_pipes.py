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
import API.api_controller
import main
import threading

from utils import settings
from utils import hotkeys
from utils import hangout
from utils import zw_logging

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

            # Begin with awaiting input
            while not hotkeys.SPEAK_TOGGLED:
                time.sleep(0.01)

                # Breakout of this if we have ended hangout mode
                if not settings.hangout_mode:
                    if not settings.hangout_mode:
                        this_pipe[0] = "BAKED"
                    continue

            #
            # Get conversation
            this_hangout_input = main.hangout_converse()

            # If our input is invalid, go back to the start of our loop
            if this_hangout_input == "Audio too short!" or this_hangout_input == "Audio error!":
                continue

            # add our appendables, if any
            this_hangout_input = hangout.hangout_interrupts_appendables + this_hangout_input

            #
            # Decide on how to reply to this message
            decided_reply_style = hangout.reply_decide(this_hangout_input)
            zw_logging.update_debug_log("Hangout reply has been decided as: " + decided_reply_style)

            #
            # Breakdown for what to do next

            if decided_reply_style == "Skip":
                # make sure that we append the skipped message!
                # implement this at some point ^^^
                print("Chose not to speak - skipping...")
                hangout.add_to_appendables(this_hangout_input)
                continue

            elif decided_reply_style == "Think":
                main.hangout_reply(this_hangout_input)

            elif decided_reply_style == "Think-Self":
                main.hangout_reply(this_hangout_input)

            elif decided_reply_style == "Reply":
                main.hangout_reply(this_hangout_input)

            elif decided_reply_style == "Force-Reply":
                main.hangout_reply(this_hangout_input)

            elif decided_reply_style == "Wait-Reply":
                main.hangout_reply(this_hangout_input)

            elif decided_reply_style == "Look":
                main.hangout_view_image_reply(this_hangout_input, True)

            elif decided_reply_style == "Look-Reply":
                main.hangout_view_image_reply(this_hangout_input, False)

            elif decided_reply_style == "Look-Think":
                main.hangout_view_image_reply(this_hangout_input, False)

            elif decided_reply_style.__contains__("Wait-Reply-"):
                decided_reply_style = decided_reply_style.removeprefix("Wait-Reply-")
                waiting_time = float(decided_reply_style)

                print("Waiting for " + str(decided_reply_style) + " seconds before reply!")

                cur_waiting_time = 0.97   # set the current waiting time (for previous calculation time)

                # Do the portion while waiting (and time it for bonuses)
                gen_timer = time.perf_counter()
                main.hangout_wait_reply_waitportion(this_hangout_input)
                gen_time_bonus = time.perf_counter() - gen_timer

                cur_waiting_time += gen_time_bonus

                # wait for a while (in a loop, waiting for input to be detected)
                while (not hotkeys.SPEAK_TOGGLED) and (cur_waiting_time < waiting_time):
                    cur_waiting_time += 0.0001
                    time.sleep(0.0001)

                # Case for speaking toggled (we go on, someone has started talking)
                if hotkeys.SPEAK_TOGGLED:
                    # make sure that we append the skipped message!
                    # implement this at some point ^^^
                    print("Audio heard - skipping...")
                    hangout.add_to_appendables(this_hangout_input)

                    # Clear out the latest chat if it is the one we just sent (it can slip in)
                    API.api_controller.pop_if_sent_is_latest(this_hangout_input)

                    continue

                else:
                    main.hangout_wait_reply_replyportion()

            else:
                # Reply, with nothing else
                main.hangout_reply(this_hangout_input)


            # Breakout of this if we have ended hangout mode
            if not settings.hangout_mode:
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

    while API.api_controller.is_in_api_request:
        time.sleep(0.03)


