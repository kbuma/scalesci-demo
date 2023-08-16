import json
import shutil
import glob
import os
from pathlib import Path
from ast import literal_eval
from re import sub

import gpt_engineer.steps as steps
from gpt_engineer.ai import AI, fallback_model
from gpt_engineer.db import DB, DBs
from jupyter_ai.chat_handlers.generate import schema

problem_statement = '''I have this scientific computation that I wrote. 
I would like to optimize it such that it runs faster (utilizing parallel computation) and is more interactive.
I will be running this on an HPC system that has support for dask and slurm.
'''
persona_prompt = '''You are an expert in optimizing scientific computations on HPC systems. 
You will help this scientist take their existing code and turn it into a modularized software application
utilizing dask with improved performance (faster, more interactive). Focus on: (1) using Dask to parallelize the computation 
and take advantage of multiple cores or nodes in the HPC system; (2) optimizing the calculations by using Dask arrays instead 
of NumPy arrays for better performance; (3) using Dask's lazy evaluation to delay the computation until necessary, reducing memory usage;
(4) using xarray's built-in Dask integration
'''
summary_prompt = '''Provide a short summary of the computation (DO NOT list out all the steps) based on the provided code.
'''
suggestions_prompt = '''Provide a short list of improvement suggestions for the provided code.
'''
improvement_prompt = '''Rewrite the provided code to incorporate the following improvement: 
{improvement}

Please now remember the steps:

Think step by step and reason yourself to the right decisions to make sure we get it right.
First lay out the names of the core classes, functions, methods that will be necessary, As well as a quick comment on their purpose.

Then you will output the content of each file including ALL code.
Each file must strictly follow a markdown code block format, where the following tokens must be replaced such that
FILENAME is the lowercase file name including the file extension,
LANG is the markup code block language for the code's language, and CODE is the code:

FILENAME
```LANG
CODE
```

Please note that the code should be fully functional. No placeholders.

You will start with the "entrypoint" file, then go to the ones that are imported by that file, and so on.
Follow a language and framework appropriate best practice file naming convention.
Make sure that files contain all imports, types etc. The code should be fully functional. Make sure that code in different files are compatible with each other.
Before you finish, double check that all parts of the architecture is present in the files.
'''
jupyter_improvement = '''I will want to interact with the computation via a Jupyter notebook.
Convert the code to have the user launch the code from and interact with a Jupyter notebook for a more interactive and visual experience.
The Jupyter notebook will follow an outline as JSON data that will validate against this JSON schema:
{schema}
Don't include an introduction or conclusion section in the outline, focus only on sections that will need code.
'''

def set_up(project_name, existing_code_location):
    input_path = Path(project_name)
    input_path.mkdir(parents=True, exist_ok=True)

    prompt_file = input_path / "prompt"

    with open(prompt_file, "w") as file:
        file.write(problem_statement)

    input_path = input_path.absolute()
    print("The following location will be used for processing:")
    print(input_path)
    
    model = "gpt-4"
    temperature = 0.1
    top_p = 0.1
    #model = fallback_model(model)
    ai = AI(
        model_name=model,
        temperature=temperature,
        top_p=top_p,
    )

    memory_path = input_path / "memory"
    workspace_path = input_path / "workspace"
    archive_path = input_path / "archive"
    
    shutil.copytree(existing_code_location, workspace_path)
    
    dbs = DBs(
        memory=DB(memory_path),
        logs=DB(memory_path / "logs"),
        input=DB(input_path),
        workspace=DB(workspace_path),
        preprompts=DB(Path(steps.__file__).parent / "preprompts"),
        archive=DB(archive_path),
    )

    dbs.workspace["all_output.txt"] = all_code_from_files(existing_code_location)

    return ai, dbs

