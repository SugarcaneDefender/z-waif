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
    print(f"[Web-UI] Shadow Chats toggled -> {settings.speak_shadowchats}")
    voice.force_cut_voice()  # Cut any ongoing speech
    return

def speaking_choice_button_click():
    settings.speak_only_spokento = not settings.speak_only_spokento
    print(f"[Web-UI] Speak-only-when-spoken-to toggled -> {settings.speak_only_spokento}")
    return

def supress_rp_button_click():
    settings.supress_rp = not settings.supress_rp
    print(f"[Web-UI] Suppress RP toggled -> {settings.supress_rp}")
    return

def newline_cut_button_click():
    settings.newline_cut = not settings.newline_cut
    print(f"[Web-UI] Newline cut toggled -> {settings.newline_cut}")
    return

def asterisk_ban_button_click():
    settings.asterisk_ban = not settings.asterisk_ban
    print(f"[Web-UI] Asterisk ban toggled -> {settings.asterisk_ban}")
    return

def hotkey_button_click():
    settings.hotkeys_locked = not settings.hotkeys_locked
    print(f"[Web-UI] Hotkeys locked toggled -> {settings.hotkeys_locked}")
    return

def change_max_tokens(tokens_count):
    try:
        settings.max_tokens = int(tokens_count)
    except ValueError:
        settings.max_tokens = int(float(tokens_count))
    print(f"[Web-UI] Max tokens set -> {settings.max_tokens}")
    return

def alarm_button_click(input_time):
    settings.alarm_time = input_time
    print(f"[Web-UI] Alarm time set -> {settings.alarm_time}")
    print(f"\nAlarm time set as {settings.alarm_time}\n")
    return

