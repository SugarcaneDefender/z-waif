import yaml
import os

task_profiles = []

def load_task_profiles():
    global task_profiles

    for file in os.listdir("Configurables/TaskProfiles"):
        if file.endswith(".yaml"):
            with open("Configurables/TaskProfiles/" + file, 'r') as infile:
                task_loder = yaml.load(infile, Loader=yaml.FullLoader)
                task_profiles.append([task_loder["Task"], task_loder["Description"]])    # Append it as the name, and then the task description
