import json
import os

converted_log_count = 0

#
# For Importing SillyTaven chats. I used it for Character.AI, as an extension converted it to that format
#

def run_conversion():

    # Gather all of our data
    for file in os.listdir("Logs/Drop_Converts_Here"):
        if file.endswith(".jsonl"):
            with open("Logs/Drop_Converts_Here/" + file, encoding="utf8") as f:
                data = [json.loads(line) for line in f]

                # Convert it to our format

                i = 1   # First line is always a header bit, ignore
                temp_log = [["[System L] Start of New Log!", ""]]
                last_sender = "None"
                temp_pair = ["", ""]

                while i < len(data):

                    # Breaker for who is sending, me first
                    if data[i]["name"] == "You":

                        # If double-dipping, send out the previous one
                        if last_sender == "You":
                            temp_log += [temp_pair]
                            temp_pair = ["", ""]

                        temp_pair[0] = data[i]["mes"]
                        last_sender = data[i]["name"]

                    # She will always send out
                    else:

                        temp_pair[1] = data[i]["mes"]
                        last_sender = data[i]["name"]

                        temp_log += [temp_pair]
                        temp_pair = ["", ""]

                    i += 1


                # Save the file
                global converted_log_count
                converted_log_count += 1

                with open("Logs/ChatLog-Converted-" + converted_log_count.__str__() + ".json", 'w') as outfile:
                    json.dump(temp_log, outfile, indent=4)

                #
                # Note: The "Drop_Converts_Here" folder will not automatically remove converted files! Buyer beware!
                # (This is because we may want to take a look at them/paste elsewhere, user must clean out after)
                #
