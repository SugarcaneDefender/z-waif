import random

import gradio
import gradio as gr
import main
import API.Oogabooga_Api_Support
import utils.logging
import utils.settings
import utils.hotkeys


based_theme = gr.themes.Base(
    primary_hue="fuchsia",
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
        msg = gr.Textbox()

        def respond(message, chat_history):
            main.main_web_ui_chat(message)

            # Retrieve the result now
            message_reply = API.Oogabooga_Api_Support.receive_via_oogabooga()

            chat_history.append((message, message_reply))

            return "", API.Oogabooga_Api_Support.ooga_history[-30:]

        def update_chat():
            # Return whole chat, plus the one I have just sent
            if API.Oogabooga_Api_Support.currently_sending_message != "":

                chat_combine = API.Oogabooga_Api_Support.ooga_history[-30:]
                chat_combine.append([API.Oogabooga_Api_Support.currently_sending_message, ""])

                return chat_combine[-30:]


            # Return whole chat, last 30
            else:
                return API.Oogabooga_Api_Support.ooga_history[-30:]


        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        demo.load(update_chat, every=0.05, outputs=[chatbot])

        #
        # Basic Mic Chat
        #

        def recording_button_click():

            utils.hotkeys.speak_input_toggle_from_ui()

            return


        with gradio.Row():

            recording_button = gr.Button(value="Mic (Toggle)")
            recording_button.click(fn=recording_button_click)

            recording_checkbox_view = gr.Checkbox(label="Now Recording!")




        #
        # Buttons
        #

        with gradio.Row():

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

            utils.hotkeys.input_toggle_autochat_from_ui()

            return


        def change_autochat_sensitivity(autochat_sens):

            utils.hotkeys.input_change_listener_sensitivity_from_ui(autochat_sens)
            return


        with gradio.Row():

            autochat_button = gr.Button(value="Toggle Auto-Chat")
            autochat_button.click(fn=autochat_button_click)

            autochat_checkbox_view = gr.Checkbox(label="Auto-Chat Enabled")

            autochat_sensitivity_slider = gr.Slider(minimum=4, maximum=144, value=20, label="Auto-Chat Sensitivity")
            autochat_sensitivity_slider.change(fn=change_autochat_sensitivity, inputs=autochat_sensitivity_slider)





        def update_settings_view():
            return utils.hotkeys.get_speak_input(), utils.hotkeys.get_autochat_toggle()


        demo.load(update_settings_view, every=0.05,
                  outputs=[recording_checkbox_view, autochat_checkbox_view])




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


            def update_visual_view():
                return utils.settings.cam_use_image_feed, utils.settings.cam_direct_talk, utils.settings.cam_reply_after, utils.settings.cam_image_preview


            demo.load(update_visual_view, every=0.05,
                      outputs=[cam_use_image_feed_checkbox_view, cam_direct_talk_checkbox_view, cam_reply_after_checkbox_view, cam_image_preview_checkbox_view])



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
                API.Oogabooga_Api_Support.soft_reset()

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
        # Shadowchats
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

            return utils.settings.hotkeys_locked, utils.settings.speak_shadowchats, utils.settings.newline_cut


        demo.load(update_settings_view, every=0.05, outputs=[hotkey_checkbox_view, shadowchats_checkbox_view, newline_cut_checkbox_view])



    #
    # DEBUG
    #

    with gr.Tab("Debug / Log"):
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
    demo.launch(server_port=7864)

