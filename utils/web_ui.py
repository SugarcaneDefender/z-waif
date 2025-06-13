import random

import gradio
import gradio as gr
import main
import API.api_controller
from utils import zw_logging
from utils import settings
from utils import hotkeys
from utils import tag_task_controller
from utils import voice
import json

#from API.api_controller import soft_reset
#from settings import speak_only_spokento

# Import the gradio theme color
with open("Configurables/GradioThemeColor.json", 'r') as openfile:
    gradio_theme_color = json.load(openfile)

based_theme = gr.themes.Base(
    primary_hue=gradio_theme_color,
    secondary_hue="indigo",
    neutral_hue="zinc",

)

# Button click handlers
def shadowchats_button_click():
    settings.speak_shadowchats = not settings.speak_shadowchats
    voice.force_cut_voice()  # Cut any ongoing speech
    return

def speaking_choice_button_click():
    settings.speak_only_spokento = not settings.speak_only_spokento
    return

def supress_rp_button_click():
    settings.supress_rp = not settings.supress_rp
    return

def newline_cut_button_click():
    settings.newline_cut = not settings.newline_cut
    return

def asterisk_ban_button_click():
    settings.asterisk_ban = not settings.asterisk_ban
    return

def hotkey_button_click():
    settings.hotkeys_locked = not settings.hotkeys_locked
    return

def change_max_tokens(tokens_count):
    settings.max_tokens = tokens_count
    return

def alarm_button_click(input_time):
    settings.alarm_time = input_time
    print(f"\nAlarm time set as {settings.alarm_time}\n")
    return

