from challonge import ChallongeTournament
import csv
import random
from copy import deepcopy
import json
import customtkinter
import os
from CTkMessagebox import CTkMessagebox
import sys
import math
from itertools import islice

class BracketGenerator:
    def __init__(self, participant_list):
        sys.setrecursionlimit(1_000_000)
        self.num_participants = len(participant_list)
        self.participants = self.parse_participant_list(participant_list)

    def run(self,run_number = 1):
        shuffled = self.participants
        random.shuffle(shuffled)

        while run_number <= 1_000_000:
            if run_number == 1:
                first_run = True
            else:
                first_run = False
            # I would prefer to not have deepcopy here, but it will consume the shuffled participants otherwise.
            if self.trainer_dittos(deepcopy(shuffled)) or self.character_dittos(deepcopy(shuffled)):
                self.participants = shuffled
                self.run(run_number + 1)
                if first_run:
                    break
                else:
                    return
            else:
                return

        # Turn the participants back into a list of "Trainer - Character"
        participant_list = self.turn_participants_back_to_list(shuffled)
        # Generate the bracket placements
        bracket = self.generate_tournament(self.num_participants)
        # Variable used to store the participant's name attached to their seed number
        participants_seeded = {}
        for x in range(0, self.num_participants):
            participants_seeded[bracket[x]] = participant_list[x]
        # Sort the seeded participants by seed
        sort = dict(sorted(participants_seeded.items()))
        # Variable to store the list of participants in order by seed
        final_participants = []
        for x in range(1, self.num_participants +1):
            final_participants.append(sort[x])

        # Return the sorted participants
        return final_participants

    def parse_participant_list(self, participant_list):
        participants = list(map(lambda entry: entry.split(" - "), participant_list))
        return participants

    def turn_participants_back_to_list(self, participants):
        participant_list = list(map(lambda entry: self.combine_entry(entry), participants))
        return participant_list

    @staticmethod
    def combine_entry(entry):
        final = ""
        for x in entry:
            final += x + " - "
        final = final.strip(" - ")
        return final

    def trainer_dittos(self, participants):
        trainers = list(map(lambda entry: entry[0], participants))
        trainer_chunks = self.chunk(trainers)
        for chunk in trainer_chunks:
            if len(chunk) != len(set(chunk)):
                return True
        return False

    def character_dittos(self, participants):
        characters = list(map(lambda x: x[1], participants))
        character_chunks = self.chunk(characters)
        for chunk in character_chunks:
            if len(chunk) != len(set(chunk)):
                return True
        return False

    # Taken from https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
    @staticmethod
    def chunk(participants):
        participants = iter(participants)
        return iter(lambda: tuple(islice(participants, 4)), ())

    # Code from this thread https://codereview.stackexchange.com/questions/17703/using-python-to-model-a-single-elimination-tournament
    def tournament_round(self, no_of_teams , matchlist ):
        new_matches = []
        for team_or_match in matchlist:
            if type(team_or_match) == type([]):
                new_matches += [ self.tournament_round(no_of_teams, team_or_match ) ]
            else:
                new_matches += [ [ team_or_match, no_of_teams + 1 - team_or_match ] ]
        return new_matches

    def flatten_list(self, matches ):
        teamlist = []
        for team_or_match in matches:
            if type(team_or_match) == type([]):
                teamlist += self.flatten_list(team_or_match )
            else:
                teamlist += [team_or_match]
        return teamlist

    def generate_tournament(self, num):
        num_rounds = math.log( num, 2 )
        if num_rounds != math.trunc( num_rounds ):
            raise ValueError( "Number of teams must be a power of 2" )
        teams = 1
        result = [1]
        while teams != num:
            teams *= 2
            result = self.tournament_round( teams, result )
        return self.flatten_list( result )


def get_participants(file):
    entries = {}
    entrants = []
    with open(file, encoding="utf-8") as fp:
        # open the amiibo tsv submissionapp provides
        entry_tsv = csv.reader(fp, delimiter="\t")
        next(entry_tsv)
        for entry in entry_tsv:
            amiibo_name = entry[0]
            character_name = entry[1]
            trainer_name = entry[2]

            starting_num = 1

            name_for_bracket = f"{trainer_name} - {character_name}"
            full_name = f"{name_for_bracket} - {amiibo_name}"
            while name_for_bracket in entries:
                old = entries[name_for_bracket]
                entries.pop(name_for_bracket)
                entries[old] = old
                entrants.pop(entrants.index(name_for_bracket))
                entrants.append(old)
                name_for_bracket = full_name
                if full_name in entries:
                    starting_num += 1
                    if str(starting_num - 1) == name_for_bracket[-1]:
                        name_for_bracket = name_for_bracket.replace(
                            str(starting_num - 1), str(starting_num)
                        )
                    else:
                        name_for_bracket = f"{name_for_bracket} - {starting_num}"

            entries[name_for_bracket] = full_name
            entrants.append(name_for_bracket)
    return entrants


