from typing import Any

import gradio as gr # type: ignore
import main
import utils.logging
import utils.settings
import utils.hotkeys
import utils.tag_task_controller
import utils.voice
import json

# Import the gradio theme color
with open("Configurables/GradioThemeColor.json", 'r') as openfile:
    gradio_theme_color = json.load(openfile)

based_theme = gr.themes.Base(
    primary_hue=gradio_theme_color,
    secondary_hue="indigo",
    neutral_hue="zinc",

)



with gr.Blocks(theme=based_theme, title="Z-Waif UI") as demo:

    #
    # CHAT
    #

    with gr.Tab("Chat"):

        #
        # Main Chatbox
        #

        chatbot = gr.Chatbot(height=540)

        with gr.Row():
            msg = gr.Textbox(scale=3)

            def respond(message: str, chat_history: list[str]|Any):

                # No send blank: use button for that!
                if message == "":
                    return ""

                main.main_web_ui_chat(message)

                # Retrieve the result now
                # message_reply = API.Oogabooga_Api_Support.receive()
                #
                # chat_history.append((message, message_reply))

                return ""   # Note: Removed the update to the chatbot here, as it is done anyway in the update_chat()!

            def update_chat():
                # Return whole chat, plus the one I have just sent
                if backend.currently_sending_message != "":

                    # Prep for viewing without metadata
                    chat_combine = backend.chat_history[-30:]
                    i = 0
                    while i < len(chat_combine):
                        chat_combine[i] = chat_combine[i][:2]
                        i += 1
                    chat_combine.append([backend.currently_sending_message, backend.currently_streaming_message])

                    return chat_combine[-30:]


                # Return whole chat, last 30
                else:
                    chat_combine = backend.chat_history[-30:]
                    i = 0
                    while i < len(chat_combine):
                        chat_combine[i] = chat_combine[i][:2]
                        i += 1

                    return chat_combine


            msg.submit(respond, [msg, chatbot], [msg])

            send_button = gr.Button(variant="primary", value="Send")
            send_button.click(respond, inputs=[msg, chatbot], outputs=[msg])

        demo.load(update_chat, every=0.05, outputs=[chatbot])

        #
        # Basic Mic Chat
        #

        def recording_button_click():

            utils.hotkeys.speak_input_toggle_from_ui()

            return


        with gr.Row():

            recording_button = gr.Button(value="Mic (Toggle)")
            recording_button.click(fn=recording_button_click)

            recording_checkbox_view = gr.Checkbox(label="Now Recording!")




        #
        # Buttons
        #

        with gr.Row():

            def regenerate():
                main.main_web_ui_next()
                return

            def send_blank():
                # Give us some feedback
                print("\nSending blank message...\n")

                # Send the blank
                main.main_web_ui_chat("")
                return

            def undo():
                main.main_undo()
                return

            button_regen = gr.Button(value="Reroll")
            button_blank = gr.Button(value="Send Blank")
            button_undo = gr.Button(value="Undo")

            button_regen.click(fn=regenerate)
            button_blank.click(fn=send_blank)
            button_undo.click(fn=undo)


        #
        # Autochat Settings
        #

        def autochat_button_click():

            # No toggle in hangout mode
            if utils.settings.hangout_mode:
                return

            utils.hotkeys.input_toggle_autochat_from_ui()

            return


        def change_autochat_sensitivity(autochat_sens):

            utils.hotkeys.input_change_listener_sensitivity_from_ui(autochat_sens)
            return


        with gr.Row():

            autochat_button = gr.Button(value="Toggle Auto-Chat")
            autochat_button.click(fn=autochat_button_click)

            autochat_checkbox_view = gr.Checkbox(label="Auto-Chat Enabled")

            autochat_sensitivity_slider = gr.Slider(minimum=4, maximum=144, value=16, label="Auto-Chat Sensitivity")
            autochat_sensitivity_slider.change(fn=change_autochat_sensitivity, inputs=autochat_sensitivity_slider)


        #
        # Semi-Auto Chat Settings
        #

        def semi_auto_chat_button_click():

            # No toggle in hangout mode
            if utils.settings.hangout_mode:
                return

            # Toggle
            utils.settings.semi_auto_chat = not utils.settings.semi_auto_chat

            # Disable
            utils.hotkeys.disable_autochat()

            return


        with gr.Row():
            semi_auto_chat_button = gr.Button(value="Toggle Semi-Auto Chat")
            semi_auto_chat_button.click(fn=semi_auto_chat_button_click)

            semi_auto_chat_checkbox_view = gr.Checkbox(label="Semi-Auto Chat Enabled")


        #
        # Hangout Mode
        #

        def hangout_mode_button_click():

            # Toggle (Handled in the hotkey script)
            utils.hotkeys.web_ui_toggle_hangout_mode()

            return

        with gr.Row():
            hangout_mode_button = gr.Button(value="Toggle Hangout Mode")
            hangout_mode_button.click(fn=hangout_mode_button_click)

            hangout_mode_checkbox_view = gr.Checkbox(label="Hangout Mode Enabled")


        def update_settings_view():
            return utils.hotkeys.get_speak_input(), utils.hotkeys.get_autochat_toggle(), utils.settings.semi_auto_chat, utils.settings.hangout_mode


        demo.load(update_settings_view, every=0.05,
                  outputs=[recording_checkbox_view, autochat_checkbox_view, semi_auto_chat_checkbox_view, hangout_mode_checkbox_view])






    #
    # VISUAL
    #

    if utils.settings.vision_enabled:
        with gr.Tab("Visual"):

            #
            # Take / Retake Image
            #

            with gr.Row():
                def take_image_button_click():
                    utils.hotkeys.view_image_from_ui()

                    return

                take_image_button = gr.Button(value="Take / Send Image")
                take_image_button.click(fn=take_image_button_click)


            #
            # Image Feed
            #

            with gr.Row():
                def cam_use_image_feed_button_click():
                    utils.settings.cam_use_image_feed = not utils.settings.cam_use_image_feed

                    return


                with gr.Row():
                    cam_use_image_feed_button = gr.Button(value="Check/Uncheck")
                    cam_use_image_feed_button.click(fn=cam_use_image_feed_button_click)

                    cam_use_image_feed_checkbox_view = gr.Checkbox(label="Use Image Feed (File Select)")


            #
            # Direct Talk
            #

            with gr.Row():
                def cam_direct_talk_button_click():
                    utils.settings.cam_direct_talk = not utils.settings.cam_direct_talk

                    return


                with gr.Row():
                    cam_direct_talk_button = gr.Button(value="Check/Uncheck")
                    cam_direct_talk_button.click(fn=cam_direct_talk_button_click)

                    cam_direct_talk_checkbox_view = gr.Checkbox(label="Direct Talk & Send")


            #
            # Reply After
            #

            with gr.Row():
                def cam_reply_after_button_click():
                    utils.settings.cam_reply_after = not utils.settings.cam_reply_after

                    return


                with gr.Row():
                    cam_reply_after_button = gr.Button(value="Check/Uncheck")
                    cam_reply_after_button.click(fn=cam_reply_after_button_click)

                    cam_reply_after_checkbox_view = gr.Checkbox(label="Post Reply / Reply After Image")



            #
            # Image Preview
            #

            with gr.Row():
                def cam_image_preview_button_click():
                    utils.settings.cam_image_preview = not utils.settings.cam_image_preview

                    return


                with gr.Row():
                    cam_image_preview_button = gr.Button(value="Check/Uncheck")
                    cam_image_preview_button.click(fn=cam_image_preview_button_click)

                    cam_image_preview_checkbox_view = gr.Checkbox(label="Preview before Sending")

            #
            # Capture screenshot
            #

            with gr.Row():
                def cam_capture_screenshot_button_click():
                    utils.settings.cam_use_screenshot = not utils.settings.cam_use_screenshot

                    return


                with gr.Row():
                    cam_capture_screenshot_button = gr.Button(value="Check/Uncheck")
                    cam_capture_screenshot_button.click(fn=cam_capture_screenshot_button_click)

                    cam_capture_screenshot_checkbox_view = gr.Checkbox(label="Capture Screenshot")

            def update_visual_view():
                return utils.settings.cam_use_image_feed, utils.settings.cam_direct_talk, utils.settings.cam_reply_after, utils.settings.cam_image_preview, utils.settings.cam_use_screenshot


            demo.load(update_visual_view, every=0.05,
                      outputs=[cam_use_image_feed_checkbox_view, cam_direct_talk_checkbox_view, cam_reply_after_checkbox_view, cam_image_preview_checkbox_view, cam_capture_screenshot_checkbox_view])



    #
    # SETTINGS
    #


    with gr.Tab("Settings"):

        #
        # Hotkeys
        #

        def hotkey_button_click():
            utils.settings.hotkeys_locked = not utils.settings.hotkeys_locked

            return


        with gr.Row():
            hotkey_button = gr.Button(value="Check/Uncheck")
            hotkey_button.click(fn=hotkey_button_click)

            hotkey_checkbox_view = gr.Checkbox(label="Disable Keyboard Shortcuts (Input Toggle Lock)")


        #
        # Shadowchats
        #

        with gr.Row():
            def shadowchats_button_click():
                utils.settings.speak_shadowchats = not utils.settings.speak_shadowchats

                return


            with gr.Row():
                shadowchats_button = gr.Button(value="Check/Uncheck")
                shadowchats_button.click(fn=shadowchats_button_click)

                shadowchats_checkbox_view = gr.Checkbox(label="Speak Typed Chats / Shadow Chats")


        #
        # Soft Reset
        #

        with gr.Row():
            def soft_reset_button_click():
                backend.soft_reset()

                return

            soft_reset_button = gr.Button(value="Chat Soft Reset")
            soft_reset_button.click(fn=soft_reset_button_click)


        #
        # Random Memory
        #

        with gr.Row():
            def random_memory_button_click():
                main.main_memory_proc()

                return

            soft_reset_button = gr.Button(value="Proc a Random Memory")
            soft_reset_button.click(fn=random_memory_button_click)


        #
        # RP Supression
        #

        with gr.Row():
            def supress_rp_button_click():
                utils.settings.supress_rp = not utils.settings.supress_rp

                return


            with gr.Row():
                supress_rp_button = gr.Button(value="Check/Uncheck")
                supress_rp_button.click(fn=supress_rp_button_click)

                supress_rp_checkbox_view = gr.Checkbox(label="Supress RP (as others)")


        #
        # Newline Cut
        #

        with gr.Row():
            def newline_cut_button_click():
                utils.settings.newline_cut = not utils.settings.newline_cut

                return


            with gr.Row():
                newline_cut_button = gr.Button(value="Check/Uncheck")
                newline_cut_button.click(fn=newline_cut_button_click)

                newline_cut_checkbox_view = gr.Checkbox(label="Cutoff at Newlines (Double Enter)")


        #
        # Asterisk Ban
        #

        with gr.Row():
            def asterisk_ban_button_click():
                utils.settings.asterisk_ban = not utils.settings.asterisk_ban

                return


            with gr.Row():
                asterisk_ban_button = gr.Button(value="Check/Uncheck")
                asterisk_ban_button.click(fn=asterisk_ban_button_click)

                asterisk_ban_checkbox_view = gr.Checkbox(label="Ban Asterisks")


        #
        # Token Limit Slider
        #

        with gr.Row():

            def change_max_tokens(tokens_count):

                utils.settings.max_tokens = tokens_count
                return


            token_slider = gr.Slider(minimum=20, maximum=2048, value=utils.settings.max_tokens, label="Max Chat Tokens / Reply Length")
            token_slider.change(fn=change_max_tokens, inputs=token_slider)



        #
        # Alarm Time
        #

        def alarm_button_click(input_time):

            utils.settings.alarm_time = input_time

            print("\nAlarm time set as " + utils.settings.alarm_time + "\n")

            return


        with gr.Row():
            alarm_textbox = gr.Textbox(value=utils.settings.alarm_time, label="Alarm Time")

            alarm_button = gr.Button(value="Change Time")
            alarm_button.click(fn=alarm_button_click, inputs=alarm_textbox)


        #
        # Language Model Preset
        #

        def model_preset_button_click(input_text):

            utils.settings.model_preset = input_text

            print("\nChanged model preset to " + utils.settings.model_preset + "\n")

            return


        with gr.Row():
            model_preset_textbox = gr.Textbox(value=utils.settings.model_preset, label="Model Preset Name")

            model_preset_button = gr.Button(value="Change Model Preset")
            model_preset_button.click(fn=model_preset_button_click, inputs=model_preset_textbox)




        def update_settings_view():

            return utils.settings.hotkeys_locked, utils.settings.speak_shadowchats, utils.settings.supress_rp, utils.settings.newline_cut, utils.settings.asterisk_ban


        demo.load(update_settings_view, every=0.05, outputs=[hotkey_checkbox_view, shadowchats_checkbox_view, supress_rp_checkbox_view, newline_cut_checkbox_view, asterisk_ban_checkbox_view])




    #
    # Tags / Tasks
    #

    with gr.Tab("Tags & Tasks"):

        #
        # Tasks

        cur_task_box = gr.Textbox(label="Current Task")

        def update_task_button_click(input_text):

            # Change the task-tag first
            utils.tag_task_controller.change_tag_via_task("Task-" + input_text)

            # Now swap the task
            utils.tag_task_controller.set_task(input_text)



        with gr.Row():
            cur_task_update_box = gr.Textbox(label="Set New Task")
            cur_task_update_button = gr.Button(value="Update Task")
            cur_task_update_button.click(fn=update_task_button_click, inputs=cur_task_update_box)

        previous_tasks_box = gr.Textbox(label="Previous Tasks", lines=7)


        #
        # Gaming Loop

        def update_gaming_loop():
            utils.settings.is_gaming_loop = not utils.settings.is_gaming_loop

        if utils.settings.gaming_enabled:

            with gr.Row():
                gaming_loop_button = gr.Button(value="Check/Uncheck")
                gaming_loop_button.click(fn=update_gaming_loop)

                gaming_loop_checkbox_view = gr.Checkbox(label="Gaming Loop")


        #
        # Tags

        cur_tags_box = gr.Textbox(label="Current Tags")

        def update_tags_button_click(new_tags):
            new_tags = new_tags.replace(" ", "")
            new_tags_list = new_tags.split(",")
            print(new_tags_list)

            utils.tag_task_controller.set_tags(new_tags_list)


        with gr.Row():
            cur_tags_update_box = gr.Textbox(label="Set New Tags")
            cur_tags_update_button = gr.Button(value="Update Tags")
            cur_tags_update_button.click(fn=update_tags_button_click, inputs=cur_tags_update_box)

        previous_tags_box = gr.Textbox(label="Previous Tags", lines=7)

        def update_tag_task_view():
            cantonese_task_list = ""
            for task in utils.settings.all_task_char_list:
                cantonese_task_list += task + "\n"

            cantonese_cur_tags_list = ""
            for tag in utils.settings.cur_tags:
                cantonese_cur_tags_list += tag + "\n"

            cantonese_all_tags_list = ""
            for tag in utils.settings.all_tag_list:
                cantonese_all_tags_list += tag + "\n"

            return utils.settings.cur_task_char, cantonese_task_list, cantonese_cur_tags_list, cantonese_all_tags_list

        def update_autogaming_check():
            return utils.settings.is_gaming_loop

        if utils.settings.gaming_enabled:
            demo.load(update_autogaming_check, every=0.05,
                      outputs=[gaming_loop_checkbox_view])

        demo.load(update_tag_task_view, every=0.05, outputs=[cur_task_box, previous_tasks_box, cur_tags_box, previous_tags_box])





    #
    # DEBUG
    #

    with gr.Tab("Debug"):
        debug_log = gr.Textbox(utils.logging.debug_log, lines=10, label="General Debug", autoscroll=True)
        rag_log = gr.Textbox(utils.logging.rag_log, lines=10, label="RAG Debug", autoscroll=True)
        kelvin_log = gr.Textbox(utils.logging.kelvin_log, lines=1, label="Random Temperature Readout")

        def update_logs():
            return utils.logging.debug_log, utils.logging.rag_log, utils.logging.kelvin_log

        demo.load(update_logs, every=0.05, outputs=[debug_log, rag_log, kelvin_log])



    #
    # LINKS
    #

    with gr.Tab("Links"):

        links_text = (
                      "Github Project:\n" +
                      "https://github.com/SugarcaneDefender/z-waif \n" +
                      "\n" +
                      "Documentation:\n" +
                      "https://docs.google.com/document/d/1qzY09kcwfbZTaoJoQZDAWv282z88jeUCadivLnKDXCo/edit?usp=sharing \n" +
                      "\n" +
                      "YouTube:\n" +
                      "https://www.youtube.com/@SugarcaneDefender \n" +
                      "\n" +
                      "Support more development on Ko-Fi:\n" +
                      "https://ko-fi.com/zwaif \n" +
                      "\n" +
                      "Email me for premium AI-waifu development, install, and assistance:\n" +
                      "zwaif77@gmail.com")

        rag_log = gr.Textbox(links_text, lines=14, label="Links")









def launch_demo():
    demo.launch(server_port=7864) # type: ignore