def model_preset_button_click(input_text):
    settings.model_preset = input_text
    print(f"\nChanged model preset to {settings.model_preset}\n")
    return

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

            def respond(message, chat_history):
                """Handle chat messages from the web UI"""
                # Handle blank messages through the blank button
                if message == "":
                    return ""

                # Send the message
                main.main_web_ui_chat(message)
                return ""

            def update_chat():
                """Update the chat display"""
                try:
                    # Return whole chat, plus the one currently being sent
                    if API.api_controller.currently_sending_message != "":
                        # Prep for viewing without metadata
                        chat_combine = API.api_controller.ooga_history[-30:]
                        chat_combine = [chat[:2] for chat in chat_combine]  # Take only first two elements
                        
                        # Add current message if it exists
                        current_msg = API.api_controller.currently_sending_message
                        current_response = API.api_controller.currently_streaming_message
                        if current_msg or current_response:
                            chat_combine.append([current_msg, current_response])
                        
                        return chat_combine[-30:]
                    else:
                        # Return last 30 messages of chat history
                        chat_combine = API.api_controller.ooga_history[-30:]
                        return [chat[:2] for chat in chat_combine]  # Take only first two elements
                except Exception as e:
                    zw_logging.log_error(f"Error updating chat: {str(e)}")
                    return []

            msg.submit(respond, [msg, chatbot], [msg])

            send_button = gr.Button(variant="primary", value="Send")
            send_button.click(respond, inputs=[msg, chatbot], outputs=[msg])

        demo.load(update_chat, every=0.05, outputs=[chatbot])

        #
        # Basic Mic Chat
        #

        def recording_button_click():

            hotkeys.speak_input_toggle_from_ui()

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
                """Regenerate the last response"""
                main.main_web_ui_next()
                return

            def send_blank():
                """Send a blank message through the web UI"""
                print("\nSending blank message...\n")
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
            if settings.hangout_mode:
                return

            hotkeys.input_toggle_autochat_from_ui()

            return


        def change_autochat_sensitivity(autochat_sens):
            
            if not isinstance(autochat_sens, int): #band-aid fix, but it just works TM
                autochat_sens = 4
            
            hotkeys.input_change_listener_sensitivity_from_ui(autochat_sens)
            return


        with gradio.Row():

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
            if settings.hangout_mode:
                return

            # Toggle
            settings.semi_auto_chat = not settings.semi_auto_chat

            # Disable
            hotkeys.disable_autochat()

            return


        with gradio.Row():
            semi_auto_chat_button = gr.Button(value="Toggle Semi-Auto Chat")
            semi_auto_chat_button.click(fn=semi_auto_chat_button_click)

            semi_auto_chat_checkbox_view = gr.Checkbox(label="Semi-Auto Chat Enabled")


        #
        # Hangout Mode
        #

        def hangout_mode_button_click():

            # Toggle (Handled in the hotkey script)
            hotkeys.web_ui_toggle_hangout_mode()

            return

        with gradio.Row():
            hangout_mode_button = gr.Button(value="Toggle Hangout Mode")
            hangout_mode_button.click(fn=hangout_mode_button_click)

            hangout_mode_checkbox_view = gr.Checkbox(label="Hangout Mode Enabled")


        # Define dummy/invisible components to avoid NameError
        shadowchats_checkbox_view = gr.Checkbox(visible=False)
        speaking_choice_checkbox_view = gr.Checkbox(visible=False)
        supress_rp_checkbox_view = gr.Checkbox(visible=False)
        newline_cut_checkbox_view = gr.Checkbox(visible=False)
        asterisk_ban_checkbox_view = gr.Checkbox(visible=False)
        hotkey_checkbox_view = gr.Checkbox(visible=False)
        max_tokens_slider = gr.Slider(visible=False)
        alarm_time_box = gr.Textbox(visible=False)
        model_preset_box = gr.Textbox(visible=False)


        def update_settings_view():
            """Update all settings views with current values."""
            return (
                settings.is_recording,
                settings.auto_chat,
                settings.semi_auto_chat,
                settings.hangout_mode,
                settings.speak_shadowchats,
                settings.speak_only_spokento,
                settings.supress_rp,
                settings.newline_cut,
                settings.asterisk_ban,
                settings.hotkeys_locked,
                settings.max_tokens,
                settings.alarm_time,
                settings.model_preset
            )


        demo.load(update_settings_view, every=0.06,
                  outputs=[recording_checkbox_view, autochat_checkbox_view, semi_auto_chat_checkbox_view, hangout_mode_checkbox_view, shadowchats_checkbox_view, speaking_choice_checkbox_view, supress_rp_checkbox_view, newline_cut_checkbox_view, asterisk_ban_checkbox_view, hotkey_checkbox_view, max_tokens_slider, alarm_time_box, model_preset_box])






    #
    # VISUAL
    #

    if settings.vision_enabled:
        with gr.Tab("Visual"):

            #
            # Take / Retake Image
            #

            with gr.Row():
                def take_image_button_click():
                    hotkeys.view_image_from_ui()

                    return

                take_image_button = gr.Button(value="Take / Send Image")
                take_image_button.click(fn=take_image_button_click)


            #
            # Image Feed
            #

            with gr.Row():
                def cam_use_image_feed_button_click():
                    settings.cam_use_image_feed = not settings.cam_use_image_feed

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
                    settings.cam_direct_talk = not settings.cam_direct_talk

                    return


                with gr.Row():
                    cam_direct_talk_button = gr.Button(value="Check/Uncheck")
                    cam_direct_talk_button.click(fn=cam_direct_talk_button_click)

                    cam_direct_talk_checkbox_view = gr.Checkbox(label="Direct Talk & Send")


            #
            # Reply After
            #

            # with gr.Row():
            #     def cam_reply_after_button_click():
            #         settings.cam_reply_after = not settings.cam_reply_after
            #
            #
            #     with gr.Row():
            #         cam_reply_after_button = gr.Button(value="Check/Uncheck")
            #         cam_reply_after_button.click(fn=cam_reply_after_button_click)
            #
            #         cam_reply_after_checkbox_view = gr.Checkbox(label="Post Reply / Reply After Image")



            #
            # Image Preview
            #

            with gr.Row():
                def cam_image_preview_button_click():
                    settings.cam_image_preview = not settings.cam_image_preview

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
                    settings.cam_use_screenshot = not settings.cam_use_screenshot

                    return


                with gr.Row():
                    cam_capture_screenshot_button = gr.Button(value="Check/Uncheck")
                    cam_capture_screenshot_button.click(fn=cam_capture_screenshot_button_click)

                    cam_capture_screenshot_checkbox_view = gr.Checkbox(label="Capture Screenshot")

            def update_visual_view():
                return settings.cam_use_image_feed, settings.cam_direct_talk, settings.cam_image_preview, settings.cam_use_screenshot


            demo.load(update_visual_view, every=0.1,
                      outputs=[cam_use_image_feed_checkbox_view, cam_direct_talk_checkbox_view, cam_image_preview_checkbox_view, cam_capture_screenshot_checkbox_view])



    #
    # SETTINGS
    #


    with gr.Tab("Settings"):
        # Create settings tab
        with gr.Row():
            with gr.Column():
                recording_checkbox_view = gr.Checkbox(label="Now Recording!", value=settings.is_recording)
                autochat_checkbox_view = gr.Checkbox(label="Auto-Chat Enabled", value=settings.auto_chat)
                semi_auto_chat_checkbox_view = gr.Checkbox(label="Semi-Auto Chat", value=settings.semi_auto_chat)
                hangout_mode_checkbox_view = gr.Checkbox(label="Hangout Mode", value=settings.hangout_mode)

            with gr.Column():
                shadowchats_checkbox_view = gr.Checkbox(label="Shadow Chats", value=settings.speak_shadowchats)
                speaking_choice_checkbox_view = gr.Checkbox(label="Only Speak When Spoken To", value=settings.speak_only_spokento)
                supress_rp_checkbox_view = gr.Checkbox(label="Suppress RP", value=settings.supress_rp)
                newline_cut_checkbox_view = gr.Checkbox(label="Newline Cut", value=settings.newline_cut)

            with gr.Column():
                asterisk_ban_checkbox_view = gr.Checkbox(label="Asterisk Ban", value=settings.asterisk_ban)
                hotkey_checkbox_view = gr.Checkbox(label="Hotkeys Locked", value=settings.hotkeys_locked)
                max_tokens_slider = gr.Slider(minimum=50, maximum=2000, value=settings.max_tokens, label="Max Tokens")
                alarm_time_box = gr.Textbox(label="Alarm Time", value=settings.alarm_time)
                model_preset_box = gr.Textbox(label="Model Preset", value=settings.model_preset)

        with gr.Row():
            with gr.Column():
                shadowchats_button = gr.Button(value="Toggle Shadow Chats")
                shadowchats_button.click(fn=shadowchats_button_click)

                speaking_choice_button = gr.Button(value="Toggle Speak Only When Spoken To")
                speaking_choice_button.click(fn=speaking_choice_button_click)

            with gr.Column():
                supress_rp_button = gr.Button(value="Toggle RP Suppression")
                supress_rp_button.click(fn=supress_rp_button_click)

                newline_cut_button = gr.Button(value="Toggle Newline Cut")
                newline_cut_button.click(fn=newline_cut_button_click)

            with gr.Column():
                asterisk_ban_button = gr.Button(value="Toggle Asterisk Ban")
                asterisk_ban_button.click(fn=asterisk_ban_button_click)

                hotkey_button = gr.Button(value="Toggle Hotkeys Lock")
                hotkey_button.click(fn=hotkey_button_click)

        # Update settings view
        demo.load(update_settings_view, every=0.06,
            outputs=[
                recording_checkbox_view,
                autochat_checkbox_view,
                semi_auto_chat_checkbox_view,
                hangout_mode_checkbox_view,
                shadowchats_checkbox_view,
                speaking_choice_checkbox_view,
                supress_rp_checkbox_view,
                newline_cut_checkbox_view,
                asterisk_ban_checkbox_view,
                hotkey_checkbox_view,
                max_tokens_slider,
                alarm_time_box,
                model_preset_box
            ])



    #
    # Tags / Tasks
    #

    with gr.Tab("Tags & Tasks"):

        #
        # Tasks

        cur_task_box = gr.Textbox(label="Current Task")

        def update_task_button_click(input_text):

            # Change the task-tag first
            tag_task_controller.change_tag_via_task("Task-" + input_text)

            # Now swap the task
            tag_task_controller.set_task(input_text)



        with gr.Row():
            cur_task_update_box = gr.Textbox(label="Set New Task")
            cur_task_update_button = gr.Button(value="Update Task")
            cur_task_update_button.click(fn=update_task_button_click, inputs=cur_task_update_box)

        previous_tasks_box = gr.Textbox(label="Previous Tasks", lines=7)


        #
        # Gaming Loop

        def update_gaming_loop():
            settings.is_gaming_loop = not settings.is_gaming_loop

        if settings.gaming_enabled:

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

            tag_task_controller.set_tags(new_tags_list)


        with gr.Row():
            cur_tags_update_box = gr.Textbox(label="Set New Tags")
            cur_tags_update_button = gr.Button(value="Update Tags")
            cur_tags_update_button.click(fn=update_tags_button_click, inputs=cur_tags_update_box)

        previous_tags_box = gr.Textbox(label="Previous Tags", lines=7)

        def update_tag_task_view():
            cantonese_task_list = ""
            for task in settings.all_task_char_list:
                cantonese_task_list += task + "\n"

            cantonese_cur_tags_list = ""
            for tag in settings.cur_tags:
                cantonese_cur_tags_list += tag + "\n"

            cantonese_all_tags_list = ""
            for tag in settings.all_tag_list:
                cantonese_all_tags_list += tag + "\n"

            return settings.cur_task_char, cantonese_task_list, cantonese_cur_tags_list, cantonese_all_tags_list

        def update_autogaming_check():
            return settings.is_gaming_loop

        if settings.gaming_enabled:
            demo.load(update_autogaming_check, every=0.05,
                      outputs=[gaming_loop_checkbox_view])

        demo.load(update_tag_task_view, every=0.1, outputs=[cur_task_box, previous_tasks_box, cur_tags_box, previous_tags_box])





    #
    # DEBUG
    #

    with gr.Tab("Debug"):
        debug_log = gr.Textbox(zw_logging.debug_log, lines=10, label="General Debug", autoscroll=True)
        rag_log = gr.Textbox(zw_logging.rag_log, lines=10, label="RAG Debug", autoscroll=True)
        kelvin_log = gr.Textbox(zw_logging.kelvin_log, lines=1, label="Random Temperature Readout")

        def update_logs():
            return zw_logging.debug_log, zw_logging.rag_log, zw_logging.kelvin_log

        demo.load(update_logs, every=0.1, outputs=[debug_log, rag_log, kelvin_log])



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
    port = 7864
    print(f"Web UI available at http://localhost:{port}")
    demo.launch(server_port=port)

