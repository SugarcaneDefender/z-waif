#
# This is the script that will house all the deciding for hangout mode, other than the bits of the actual pipe.
#

# Should they think sometimes? Or reply if sure? Or stay blank if not sure / low time?
#
# Maybe a combination system, where under a certain reply value, they stay blank or wait, at mid / long timing they think,
# and at short they begin talking right away,

#
#
#

import random

import main
import utils.cane_lib
import utils.settings
import json


#
# Hangout control
#

hangout_interrupts_appendables = ""


#
# Hangout decider variables
#

conversation_engagement_level = "Engaged"   # Valid values are "Engaged", "Low", "Listening"
camera_look_level = "Low"            # Valid values are "Active Watching", "High", "Low", "None"
use_interruptable_chat = True       # Should we allow us to interrupt our waifu with our voice?

# Load our defaults
with open("Configurables/Hangout/ReplySettingDefaults.json", 'r') as openfile:
    settings_default = json.load(openfile)
    conversation_engagement_level = settings_default[0][1]
    camera_look_level = settings_default[1][1]

    if settings_default[2][1] == "True":
        use_interruptable_chat = True
    else:
        use_interruptable_chat = False

replies_skipped_stacking = 0    # Make sure we clear on response (in hangout mode)
replies_since_last_cam = 0      # Replies since we have last looked with the camera

# Load in the configurable reply personality
with open("Configurables/Hangout/ReplyPersonality.json", 'r') as openfile:
    configurable_reply_personality = json.load(openfile)

# Load in the configurable thinking words
with open("Configurables/Hangout/ThinkingWords.json", 'r') as openfile:
    configurable_thinking_keywords = json.load(openfile)

# Load in the configurable camera words
with open("Configurables/Hangout/CameraWords.json", 'r') as openfile:
    configurable_camera_keywords = json.load(openfile)


