import json
import subprocess
import os

from typing import Callable, ClassVar, Generic, Iterable, TypeVar, cast

from textual.types import OptionDoesNotExist
from textual._on import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid, HorizontalGroup, VerticalGroup
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    TabbedContent,
    TabPane,
    OptionList,
    Input,
    Label,
    SelectionList,
)
from textual.widgets.option_list import Option

VER = "2.0.0"
TITLE= r"""
    ___         __           ____               _           __     ____  _                __                  
   /   | __  __/ /_____     / __ \_________    (_)__  _____/ /_   / __ \(_)_______  _____/ /_____  _______  __
  / /| |/ / / / __/ __ \   / /_/ / ___/ __ \  / / _ \/ ___/ __/  / / / / / ___/ _ \/ ___/ __/ __ \/ ___/ / / /
 / ___ / /_/ / /_/ /_/ /  / ____/ /  / /_/ / / /  __/ /__/ /_   / /_/ / / /  /  __/ /__/ /_/ /_/ / /  / /_/ / 
/_/  |_\__,_/\__/\____/  /_/   /_/   \____/_/ /\___/\___/\__/  /_____/_/_/   \___/\___/\__/\____/_/   \__, /  
                                         /___/                                                       /____/   
"""

class _SelectionList(SelectionList):
    # adding custom bindings to SelectionList
    BINDINGS = [
        Binding("j","cursor_down","move down", show=True),
        Binding("k","cursor_up","move up", show=True),
    ]

class _OptionList(OptionList):
    # adding custom bindings to OptionList
    BINDINGS = [
        Binding("j","cursor_down","move down", show=True),
        Binding("k","cursor_up","move up", show=True),
        Binding("r","remove_item","remove item",show=True),
    ]

    def action_remove_item(self):
        highlight = self.highlighted_option 
        if highlight is not None:
            highlightID= highlight.id
            self.remove_option(option_id=highlightID)

