from ast import literal_eval
from dataclasses import dataclass, field
import datetime
import glob
import logging
import os
from pathlib import Path
import shutil
import warnings

import gpt_engineer.steps as steps
from gpt_engineer.ai import AI, fallback_model
from gpt_engineer.db import DB, DBs
import ipylab
from IPython.display import Markdown, display
import ipywidgets as widgets
from jupyter_ai.chat_handlers.generate import schema
import jupyter_core
import openai
import yaml


logging.basicConfig(filename='scalesci.log', level=logging.INFO)
logger = logging.getLogger()

EXCLUDE_DIRECTORIES = ['__pycache__', '.git', '.ipynb_checkpoints']


def read_file_to_string(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        logger.info(f"{file_path} not found.")
        return None


class ScaleSciProjectWidget(widgets.VBox):
    def __init__(self, model=None, session_callback=None, summary_callback=None,
                 improvements_callback=None, implement_callback=None, implement_notebook_callback=None):
        super().__init__()
        if model is None:
            raise Exception("Data model required!")

        self.jupyter_home = jupyter_core.paths.get_home_dir()

        self.width_auto_layout = widgets.Layout(width='auto')
        width_80_layout = widgets.Layout(width='80%')
        width_20_layout = widgets.Layout(width='20%')

        self.data_model = model
        self.app = ipylab.JupyterFrontEnd()
        self.out = widgets.Output()

        self.parent_layout = widgets.Layout(height='40vh', width='auto')
        self.child_layout = widgets.Layout(height='30vh', width='auto')
        self.nav_layout = widgets.Layout(height='20vh', width='auto')

        self.layout = self.parent_layout
        self.tab = widgets.Tab(layout=self.width_auto_layout)

        self.callbacks = {
            'session': session_callback,
            'summary': summary_callback,
            'improvements': improvements_callback,
            'implement': implement_callback,
            'implement_notebook': implement_notebook_callback
            }

        self.data_model.generate_project_name()

        self.project_input = widgets.Text(
            value=self.data_model.project_name,
            description='Project Directory Name',
            layout=width_80_layout)
        self.project_input_autogenerate_button = widgets.Button(
            description='Generate Name', button_style='', layout=width_20_layout)
        self.project_input_autogenerate_button.on_click(self.autogenerate_project_input)
        self.project_input.style.description_width='auto'
        self.project_box = widgets.HBox(children=[self.project_input, self.project_input_autogenerate_button])
        self.starting_code_location_display = widgets.Text(
            value=self.data_model.starting_code_location,
            description='Starting Code Directory',
            disabled=True,
            layout=width_80_layout)
        self.starting_code_location_display.style.description_width='auto'
        self.select_starting_code_button = widgets.Button(
            description='Select Directory',
            icon='folder-open',
            button_style='',
            layout=width_20_layout)
        self.select_starting_code_button.on_click(self.select_code_location)
        self.select_starting_code_directory_nav_box = widgets.VBox(layout=self.nav_layout)
        self.select_starting_code_directory_nav_box.layout.display = 'block'
        self.select_starting_code_box = widgets.HBox(children=[
            self.starting_code_location_display,
            self.select_starting_code_button],
            layout=self.width_auto_layout)
        self.project_workspace_shortcut = widgets.Button(
            description='Show workspace files',
            icon='folder-open',
            button_style='',
            layout=self.width_auto_layout,
            disabled=True)
        self.project_workspace_shortcut.on_click(self.show_workspace)
        self.code_session_button = widgets.ToggleButton(
            description='Start a new coding session',
            icon='check',
            button_style='',
            layout=self.width_auto_layout,
            disabled=True)
        self.code_session_button.observe(self.toggle_session, 'value')
        self.summary_text = widgets.Textarea(
            value=self.data_model.ai_summary, description='', disabled=True, layout=self.child_layout)
        self.summary_text.style.description_width='auto'
        self.summary_request_button = widgets.Button(
            description='Get AI Code Summary', button_style='', layout=self.width_auto_layout)
        self.summary_request_button.on_click(self.get_summary)
        self.suggestions_area = widgets.VBox(children=[], layout=self.child_layout)
        self.suggestions_request_button = widgets.Button(
            description='Get AI Improvement Suggestions', button_style='', layout=self.width_auto_layout)
        self.suggestions_request_button.on_click(self.get_improvement_suggestions)
        self.implement_request_button = widgets.Button(
            description='Generate Code', button_style='', layout=self.width_auto_layout, disabled=True)
        self.implement_request_button.on_click(self.implement_improvements)
        self.implement_notebook_request_button = widgets.Button(
            description='Generate Jupyter Notebook', button_style='', layout=self.width_auto_layout, disabled=True)
        self.implement_notebook_request_button.on_click(self.implement_notebook)
        self.log_area = widgets.Textarea(
            value='', description='', disabled=True, layout=self.parent_layout)
        self.setup_box = widgets.VBox(children = [
            widgets.HBox(
                children=[
                    self.code_session_button, self.project_workspace_shortcut],
                layout=self.width_auto_layout),
            self.project_box,
            self.select_starting_code_box,
            self.select_starting_code_directory_nav_box],
            layout=self.parent_layout)
        self.summary_box = widgets.VBox(
            children=[self.summary_text, self.summary_request_button],
            layout=self.parent_layout)
        self.suggestions_box = widgets.VBox(
            children=[
                widgets.HBox([
                    self.suggestions_request_button,
                    self.implement_request_button,
                    self.implement_notebook_request_button]),
                self.suggestions_area],
            layout=self.parent_layout)
        self.message_box = widgets.VBox(
            children=[self.log_area],
            layout=self.parent_layout
            )
        self.tab.children = [self.setup_box, self.summary_box, self.suggestions_box, self.message_box]
        self.tab.titles = ['AI Code Session', 'AI Code Summary', 'AI Suggestions', 'Message Log']
        self.children = [self.tab]

    def autogenerate_project_input(self, b):
        self.data_model.generate_project_name()
        with self.out:
            if self.project_input.style.text_color == 'red':
                self.project_input.style.text_color = 'black'
            self.project_input.value = self.data_model.project_name

    def select_code_location(self, b):
        if b is not None:
            p = self.data_model.starting_code_location
            if p is None:
                p = os.getcwd()
            self.data_model.starting_code_location = p
            with self.out:
                self.starting_code_location_display.value = str(p)
                #self.select_starting_code_directory_nav_box.layout.visibility = 'visible'
            self.display_code_location_directory()

    def display_code_location_directory(self):
        p = self.starting_code_location_display.value
        names = sorted(os.listdir(p))
        directories = sorted([n for n in names if os.path.isdir(os.path.join(p, n)) and n not in EXCLUDE_DIRECTORIES])
        current_files = sorted([n for n in names if os.path.isfile(os.path.join(p, n))])

        with self.out:
            children = []
            button_layout = self.width_auto_layout
            nav_up = widgets.Button(description='..', button_style='', icon='folder', layout=button_layout)
            nav_up.on_click(self.nav_to)
            children.append(nav_up)
            for dir in directories:
                folder_item_button = widgets.Button(
                    description=dir, button_style='', icon='folder', layout=button_layout)
                folder_item_button.on_click(self.nav_to)
                children.append(folder_item_button)
            for fname in current_files:
                file_item = widgets.HTML("<div>{}</div>".format(fname))
                children.append(file_item)
            self.select_starting_code_directory_nav_box.children = tuple(children)
            self.code_session_button.disabled = False
            #display(self)

    def nav_to(self, b):
        if b is not None:
            p = os.path.join(self.starting_code_location_display.value, b.description)
            self.starting_code_location_display.value = p
            self.data_model.starting_code_location = p
            self.display_code_location_directory()

    def show_workspace(self, b):
        p = os.path.join(os.path.abspath(self.data_model.project_name), 'workspace').split(self.jupyter_home)[1]
        logger.info(p)
        self.app.commands.execute('filebrowser:open-path', {'path': p})

    def toggle_session(self, data=None):
        if data is None:
            raise Exception('No button value')
        with self.out:
            self.out.clear_output(wait=True)
            if data['new']:
                if os.path.exists(os.path.join(os.getcwd(), self.project_input.value)):
                    print("Project directory exists")
                    self.project_input.style.text_color = 'red'
                    self.code_session_button.value = False
                    return
                elif self.project_input.style.text_color == 'red':
                    self.project_input.style.text_color = 'black'
                self.data_model.project_name = self.project_input.value
                self.callbacks['session']()
                self.update_logs()
                self.project_workspace_shortcut.disabled = False
                self.project_input.disabled = True
                self.project_input_autogenerate_button.disabled = True
                self.select_starting_code_button.disabled = True
                self.select_starting_code_directory_nav_box.layout.visibility = 'hidden'
                self.code_session_button.description = 'Stop this coding session'
                self.code_session_button.icon = 'ban'
                self.suggestions_request_button.disabled = False
                self.implement_request_button.disabled = True
                self.implement_notebook_request_button.disabled = True
                display(self)
            else:
                self.project_workspace_shortcut.disabled = True
                self.project_input.disabled = False
                self.project_input_autogenerate_button.disabled = False
                self.select_starting_code_button.disabled = False
                self.code_session_button.description = 'Start a new coding session'
                self.code_session_button.icon = 'check'
                self.select_starting_code_directory_nav_box.layout.visibility = 'visible'
                self.suggestions_request_button.disabled = True
                self.implement_request_button.disabled = True
                self.implement_notebook_request_button.disabled = True
                display(self)

    def get_summary(self, b):
        with self.out:
            self.summary_text.value = "Gathering Summary"
            display(self)
        self.callbacks['summary']()
        self.update_logs()
        with self.out:
            self.summary_text.value = self.data_model.ai_summary

    def get_improvement_suggestions(self, b):
        with self.out:
            self.suggestions_area.children = tuple([widgets.HTML("<div>Gathering Suggestions</div>")])
            display(self)
        self.callbacks['improvements']()
        self.update_logs()
        with self.out:
            children = []
            intro = widgets.HTML("<h2>{}</h2>".format(self.data_model.ai_suggestions['intro']['label']))
            children.append(intro)
            for i in range(1,len(self.data_model.ai_suggestions)):
                k = str(i)
                cb = widgets.Checkbox(
                    value=False, description=self.data_model.ai_suggestions[k]['label'], indent=False)
                cb.style.description_width = 'auto'
                self.data_model.ai_suggestions[k]['checkbox'] = cb

            for i in range(1, len(self.data_model.ai_suggestions)):
                k = str(i)
                children.append(self.data_model.ai_suggestions[k]['checkbox'])
                children.append(
                    widgets.HTML("<p>{}</p>".format(self.data_model.ai_suggestions[k]['description'])))

            self.suggestions_request_button.disabled = True
            self.implement_request_button.disabled = False
            self.suggestions_area.children=tuple(children)
            display(self)

    def implement_improvements(self, b):
        p = os.path.join(os.path.abspath(self.data_model.project_name)).split(self.jupyter_home)[1]
        # the workspace directory is deleted and created again as part of implementation
        self.app.commands.execute('filebrowser:open-path', {'path': p})

        with self.out:
            self.suggestions_request_button.disabled = True
            self.implement_request_button.disabled = True

            for i in range(1, len(self.suggestions_area.children), 2):
                self.suggestions_area.children[i].disabled = True

        self.callbacks['implement']()

        if self.data_model.ai_connection:
            self.show_workspace(b)
            self.update_logs()
            implemented = 0
            with self.out:
                for i in range(1, len(self.suggestions_area.children), 2):
                    if isinstance(self.suggestions_area.children[i], widgets.Checkbox):
                        k = self.suggestions_area.children[i].description.split('.', 1)[0]
                        self.suggestions_area.children[i].disabled = self.data_model.ai_suggestions[k]['implemented']
                        if self.data_model.ai_suggestions[k]['implemented']:
                            implemented += 1
                self.suggestions_request_button.disabled = True
                self.implement_notebook_request_button.disabled = False
                all_implemented = (implemented == len(self.data_model.ai_suggestions) - 1)
                self.implement_request_button.disabled = all_implemented
                display(self)

    def implement_notebook(self, b):
        p = os.path.join(os.path.abspath(self.data_model.project_name)).split(self.jupyter_home)[1]
        # the workspace directory is deleted and created again as part of implementation
        self.app.commands.execute('filebrowser:open-path', {'path': p})

        with self.out:
            self.suggestions_request_button.disabled = True
            self.implement_request_button.disabled = True

            for i in range(1, len(self.suggestions_area.children), 2):
                self.suggestions_area.children[i].disabled = True

        self.callbacks['implement_notebook']()
        self.show_workspace(b)
        self.update_logs()
        implemented = 0
        with self.out:
            for i in range(1, len(self.suggestions_area.children), 2):
                if isinstance(self.suggestions_area.children[i], widgets.Checkbox):
                    k = self.suggestions_area.children[i].description.split('.', 1)[0]
                    self.suggestions_area.children[i].disabled = self.data_model.ai_suggestions[k]['implemented']
                    if self.data_model.ai_suggestions[k]['implemented']:
                        implemented += 1
            self.implement_notebook_request_button.disabled = True
            all_implemented = (implemented == len(self.data_model.ai_suggestions) - 1)
            self.implement_request_button.disabled = all_implemented

    def update_logs(self):
        logger.info("update_logs")

        p = os.path.abspath(os.path.join(self.data_model.project_name, 'memory', 'logs'))
        if not os.path.exists(p):
            return

        text = ''
        log_filenames = [os.path.join(p, n) for n in os.listdir(p)]
        log_filenames = sorted(log_filenames, key=lambda name: os.path.getmtime(os.path.join(p, name)))
        for name in log_filenames:
            filepath = os.path.join(p, name)
            with open(filepath, 'r') as f:
                text += '{}\n{}\n'.format(name, f.read())
        with self.out:
            self.log_area.value = text
            display(self)

@dataclass
class ScaleSciCollabAIModelProperties:
    model_type: str = "gpt-4"
    model_temp: float = 0.1
    model_top_p: float = 0.1


@dataclass
class ScaleSciCollabModel:
    project_name: str
    starting_code_location: str
    ai_properties: ScaleSciCollabAIModelProperties = None
    ai: AI = None
    dbs: DBs = None
    ai_prompts: dict = None
    ai_summary: str = None
    ai_suggestions: dict = None
    ai_message_log: list = None

    def generate_project_name(self):
        self.project_name = "ScaleSci-AI-Collab-{}".format(datetime.datetime.now().isoformat())

    def get_project_path(self):
        return Path(self.project_name)

    def get_db_improvement(self, should_pop=False):
        try:
            nums = literal_eval(self.dbs.input['needed_improvements'])
        except KeyError:
            logger.info("No more improvements found")
            nums = None
        imp = None
        while nums:
            if should_pop:
                num = nums.pop(0)
            else:
                num = nums[0]
            try:
                imp = self.dbs.input['improvement_' + str(num)]
                break
            except KeyError:
                logger.info(f"Skipping improvement {num}")
        if should_pop:
            self.dbs.input['needed_improvements'] = repr(nums)
        return imp

    def store_ai_suggestions(self, content):
        logger.info(content)
        lines = [x for x in content.splitlines() if len(x) > 0]
        self.ai_suggestions = {
            'intro': {
                'label': lines[0],
                'description': '',
                'implemented': False
                }
            }

        for i in range(len(lines)):
            logger.info(lines[i])
            scrubbed_line = lines[i].replace('**', '')
            logger.info(scrubbed_line)

            try:
                num = int(scrubbed_line.split('.', 1)[0])
            except Exception as e:
                self.ai_suggestions['intro'] = {
                    'label': scrubbed_line,
                    'description': '',
                    'implemented': False
                    }
                continue

            try:
                label, description = scrubbed_line.split(':')
                label = label.strip()
                num = label.split('.', 1)[0]
                description = description.strip()
            except Exception as e:
                logger.exception(e)
                raise

            self.ai_suggestions[num] = {
                'label': label,
                'description': description,
                'implemented': False
                }
        logger.info(self.ai_suggestions)

    def store_selected_db_improvements(self):
        selected_improvements = []
        improvement_strings = []
        for i in range(1,len(self.ai_suggestions)):
            k = str(i)
            if self.ai_suggestions[k]['checkbox'].value:
                selected_improvements.append(i)
                improvement_strings.append(
                    f"{self.ai_suggestions[k]['label']}: {self.ai_suggestions[k]['description']}\n")

        if len(selected_improvements) == 0:
            logger.info("Choose at least one suggested improvement")
            return

        for i in range(len(selected_improvements)):
            self.dbs.input[f'improvement_{selected_improvements[i]}'] = improvement_strings[i]
        self.dbs.input['needed_improvements'] = repr(selected_improvements)

class ScaleSciCollabProject:
    def __init__(self, project_name=None, existing_code_location=None):
        os.environ["OPENAI_API_KEY"] = openai.api_key
        self.data_model = ScaleSciCollabModel(
            project_name,
            existing_code_location)
        self.project_widget = ScaleSciProjectWidget(
            self.data_model,
            self.start_new_project,
            self.get_summary,
            self.get_improvement_suggestions,
            self.implement_selected_improvements,
            self.implement_jupyter_improvement)
        display(self.project_widget)

    def start_new_project(self, b=None):
        input_path = self.data_model.get_project_path()
        input_path.mkdir(parents=True, exist_ok=True)

        prompt_file = input_path / "prompt"
        with open('prompts.yml', 'r') as prompts_file:
            self.data_model.ai_prompts = yaml.safe_load(prompts_file)

        with open(prompt_file, "w") as file:
            file.write(self.data_model.ai_prompts["problem_statement"])

        logger.info("The following location will be used for processing:")
        logger.info(input_path.absolute())

        self.data_model.ai_properties = ScaleSciCollabAIModelProperties()

        # model = fallback_model(model)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.data_model.ai = AI(
                model_name=self.data_model.ai_properties.model_type,
                temperature=self.data_model.ai_properties.model_temp,
                top_p=self.data_model.ai_properties.model_top_p,
                )
            self.data_model.ai_connection = True

        memory_path = input_path / "memory"
        workspace_path = input_path / "workspace"
        archive_path = input_path / "archive"

        shutil.copytree(self.data_model.starting_code_location, workspace_path)

        self.data_model.dbs = DBs(
            memory=DB(memory_path),
            logs=DB(memory_path / "logs"),
            input=DB(input_path),
            workspace=DB(workspace_path),
            preprompts=DB(Path(steps.__file__).parent / "preprompts"),
            archive=DB(archive_path),
            )

        self.data_model.dbs.workspace["all_output.txt"] = (
            self.all_code_from_files(self.data_model.starting_code_location))
        self.data_model.dbs.logs['new_session'] = "{}\nproject_name: {}\nstarting_code: {}\nworkspace: {}".format(
            datetime.datetime.now().isoformat(), self.data_model.project_name, self.data_model.starting_code_location,
            workspace_path)


    def all_code_from_files(self, path):
        chat = "These are the files implementing the code\n"
        directory_path = path
        file_pattern = "**/*.*"  # Match all files recursively

        file_paths = glob.glob(os.path.join(directory_path, file_pattern), recursive=True)

        for file_path in file_paths:
            file_name = os.path.relpath(file_path, start=directory_path)
            file_content = read_file_to_string(file_path)
            chat += f"**{file_name}**\n```{file_content}\n```\n\n"
        return chat


    # customization of steps one
    def setup_sys_prompt(self):
        return (
            '{}\nUseful to know:\n{}'.format(
                self.data_model.ai_prompts["persona_prompt"],
                self.data_model.dbs.preprompts["philosophy"]
                )
        )


    def send_and_recieve_messages_with_ai_collaborator(self, prompt, log_key):
        if prompt is None:
            raise Exception('Missing prompt message to AI.')
        if log_key is None:
            log_key = datetime.datetime.now().isoformat()

        code_output = self.data_model.dbs.workspace["all_output.txt"]
        messages_out = [
            self.data_model.ai.fsystem(self.setup_sys_prompt()),
            self.data_model.ai.fuser(f'Instructions: {self.data_model.ai_prompts["problem_statement"]}'),
            self.data_model.ai.fuser(code_output),
            self.data_model.ai.fsystem(prompt),
            ]
        logger.info("Sending messages to AI model: {}".format(messages_out))
        messages_in = self.data_model.ai.next(
            messages_out, prompt, step_name=steps.curr_fn()
            )
        if messages_in:
            self.data_model.dbs.logs[log_key] = AI.serialize_messages(messages_in)
        return messages_in

    def get_summary(self, b=None):
        messages = self.send_and_recieve_messages_with_ai_collaborator(
            self.data_model.ai_prompts['summary_prompt'], 'get_summary')
        self.data_model.ai_summary = messages[-1].content
        return messages

    def get_improvement_suggestions(self, b=None):
        messages = self.send_and_recieve_messages_with_ai_collaborator(
            'suggestions_prompt', 'get_improvement_suggestions')
        self.data_model.store_ai_suggestions(messages[-1].content)

    def implement_selected_improvements(self):
        selected_improvements = []
        for i in range(1,len(self.data_model.ai_suggestions)):
            k = str(i)
            if self.data_model.ai_suggestions[k]['checkbox'].value:
                selected_improvements.append(i)

        if len(selected_improvements) == 0:
            logger.info("Choose at least one suggested improvement")
            return

        self.data_model.store_selected_db_improvements()

        logger.info("Processing improvements:")
        for i in range(len(selected_improvements)):
            msgs = self.implement_improvement()
            if msgs is None:
                break
        logger.info("Final result is located in: " + str(self.data_model.dbs.workspace.path))

    def implement_improvement(self):
        code_output = self.data_model.dbs.workspace["all_output.txt"]
        improvement = self.data_model.get_db_improvement(should_pop=True)
        if improvement is None:
            return None
        logger.info("Preparing messages for our AI Collaborator")
        messages = [
            self.data_model.ai.fsystem(self.setup_sys_prompt()),
            self.data_model.ai.fuser(f"Instructions: {self.data_model.ai_prompts['problem_statement']}"),
            self.data_model.ai.fuser(code_output),
            self.data_model.ai.fsystem(self.data_model.dbs.preprompts["generate"]),
            ]
        logger.info("Saving an archive of our current state")
        steps.archive(self.data_model.dbs)
        logger.info("Sending messages to our AI Collaborator and waiting for a response...")
        messages = self.data_model.ai.next(
            messages, self.data_model.ai_prompts['improvement_prompt'].format(
                improvement=improvement), step_name=steps.curr_fn()
            )
        if messages:
            logger.info("Our AI Collaborator has responded with updates")
            self.data_model.dbs.logs['implement_improvement'] = AI.serialize_messages(messages)
            self.data_model.ai_suggestions[improvement.split('.', 1)[0]]['implemented'] = True
            logger.info("Saving updates to our workspace area")
            steps.to_files(messages[-1].content.strip(), self.data_model.dbs.workspace)
            self.data_model.ai_connection = True
        else:
            logger.info("We did not receive a response from our AI Collaborator")
            self.data_model.ai_connection = False
        return messages

    def implement_jupyter_improvement(self):
        code_output = self.data_model.dbs.workspace["all_output.txt"]
        messages = [
            self.data_model.ai.fsystem(self.setup_sys_prompt()),
            self.data_model.ai.fuser(f"Instructions: {self.data_model.ai_prompts['problem_statement']}"),
            self.data_model.ai.fuser(code_output),
            self.data_model.ai.fsystem(self.data_model.dbs.preprompts["generate"]),
            ]
        steps.archive(self.data_model.dbs)
        messages = self.data_model.ai.next(
            messages,
            self.data_model.ai_prompts['improvement_prompt'].format(
                improvement=self.data_model.ai_prompts['jupyter_improvement'].format(schema=schema)),
            step_name=steps.curr_fn()
            )
        if messages:
            self.data_model.dbs.logs['implement_jupyter_improvement'] = AI.serialize_messages(messages)
        steps.to_files(messages[-1].content.strip(), self.data_model.dbs.workspace)
        return messages