# Give value to how much this reply should be worth, and how we should respond
# Include previous reply info??? Would this help?>?>
# We should make each of these weights configurable!
#
# Three weights!
#
# reply_speed   -   Determines how long waiting is needed
# reply_depth   -   Determines how much thinking is needed
# reply_cam     -   How much camera we need
def reply_decide(input_text):
    global replies_skipped_stacking
    reply_speed = 100
    reply_depth = 100
    reply_cam = 100


    #
    # Value changes;
    #

    # IMPLEMENT LATER: Reply will mutate based on confidence from received speech (and possibly image) being correct

    # IMPLEMENT LATER: Reply will be more valuable if a face is detected in the camera

    # IMPLEMENT LATER: Reply will be more valuable if large camera changes are detected

    # Reply depth will be somewhat less valuable if the text is shorter
    if len(input_text) < 119:
        reply_depth += -10

    # Reply depth will be somewhat less valuable if the text is very long, also
    if len(input_text) > 719:
        reply_depth += -10

    # Reply speed is goldieloxxed for middle length text
    if len(input_text) > 90 and len(input_text) < 599:
        reply_speed += 15

    # Reply speed small boost for low text
    if len(input_text) < 200:
        reply_speed += 10

    # Reply will gain speed per message not replied to previously (unless we are just listening)
    if conversation_engagement_level == "Engaged":
        reply_speed *= 1 + (replies_skipped_stacking * 0.1)

    # Reply will have boosted depth and speed value if waifu detects their name in it.
    if utils.cane_lib.keyword_check(input_text, keywords=[main.char_name]):
        reply_depth += 20
        reply_speed += 70

    # Reply will have massive depth value if told to "think", "remember", "consider". Use keyword list.
    if utils.cane_lib.keyword_check(input_text, keywords=configurable_thinking_keywords):
        reply_depth += 60

    # Reply will have more camera-ness if we haven't used the camera in a while
    reply_cam *= 1 + (replies_since_last_cam * 0.05)

    # Reply with gain / lose camera-ness based on setting
    if camera_look_level is "Active Watching":
        reply_cam *= 1.47
    elif camera_look_level is "High":
        reply_cam *= 1.04
    elif camera_look_level is "Low":
        reply_cam *= 0.67
    elif camera_look_level is "None":
        reply_cam *= 0.0

    # Reply will have more camera-ness if we say "look at this", "see this". Use keyword list.
    if utils.cane_lib.keyword_check(input_text, keywords=configurable_camera_keywords):
        reply_cam += 120

    # Reply will have less value if we are in "Low" engagement mode
    if conversation_engagement_level == "Low":
        reply_depth *= 0.84
        reply_speed *= 0.57
        reply_cam *= 1.05

    # Reply will have less value if we are in "Listening" mode
    if conversation_engagement_level == "Listening":
        reply_depth *= 0.62
        reply_speed *= 0.37
        reply_cam *= 1.10

    # Reply will be adjustable based on configuration
    reply_speed *= configurable_reply_personality[0][1]
    reply_depth *= configurable_reply_personality[0][1]
    reply_cam *= configurable_reply_personality[0][1]

    # Reply will have random, configurable fluctuations in these values, to help with realism and also loosen requirements
    randomness_value = configurable_reply_personality[3][1] * 0.227

    reply_speed *= random.uniform(1 - randomness_value, 1 + randomness_value)
    reply_depth *= random.uniform(1 - randomness_value, 1 + randomness_value)
    reply_cam *= random.uniform(1 - (randomness_value / 2), 1 + (randomness_value / 2))

    # Remove the ability to use the camera if we have no vision
    if not utils.settings.vision_enabled:
        reply_cam = 0

    #
    # List of possible options for the reply;
    #

    # Skip - Simply no reply, no request
    # Think - Do some internal thinking, then decide to reply, not reply, or force reply. Basically defer to her.
    # Think-Self - Do some internal thinking, don't reply or anything just think to self.
    # Reply - Reply right away. Is interruptable,
    # Force-Reply - Force a reply that will not be interruptable, unless called by name.
    # Wait-Reply-(AMMOUNT_OF_TIME) - Wait to reply, and if no activity is detected in this time, run it. Else skip.
    # Look - Just look and store the data of what we see.
    # Look-Reply - Look and directly reply.
    # Look-Think - Do the look action, and then go on to a normal think action.

    # Reply right away if we are really, REALLY hastened
    if reply_speed > 300:
        return "Force-Reply"

    # Use the camera and talk if urgent
    if reply_cam > 149 and reply_speed > 120:
        return "Look-Reply"

    # Look at the camera and think, if it is not urgent, thinky, and camera-y
    if reply_cam > 144 and reply_depth > 130 and reply_speed < 90:
        return "Look-Think"

    if reply_cam > 130 and reply_speed < 120:
        return "Look"

    # Reply right away if we are  hastened
    if reply_speed > 195:
        return "Force-Reply"

    # Think to self if we are low speed and of decent depth
    if reply_speed < 70 and reply_depth > 105:
        return "Think-Self"

    # If thinking is required, then do that instead
    if reply_depth > 130:
        return "Think"

    # Force reply still if not done above
    if reply_speed > 150:
        return "Force-Reply"

    # Reply normally otherwise
    if reply_speed > 99:
        return "Reply"

    # If no depth is there, just wait.
    if reply_depth < 54:
        replies_skipped_stacking += 1
        return "Skip"

    # If low depth and speed, wait a while to reply
    if reply_speed < 70 and reply_depth < 70:
        return "Wait-Reply-9"

    return "Wait-Reply-5"


def clear_reply_skipping():
    global replies_skipped_stacking
    replies_skipped_stacking = 0

def add_to_appendables(input):
    global hangout_interrupts_appendables
    hangout_interrupts_appendables += input

def clear_appendables():
    global hangout_interrupts_appendables
    hangout_interrupts_appendables = ""