customtkinter.set_appearance_mode(
    "System"
)  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(
    "green"
)  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        if os.path.isfile("config.json"):
            with open("config.json") as f:
                config = json.load(f)
            self.challonge_username = config["username"]
            self.challonge_api_key = config["api_key"]
        else:
            config = {}
            self.challonge_username = None
            self.challonge_api_key = None
        self.tournament_url = None
        # configure window
        self.title("Bracket Generator")
        self.geometry(f"{1100}x{580}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create main entry and button
        self.entry = customtkinter.CTkEntry(
            self, placeholder_text="Input amiibo tsv path here"
        )
        self.entry.grid(
            row=3, column=1, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="nsew"
        )
        self.entry1 = customtkinter.CTkEntry(
            self, placeholder_text="Tournament url", height=30
        )
        self.entry1.place(relx=0.918, rely=0.06, anchor=customtkinter.CENTER)
        self.entry2 = customtkinter.CTkEntry(
            self, placeholder_text="Challonge username", height=30
        )
        self.entry2.place(relx=0.918, rely=0.13, anchor=customtkinter.CENTER)
        self.entry3 = customtkinter.CTkEntry(
            self, placeholder_text="Challonge api key", height=30
        )
        self.entry3.place(relx=0.918, rely=0.20, anchor=customtkinter.CENTER)
        self.checkbox_1 = customtkinter.CTkCheckBox(self, text="Create bracket?")
        self.checkbox_1.place(relx=0.918, rely=0.27, anchor=customtkinter.CENTER)
        # # create textbox
        self.textbox = customtkinter.CTkTextbox(self, width=200, height=400)
        self.textbox.grid(
            row=0, column=1, rowspan=2, padx=(20, 0), pady=(20, 0), sticky="nsew"
        )
        self.textbox.configure(state=customtkinter.DISABLED)

        self.main_button_1 = customtkinter.CTkButton(
            master=self,
            text="Submit",
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "#DCE4EE"),
            command=self.tsv_button_event,
        )
        self.main_button_1.grid(
            row=3, column=3, padx=(20, 20), pady=(20, 20), sticky="nsew"
        )

        if os.path.isfile("config.json"):
            with open("config.json") as f:
                config = json.load(f)
            self.challonge_username = config["username"]
            self.entry2.insert(0, self.challonge_username)
            self.challonge_api_key = config["api_key"]
            self.entry3.insert(0, self.challonge_api_key)
        else:
            config = {}
            self.challonge_username = None
            self.challonge_api_key = None

    def tsv_button_event(self):
        tsv_path = self.entry.get()
        if os.path.exists(tsv_path):
            # setup participants
            participants = get_participants(tsv_path)
            bracket = BracketGenerator(participants)
            participants = bracket.run()
            participant_string = ""
            for participant in deepcopy(participants):
                participant_string += participant + "\n"

            # redraw to the text box
            participant_string = ""
            for x in participants:
                participant_string += x + "\n"
            self.textbox.configure(state=customtkinter.NORMAL)
            self.textbox.delete("0.0", customtkinter.END)
            self.textbox.insert("0.0", participant_string)
            self.textbox.configure(state=customtkinter.DISABLED)

            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")

            # setup challonge credentials
            if self.entry3.get() != "":
                self.challonge_api_key = self.entry3.get()
            else:
                CTkMessagebox(
                    title="Error", message="Fill out challonge api key!", icon=os.path.join(base_path, "images", "cancel.png")
                )
            if self.entry2.get() != "":
                self.challonge_username = self.entry2.get()
            else:
                CTkMessagebox(
                    title="Error", message="Fill out challonge username!", icon=os.path.join(base_path, "images", "cancel.png")
                )
            if self.entry1.get() != "":
                self.tournament_url = self.entry1.get()
            else:
                CTkMessagebox(
                    title="Error", message="Fill out tournament url!", icon=os.path.join(base_path, "images", "cancel.png")
                )
            if self.checkbox_1.get() == 1:
                msg = CTkMessagebox(
                    title="Tournament Type",
                    message="Please Choose the tournament type.",
                    icon=os.path.join(base_path, "images", "question.png"),
                    option_1="Single Elimination",
                    option_2="Double Elimination",
                )

                tour = ChallongeTournament(
                    None, self.challonge_username, self.challonge_api_key
                )
                tour.create_tournament(
                    "placeholder", msg.get().lower(), self.tournament_url
                )
            else:
                tour = ChallongeTournament(
                    self.tournament_url, self.challonge_username, self.challonge_api_key
                )
            tour.mass_add_participants(participants)
            tour.start_tournament()

            config = {
                "username": self.challonge_username,
                "api_key": self.challonge_api_key,
            }
            with open("config.json", "w+") as f:
                json.dump(config, f, indent=4)
        else:
            CTkMessagebox(
                title="Error", message="TSV Path is incorrect!!!!", icon="cancel"
            )


if __name__ == "__main__":
    app = App()
    app.mainloop()
