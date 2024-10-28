#
#
# GRRRR! GRRRRRRR! I HATE WORKFLOWS!

# This is our state manager. It can have a list of many options to control IO. Options are as follows;
# "Idle" = Nothing is happening
# "TTS Process" = TTS Processing Message
# "RAG Process" = RAG Running and Processing
# "Thinking" = LLM Work
# "Speaking" = TTS Output
#
# Pipe type respresents a variety of actions, such as "Talk", "Picture", "Discord Message"
#
# Comes with [current pipeflow spot, pipe ID, pipe type]
cur_states = [["Idle", 0, "None"], ["Idle", 0, "Discord"]]
