from utils import settings
import os
import json
from utils import cane_lib
from utils import zw_logging
import yaml

# Loads tags and tasks
def load_tags_tasks():

    with open("Configurables/TaskList.json", 'r') as openfile:
        settings.all_task_char_list = json.load(openfile)

    with open("Configurables/TagList.json", 'r') as openfile:
        settings.all_tag_list = json.load(openfile)

# Saves tags and tasks
def save_tags_tasks():

    with open("Configurables/TaskList.json", 'w') as outfile:
        json.dump(settings.all_task_char_list, outfile, indent=4)

    with open("Configurables/TagList.json", 'w') as outfile:
        json.dump(settings.all_tag_list, outfile, indent=4)


def set_task(input_text):
    if input_text == "None" or input_text == "":
        settings.cur_task_char = "None"
    else:
        settings.cur_task_char = settings.char_name + "-" + input_text

        add_task = True
        for task in settings.all_task_char_list:
            if input_text == task:
                add_task = False

        if add_task:
            settings.all_task_char_list.append(input_text)
            save_tags_tasks()

    zw_logging.update_debug_log("Task set to " + settings.cur_task_char)

def set_tags(new_tags_list):

    # Set 'em
    settings.cur_tags = new_tags_list

    # Also add back in our task-tag as well
    task_tag_clean = get_pure_task()
    change_tag_via_task("Task-" + task_tag_clean)

    # Add to our list of previous tags
    for tag in settings.cur_tags:
        if tag not in settings.all_tag_list:
            settings.all_tag_list.append(tag)

    # Save
    save_tags_tasks()


def apply_tags():
    taglist = settings.cur_tags.copy()

    if settings.is_gaming_loop:
        taglist.append("Auto-Gaming")

    return taglist


def change_tag_via_task(intag):
    if settings.cur_tags is not None:
        for tag in settings.cur_tags:
            if cane_lib.keyword_check(tag, ["Task"]):
                settings.cur_tags.remove(tag)
                break

    if intag not in ["Task-", "Task-None"]:
        settings.cur_tags.append(intag)

# Purifies the task to just the task name, no character
def get_pure_task():
    task_tag_clean = settings.cur_task_char
    task_tag_clean = task_tag_clean.replace(settings.char_name + "-", "")
    return task_tag_clean

# Pulls the current task from the configurables.
def get_cur_task_description():

    # Search for it in the configurables
    with open("Configurables/TaskProfiles/" + get_pure_task() + ".yaml", 'r') as openfile:
        task_loder = yaml.load(openfile, Loader=yaml.FullLoader)
        return task_loder["Description"]

def get_current_tags():
    """Get the current list of tags"""
    return settings.cur_tags

def get_all_tags():
    """Get all available tags"""
    return settings.all_tag_list