class AutoProjDirUI(App):
    CSS_PATH = "main.tcss"

    BINDINGS = [
            Binding( "ctrl+c", "quit_app", "Quit App", show= True),
            #Binding( "ctrl+o", "reload_app", "reloads the app",),
    ]

    def action_quit_app(self):
        self.exit()

    def action_reload_app(self):
        # leaving this for now. It would be nice if you could push a button to reload the settings
        # right now its telling me that I have duplicate IDs, so I would have to clear 
        self.notify("refresh!")
        self.read_option()   
        self.initialize_form()
        self.recompose()
        #self.refresh(recompose=True)

    def read_option(self):
        # Read settings file and set the appropriate internal variables

        self.dir_list= [] # this is what we read from the settings.json file
        self.dirSetting_list = [] # this is what we eventually write to the settings.json file
        with open('settings.json',"r") as json_data:
            d = json.load(json_data)
            json_data.close()
        self.theme_def = d["theme"]
        temp_dirs =d["dirs"] 
        for i in range(0,len(d["dirs"])):
            lbl =temp_dirs[i][0] 
            val =temp_dirs[i][0] 
            # if running linux, we will have to deal with the whitespace
            # we may want to do a bit more processing on the name 
            # (removing trailing whitespaces, allowing preferences for space replacement, etc.) 
            # For the time being, if people want their directories to be nice, they have to format it themselves.

            if temp_dirs[i][1] == '1':
                enbl = True
            else:
                enbl = False
            temp_tup = (lbl,val, enbl) 
            self.dir_list.append(temp_tup) # this is a list of tuples that will be used to build the directory list in "compose" method

        self.base_path = d["base_path"]
        self.note_path = d["note_path"]
        self.read_def = d["readme_def"]
        self.git_def = d["git_def"]
        self.mkNote_def = d["mkNote_def"]
        self.venv_def = d["venv_def"]
        self.cargo_def = d["cargo_def"]
        #self.linkDef = d["link_def"]

    def write_option(self):
        option_list=self.query_one("#dirSetting_list")
        opt_num = option_list.option_count
        self.dirSetting_list = []
        for j in range(0,opt_num):
            optStr = option_list.get_option_at_index(j).prompt
            self.dirSetting_list.append(optStr)
        num_dirs = len(self.dirSetting_list)

        base_path = self.query_one("#projSetting_input").value
        base_path = base_path.replace("\\", "\\\\")
        note_path = self.query_one("#noteSetting_input").value
        note_path = note_path.replace("\\", "\\\\")

        read_setting = "1" if self.query_one("#readmeSetting_check").value else "0"
        git_setting = "1" if self.query_one("#gitSetting_check").value else "0"
        mkNote_setting = "1" if self.query_one("#mknoteSetting_check").value else "0"
        venv_setting = "1" if self.query_one("#venvSetting_check").value else "0"
        cargo_setting = "1" if self.query_one("#cargoSetting_check").value else "0"

        theme_setting = self.theme

        # open the settings file
        f = open("settings.json", "w")

        # begin constructing the contents
        settings_content= "{\n\t\"dirs\": [\n"

        # write the directories
        for k in range(0,num_dirs):
            settings_content+= "\t\t["  + f"\"{self.dirSetting_list[k]}\""  + ",\"0\"]" # this adds the directory to the json file. right now, files are all default to off
            if k < (num_dirs-1):
                settings_content +=  ",\n"
        settings_content+= "\n\t],\n"
        
        # start writing options
        settings_content += "\t\"base_path\":" +f"\"{base_path}\"" + ",\n"
        settings_content += "\t\"note_path\":" +f"\"{note_path}\"" + ",\n"
        settings_content += "\t\"readme_def\":" +f"\"{read_setting}\"" + ",\n"
        settings_content += "\t\"git_def\":" +f"\"{git_setting}\"" + ",\n"
        settings_content += "\t\"mkNote_def\":" +f"\"{mkNote_setting}\"" + ",\n"
        settings_content += "\t\"venv_def\":" +f"\"{venv_setting}\"" + ",\n"
        settings_content += "\t\"cargo_def\":" +f"\"{cargo_setting}\"" + ",\n"

       # write theme
        settings_content += "\t\"theme\":" +f"\"{theme_setting}\"" + "\n"

        # last line
        settings_content +="\n}"
        f.write(settings_content)
        self.notify("Wrote settings",severity="information")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        with TabbedContent(initial="main_tab"):
            with TabPane("Main", id="main_tab"):
                yield Container(
                    Label(TITLE,id="title_label"),
                    id="title_container"
                )

                yield Container(
                    Input(placeholder="Project Name", id="projname_input"),
                    id= "name_container"
                )

                yield Container(
                    _SelectionList(id="dir_list"),
                    id="dir_container"
                )

                yield HorizontalGroup(
                    VerticalGroup(
                        Checkbox("Create readme?",id="readme_check"),
                        Checkbox("Make note?",id="mknote_check")
                    ),
                    VerticalGroup(
                        #yield Checkbox("Link to note?", id="mklink_check")
                        Checkbox("Init git?", id="git_check"),
                        Checkbox("Init virtual environment?", id="venv_check"),
                        Checkbox("Init cargo?", id="cargo_check")
                    ),
                    id="option_container"
                )

                yield HorizontalGroup(
                    Button("Create Project",variant="primary",id="create",classes="main_buttons"),
                    Button("Close",id="close",classes="main_buttons"),
                    id="buttons1"
                )

            with TabPane("Settings", id="settings_tab"):
                yield Container(
                    _OptionList(id="dirSetting_list"),
                    Input("add directory",id="dirSetting_input"),
                    classes="setting_container"
                )
                yield Container(
                    VerticalGroup(
                        HorizontalGroup( 
                            VerticalGroup(
                                Checkbox("readme default",id="readmeSetting_check"),
                                Checkbox("make note default",id="mknoteSetting_check"),
                            ),
                            VerticalGroup(
                                #yield Checkbox("note link default", id="mklinkSetting_check")
                                Checkbox("git default", id="gitSetting_check"),
                                Checkbox("venv default", id="venvSetting_check"),
                                Checkbox("cargo default", id="cargoSetting_check"),
                            )
                        ),
                        Input("base path",id="projSetting_input"),
                        Input("notes path",id="noteSetting_input"),
                    ),
                    classes="setting_container"
                )
                yield Button("Save Settings",variant="primary",id="save",classes="saveSetting_button")

    def on_mount(self) -> None:
        self.title= "Auto Project Directory"
        self.sub_title = f"v{VER}"
        self.theme = self.theme_def
        self.query_one("#name_container").border_title = "Project Name"
        self.query_one("#dir_container").border_title = "Subdirectories"
        self.query_one("#option_container").border_title = "Options"

        for i in range(0,len(self.dir_list)):
            self.query_one("#dir_list").add_option(self.dir_list[i]) 
            dirListID = self.dir_list[i][0].replace(" ","_")
            self.query_one("#dirSetting_list").add_option(Option(self.dir_list[i][0],dirListID))

        if self.read_def == "1":
            self.query_one("#readme_check").value = True
            self.query_one("#readmeSetting_check").value = True
        if self.mkNote_def == "1":
            self.query_one("#mknote_check").value = True
            self.query_one("#mknoteSetting_check").value = True
        if self.git_def == "1":
            self.query_one("#git_check").value = True
            self.query_one("#gitSetting_check").value = True
        #if self.linkDef == "1":
        #    self.query_one("#mkLink_check").value = True
        if self.venv_def == "1":
            self.query_one("#venv_check").value = True
            self.query_one("#venvSetting_check").value = True
        if self.cargo_def == "1":
            self.query_one("#cargo_check").value = True
            self.query_one("#cargoSetting_check").value = True
        self.query_one("#projSetting_input").value = self.base_path
        self.query_one("#noteSetting_input").value = self.note_path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "create":
            self.sanitize_name()
            self.process_request()
        elif button_id == "close":
            self.exit()
        elif button_id == "save":
            self.write_option()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        input_id = event.input.id
        if input_id == "dirSetting_input":
            input_dir_name =  self.query_one("#dirSetting_input").value
            input_dir_id = input_dir_name.replace(" ","_")
            option_list=self.query_one("#dirSetting_list")
            try:
                option_list.get_option(input_dir_id) 
                self.notify("Directory name already exists",severity="warning")
            except OptionDoesNotExist:
                option_list.add_option(Option(f"{input_dir_name}",f"{input_dir_id}"))
                self.query_one("#dirSetting_input").clear()

    def initialize_form(self):
        self.title= "Auto Project Directory"
        self.sub_title = f"v{VER}"

        self.query_one("#name_container").border_title = "Project Name"
        self.query_one("#dir_container").border_title = "Subdirectories"
        self.query_one("#option_container").border_title = "Options"

        self.query_one("#dirSetting_list").clear_options()
        for i in range(0,len(self.dir_list)):
            self.query_one("#dir_list").add_option(self.dir_list[i]) 
            dir_list_id = self.dir_list[i][0].replace(" ","_")
            self.query_one("#dirSetting_list").add_option(Option(self.dir_list[i][0],dir_list_id))

        if self.read_def == "1":
            self.query_one("#readme_check").value = True
            self.query_one("#readmeSetting_check").value = True
        if self.mkNote_def == "1":
            self.query_one("#mknote_check").value = True
            self.query_one("#mknoteSetting_check").value = True
        if self.git_def == "1":
            self.query_one("#git_check").value = True
            self.query_one("#gitSetting_check").value = True
        #if self.linkDef == "1":
        #    self.query_one("#mkLink_check").value = True
        if self.venv_def == "1":
            self.query_one("#venv_check").value = True
            self.query_one("#venvSetting_check").value = True
        if self.cargo_def == "1":
            self.query_one("#cargo_check").value = True
            self.query_one("#cargoSetting_check").value = True
        self.query_one("#projSetting_input").value = self.base_path
        self.query_one("#noteSetting_input").value = self.note_path

    def sanitize_name(self):
        # todo add more "sanitization" removing illegal characters, substituting characters, etc
        t_proj_name = self.query_one("#projname_input").value
        if t_proj_name:
            self.proj_name = t_proj_name
            self.proceed = True 
        else:
            self.proceed = False

    def process_request(self):
        # get all the requests from the form
        di = self.query_one("#dir_list").selected

        readme = self.query_one("#readme_check").value
        makenote = self.query_one("#mknote_check").value
        initgit = self.query_one("#git_check").value
        initvenv = self.query_one("#venv_check").value
        initcargo = self.query_one("#cargo_check").value
        actions = False

        if (self.proceed) :
            self.PROJ_PATH = self.base_path + self.proj_name + "\\"
            try:
                # make project path
                os.makedirs(self.PROJ_PATH)

                # make subdirectories
                for i in range(0,len(di)):
                    path = self.PROJ_PATH + di[i]
                    os.makedirs(path)

                # make readme
                if readme:
                    try:
                        open(self.PROJ_PATH + "readme.md","x")
                        actions = True
                    except:
                        self.notify("Error creating README",severity="warning")

                # make a note
                if makenote:
                    try:
                        self.make_note()
                        actions = True
                    except:
                        self.notify("Error creating note",severity="warning")

                # initialize git                
                if initgit:
                    try:
                        self.init_git()
                        actions = True
                    except:
                        self.notify("Error initiating git",severity="warning")

                # initialize venv
                if initvenv:
                    try:
                        self.init_venv()
                        actions = True
                    except:
                        self.notify("Error initiating venv",severity="warning")

                if initcargo:
                    try:
                        self.init_cargo()
                        actions = True
                    except:
                        self.notify("Error initiating cargo",severity="warning")

                # wrapping up
                if actions: 
                    self.notify("Directories created and actions performed!")
                else:
                    self.notify("Directories created!")

            except FileExistsError:
                self.notify("Directory already exists. Aborting operation",severity="error")

        else:
            self.notify("Error in project name",severity="error")

    def make_note(self):
        note_path = self.note_path + self.proj_name + ".md"
        f = open(note_path, "a")
        folder_link = "["+self.proj_name+"](file://"+self.PROJ_PATH+")"
        note_content=f"links:\n{folder_link}\n\n---" 
        f.write(note_content)

    def init_git(self):
        subprocess.call(['git','init'],stdout=subprocess.DEVNULL,cwd= self.PROJ_PATH)

    def init_cargo(self):
        subprocess.call(['cargo','init'],stdout=subprocess.DEVNULL,cwd= self.PROJ_PATH)

    def init_venv(self):
        subprocess.call(['python','-m','venv','.venv'],stdout=subprocess.DEVNULL,cwd= self.PROJ_PATH)

    def make_link(self):
        # work in progress. Ideally if the user clicks the 'make link" checkbox they do not necessarily need to press the make note button
        # the system would be able to automatically find which note you are talking about and link to it
        # trying to achieve that with fzf, but its not working right now
        # once we know where the link is, then we can make a desktop file or shortcut as appropriate

        link_path = self.PROJ_PATH + "note.desktop"
        res = subprocess.call(['fzf',f'--query={self.proj_name}','--select-1'], cwd=self.note_path)
        print(res)

if __name__ == "__main__":
    app = AutoProjDirUI()
    app.read_option() 
    app.run()