import utils.settings
import os
import json
import utils.cane_lib
import utils.logging

# Loads tags and tasks
def load_tags_tasks():

    with open("Configurables/TaskList.json", 'r') as openfile:
        utils.settings.all_task_char_list = json.load(openfile)

    with open("Configurables/TagList.json", 'r') as openfile:
        utils.settings.all_tag_list = json.load(openfile)

# Saves tags and tasks
def save_tags_tasks():

    with open("Configurables/TaskList.json", 'w') as outfile:
        json.dump(utils.settings.all_task_char_list, outfile, indent=4)

    with open("Configurables/TagList.json", 'w') as outfile:
        json.dump(utils.settings.all_tag_list, outfile, indent=4)


def set_task(input_text):
    if input_text == "None" or input_text == "":
        utils.settings.cur_task_char = "None"
    else:
        utils.settings.cur_task_char = utils.settings.char_name + "-" + input_text

        add_task = True
        for task in utils.settings.all_task_char_list:
            if input_text == task:
                add_task = False

        if add_task:
            utils.settings.all_task_char_list.append(input_text)
            save_tags_tasks()

    utils.logging.update_debug_log("Task set to " + utils.settings.cur_task_char)

def set_tags(new_tags_list):

    # Set 'em
    utils.settings.cur_tags = new_tags_list

    # Also add back in our task-tag as well
    task_tag_clean = get_pure_task()
    change_tag_via_task("Task-" + task_tag_clean)

    # Add to our list of previous tags
    for tag in utils.settings.cur_tags:
        if tag not in utils.settings.all_tag_list:
            utils.settings.all_tag_list.append(tag)

    # Save
    save_tags_tasks()


def apply_tags():
    taglist = utils.settings.cur_tags.copy()

    if utils.settings.is_gaming_loop:
        taglist.append("Auto-Gaming")

    return taglist


def change_tag_via_task(intag):
    if utils.settings.cur_tags is not None:
        for tag in utils.settings.cur_tags:
            if utils.cane_lib.keyword_check(tag, ["Task"]):
                utils.settings.cur_tags.remove(tag)
                break

    if intag not in ["Task-", "Task-None"]:
        utils.settings.cur_tags.append(intag)

# Purifies the task to just the task name, no character
def get_pure_task():
    task_tag_clean = utils.settings.cur_task_char
    task_tag_clean = task_tag_clean.replace(utils.settings.char_name + "-", "")
    return task_tag_clean