def all_code_from_files(path):
    chat = "These are the files implementing the code\n"
    directory_path = path
    file_pattern = "**/*.*"  # Match all files recursively

    file_paths = glob.glob(os.path.join(directory_path, file_pattern), recursive=True)

    for file_path in file_paths:
        file_name = os.path.relpath(file_path, start=directory_path)
        file_content = read_file_to_string(file_path)
        chat += "**" + file_name + "**\n" + "```" + file_content + "\n```\n\n"
    return chat

def read_file_to_string(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"{file_path} not found.")
        return None

# customization of steps one
def setup_sys_prompt(dbs: DBs) -> str:
    return (
        persona_prompt + "\nUseful to know:\n" + dbs.preprompts["philosophy"]
    )

def get_summary(ai, dbs):
    code_output = dbs.workspace["all_output.txt"]
    messages = [
        ai.fsystem(setup_sys_prompt(dbs)),
        ai.fuser(f"Instructions: {problem_statement}"),
        ai.fuser(code_output),
        ai.fsystem(summary_prompt),
    ]
    messages = ai.next(
        messages, summary_prompt, step_name=steps.curr_fn()
    )
    return messages

def get_improvement_suggestions(ai, dbs):
    code_output = dbs.workspace["all_output.txt"]
    messages = [
        ai.fsystem(setup_sys_prompt(dbs)),
        ai.fuser(f"Instructions: {problem_statement}"),
        ai.fuser(code_output),
        ai.fsystem(suggestions_prompt),
    ]
    messages = ai.next(
        messages, suggestions_prompt, step_name=steps.curr_fn()
    )
    store_improvements(messages[-1].content.strip(), dbs.input)
    return messages

def implement_improvement(ai, dbs):
    code_output = dbs.workspace["all_output.txt"]
    improvement = pop_improvement(dbs.input)
    if improvement is None:
        return None
    messages = [
        ai.fsystem(setup_sys_prompt(dbs)),
        ai.fuser(f"Instructions: {problem_statement}"),
        ai.fuser(code_output),
        ai.fsystem(dbs.preprompts["generate"]),
    ]
    steps.archive(dbs)
    messages = ai.next(
        messages, improvement_prompt.format(improvement=improvement), step_name=steps.curr_fn()
    )
    steps.to_files(messages[-1].content.strip(), dbs.workspace)
    return messages

def implement_jupyter_improvement(ai, dbs):
    code_output = dbs.workspace["all_output.txt"]
    messages = [
        ai.fsystem(setup_sys_prompt(dbs)),
        ai.fuser(f"Instructions: {problem_statement}"),
        ai.fuser(code_output),
        ai.fsystem(dbs.preprompts["generate"]),
    ]
    steps.archive(dbs)
    messages = ai.next(
        messages, 
        improvement_prompt.format(improvement=jupyter_improvement.format(schema=schema)), 
        step_name=steps.curr_fn()
    )
    steps.to_files(messages[-1].content.strip(), dbs.workspace)
    return messages

def peek_improvement(input):
    return get_improvement(input, False)

def pop_improvement(input):
    return get_improvement(input, True)

def improvement_list(input):
    try:
        return literal_eval(input['needed_improvements'])
    except KeyError:
        print("No more improvements found")
        return None

def get_improvement(input, pop):
    nums = improvement_list(input)
    imp = None
    while nums:
        if pop:
            num = nums.pop(0)
        else:
            num = nums[0]
        try:
            imp = input['improvement_' + str(num)]
            break
        except KeyError:
            print(f"Skipping improvement {num}")
    input['needed_improvements'] = repr(nums)
    return imp


def store_improvements(content, input):
    nums = []
    for num, imp in parse_numbered_list(content).items():
        input['improvement_' + str(num)] = imp
        nums.append(num)
    input['needed_improvements'] = repr(nums)

def parse_numbered_list(string_list):
    lines = string_list.strip().split('\n')
    result = {}
    
    for line in lines:
        parts = line.split(' ', 1)
        if len(parts) == 2:
            key, value = parts
            key = sub(r'\D', '', key)
            try:
                key = int(key)
                result[key] = value.strip()
            except ValueError:
                pass
                
    return result