def model_preset_button_click(input_text):
    settings.model_preset = input_text
    print(f"[Web-UI] Model preset set -> {settings.model_preset}")
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
                """Handle chat messages from the web UI (blank allowed)"""
                # Always pass along; API layer converts blank to *listens attentively*
                main.main_web_ui_chat(message)
                return ""

            def update_chat():
                """Update the chat display"""
                try:
                    # Use platform-separated chat history instead of ooga_history
                    from utils.chat_history import get_chat_history
                    
                    # Get webui platform chat history
                    webui_history = get_chat_history("webui_user", "webui", limit=30)
                    
                    # Convert to the format expected by Gradio chatbot
                    chat_pairs = []
                    current_pair = [None, None]
                    
                    for msg in webui_history:
                        if msg["role"] == "user":
                            # Start a new pair or complete an incomplete one
                            if current_pair[0] is None:
                                current_pair[0] = msg["content"]
                            else:
                                # Save previous incomplete pair and start new one
                                if current_pair[0] is not None:
                                    chat_pairs.append([current_pair[0], current_pair[1] or ""])
                                current_pair = [msg["content"], None]
                        elif msg["role"] == "assistant":
                            # Complete the current pair
                            current_pair[1] = msg["content"]
                            chat_pairs.append([current_pair[0] or "", current_pair[1]])
                            current_pair = [None, None]
                    
                    # Add any incomplete pair
                    if current_pair[0] is not None:
                        chat_pairs.append([current_pair[0], current_pair[1] or ""])
                    
                    # Check if there's a message currently being sent/streamed
                    current_sending = API.api_controller.currently_sending_message
                    current_streaming = API.api_controller.currently_streaming_message
                    
                    if current_sending != "":
                        # Clean the platform marker from the display
                        display_sending = current_sending
                        if "[Platform:" in display_sending:
                            import re
                            display_sending = re.sub(r'\[Platform:[^\]]*\]\s*', '', display_sending).strip()
                        
                        # Add current message being processed
                        chat_pairs.append([display_sending, current_streaming])
                    
                    # Debug logging
                    # print(f"[Web-UI] Returning {len(chat_pairs)} chat pairs from platform history")
                    
                    return chat_pairs
                except Exception as e:
                    print(f"[Web-UI] Error updating chat: {str(e)}")
                    zw_logging.log_error(f"Error updating chat: {str(e)}")
                    # Fallback to empty chat
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
                print("Regenerating last response (Web UI)")
                main.main_web_ui_next()
                return

            def send_blank():
                """Send a blank message through the web UI"""
                print("Sending blank message (Web UI)")
                main.main_web_ui_chat("")
                return

            def undo():
                """Undo last message from web UI"""
                try:
                    # Clear from platform-separated history first
                    from utils.chat_history import chat_histories, save_chat_histories
                    user_key = "webui_webui_user"  # Web UI user key
                    
                    if user_key in chat_histories and len(chat_histories[user_key]) >= 2:
                        # Remove the last user and assistant messages
                        chat_histories[user_key] = chat_histories[user_key][:-2]
                        save_chat_histories()
                    
                    # Also handle old system for backward compatibility
                    API.api_controller.undo_message()
                    
                    # Update the chat display after undo
                    updated_chat = update_chat()
                    status_message = "✅ Last message undone successfully!\n🔄 Conversation reverted to previous state"
                    print(f"[Web-UI] {status_message}")
                    return updated_chat, status_message
                except Exception as e:
                    error_msg = f"❌ Error during undo: {e}"
                    print(f"[Web-UI] {error_msg}")
                    return update_chat(), error_msg

            def clear_history():
                """Clear conversation history from web UI"""
                try:
                    # Clear platform-separated history for web UI user
                    from utils.chat_history import clear_all_histories
                    clear_all_histories()
                    
                    # Also clear old system for backward compatibility
                    fresh_history = [["Hello, I am back!", "Welcome back! *smiles*"]]
                    import json
                    with open("LiveLog.json", 'w') as outfile:
                        json.dump(fresh_history, outfile, indent=4)
                    API.api_controller.ooga_history = fresh_history
                    
                    # Update the chat display after clearing (should be empty now)
                    updated_chat = []  # Empty chat after clearing
                    status_message = "✅ Conversation history cleared successfully!\n🔄 Chat has been reset to fresh start\n🗑️ All conversation data cleared"
                    print(f"[Web-UI] {status_message}")
                    return updated_chat, status_message
                except Exception as e:
                    error_msg = f"❌ Error clearing history: {e}"
                    print(f"[Web-UI] {error_msg}")
                    return update_chat(), error_msg

            def soft_reset():
                """Perform soft reset from web UI"""
                try:
                    # Use the API controller's soft reset which now handles both systems
                    API.api_controller.soft_reset()
                    
                    # Update the chat display after soft reset
                    updated_chat = update_chat()
                    status_message = "✅ Chat soft reset completed successfully!\n🔄 System reset messages added to conversation\n💬 The AI will now respond with refreshed context"
                    print(f"[Web-UI] {status_message}")
                    return updated_chat, status_message
                except Exception as e:
                    error_msg = f"❌ Error during soft reset: {e}"
                    print(f"[Web-UI] {error_msg}")
                    return update_chat(), error_msg

            button_regen = gr.Button(value="Reroll")
            button_blank = gr.Button(value="Send Blank")
            button_undo = gr.Button(value="Undo")
            button_clear_history = gr.Button(value="Clear History")
            button_soft_reset = gr.Button(value="Chat Soft Reset")

            button_regen.click(fn=regenerate)
            button_blank.click(fn=send_blank)
            
        # Add a status display for operations feedback
        with gr.Row():
            status_display = gr.Textbox(label="Status", interactive=False, lines=3, placeholder="Operation status will appear here...")
            
        # Connect buttons with proper outputs to update chat and show status
        button_undo.click(fn=undo, outputs=[chatbot, status_display])
        button_clear_history.click(fn=clear_history, outputs=[chatbot, status_display])
        button_soft_reset.click(fn=soft_reset, outputs=[chatbot, status_display])


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
            
            if not isinstance(autochat_sens, (int, float)):
                autochat_sens = 16 # Default value
            
            hotkeys.input_change_listener_sensitivity_from_ui(int(autochat_sens))
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

            # Log the toggle for UI tracking
            if settings.semi_auto_chat:
                print("Semi-Auto Chat toggled ON (Web UI)")
            else:
                print("Semi-Auto Chat toggled OFF (Web UI)")

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

        with gr.Row():
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
                hotkeys.get_autochat_toggle(),  # Fix: Use correct autochat variable
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


        # Note: Checkbox updates moved to consolidated update_all_views function below
        # This prevents duplicate updates that cause visual glitching






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
        with gr.Row():
            shadowchats_button = gr.Button(value="Toggle Shadow-Chat Speaking")
            shadowchats_button.click(fn=shadowchats_button_click)
            shadowchats_checkbox_view = gr.Checkbox(label="Shadow-Chats Can Be Spoken", interactive=False)

        with gr.Row():
            hotkeys_button = gr.Button(value="Toggle Hotkey Lock")
            hotkeys_button.click(fn=hotkey_button_click)
            hotkeys_checkbox_view = gr.Checkbox(label="Hotkeys Locked", interactive=False)

        with gr.Row():
            rp_sup_button = gr.Button(value="Toggle RP Suppression")
            rp_sup_button.click(fn=supress_rp_button_click)
            rp_sup_checkbox_view = gr.Checkbox(label="Suppress RP", interactive=False)
            
        with gr.Row():
            newline_cut_button = gr.Button(value="Toggle Newline Cut")
            newline_cut_button.click(fn=newline_cut_button_click)
            newline_cut_checkbox_view = gr.Checkbox(label="Cut on Newline", interactive=False)
        
        with gr.Row():
            asterisk_ban_button = gr.Button(value="Toggle Asterisk Ban")
            asterisk_ban_button.click(fn=asterisk_ban_button_click)
            asterisk_ban_checkbox_view = gr.Checkbox(label="Ban Asterisks", interactive=False)

        with gr.Row():
            max_tokens_slider = gr.Slider(minimum=20, maximum=500, value=300, label="Max Tokens", interactive=True)
            max_tokens_slider.change(fn=change_max_tokens, inputs=max_tokens_slider)
        
        with gr.Row():
            alarm_textbox = gr.Textbox(label="Set Alarm (ex: 12:00)", scale=3, interactive=True)
            alarm_button = gr.Button(value="Set Alarm")
            alarm_button.click(fn=alarm_button_click, inputs=alarm_textbox)
        
        with gr.Row():
            model_preset_textbox = gr.Textbox(label="Set Model Preset", scale=3, interactive=True)
            model_preset_button = gr.Button(value="Set Preset")
            model_preset_button.click(fn=model_preset_button_click, inputs=model_preset_textbox)

    #
    # TAGS & TASKS
    #
    with gr.Tab("Tags & Tasks"):
        def get_current_tags():
            return ", ".join(settings.cur_tags) if settings.cur_tags else "None"

        def get_current_task():
            return settings.cur_task_char

        with gr.Row():
            current_tags_view = gr.Textbox(label="Current Tags", interactive=False)
            current_task_view = gr.Textbox(label="Current Task", interactive=False)
        
        demo.load(get_current_tags, outputs=current_tags_view, every=0.5)
        demo.load(get_current_task, outputs=current_task_view, every=0.5)

        with gr.Row():
            tag_input = gr.Textbox(label="Add/Remove Tag")
            add_tag_button = gr.Button("Add Tag")
            remove_tag_button = gr.Button("Remove Tag")

            add_tag_button.click(lambda x: tag_task_controller.add_tag(x), inputs=tag_input)
            remove_tag_button.click(lambda x: tag_task_controller.remove_tag(x), inputs=tag_input)

        with gr.Row():
            task_dropdown = gr.Dropdown(choices=settings.all_task_char_list, label="Select Task", interactive=True)
            set_task_button = gr.Button("Set Task")
            clear_task_button = gr.Button("Clear Task")

            set_task_button.click(lambda x: tag_task_controller.set_task(x), inputs=task_dropdown)
            clear_task_button.click(lambda: tag_task_controller.set_task("None"))



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

    # Universal update function for all dynamic UI elements (consolidated to prevent conflicts)
    def update_all_views():
        return (
            hotkeys.get_speak_input(),           # recording_checkbox_view
            hotkeys.get_autochat_toggle(),       # autochat_checkbox_view - FIXED: use correct variable
            settings.semi_auto_chat,             # semi_auto_chat_checkbox_view
            settings.hangout_mode,               # hangout_mode_checkbox_view
            settings.speak_shadowchats,          # shadowchats_checkbox_view
            settings.hotkeys_locked,             # hotkeys_checkbox_view
            settings.supress_rp,                 # rp_sup_checkbox_view
            settings.newline_cut,                # newline_cut_checkbox_view
            settings.asterisk_ban                # asterisk_ban_checkbox_view
        )

    # A single demo.load call to update all checkboxes simultaneously
    # Update frequency reduced to prevent visual glitching
    demo.load(
        fn=update_all_views,
        every=0.25,  # Reduced frequency to prevent glitching
        outputs=[
            recording_checkbox_view,
            autochat_checkbox_view,
            semi_auto_chat_checkbox_view,
            hangout_mode_checkbox_view,
            shadowchats_checkbox_view,
            hotkeys_checkbox_view,
            rp_sup_checkbox_view,
            newline_cut_checkbox_view,
            asterisk_ban_checkbox_view
        ]
    )

def launch_demo():
    # Launch Gradio with error handling and optional shareability
    try:
        demo.launch(inbrowser=True, share=False)
    except Exception as e:
        if "conflict" in str(e).lower():
            print("Gradio server is already running. Please close the other instance.")
        else:
            print(f"Gradio launch failed: {e}")

