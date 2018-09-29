import re
from typing import List

import requests
from secrets.config import headers


URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""


def run_query(query):
    print("Running Github GraphQL query")
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
    

def get_organisation_project():
    # YouthZone planning
    query = """
    {
  organization(login: "MozillaFestival") {
    projects(search: "%s", first: 1) {
      nodes {
        columns(first: 30) {
          nodes {
            url
            name
            id
            cards(first: 70) {
              nodes {
                id
                note
                content {
                  ... on Issue {
                    id
                    title
                    url
                    body
                    labels(first: 20) {
                      nodes {
                        id
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
    """ % str("YouthZone Scheduling")
    result = run_query(query)["data"]["organization"]["projects"]["nodes"][0]["columns"]["nodes"]
    return result # Returning each column in a list of columns





class Issue():
    assignees = None
    id = None
    labels = None
    title = None
    url = None
    day = None
    body = None
    comments = None
    milestone = None

    def __init__(self, id, title, url, description):
        self.id = id
        self.title = title
        self.url = url
        self.assignees = []
        self.labels = []
        self.comments = []
        self.description = description

    @property
    def description_text(self):
        output = ""
        for line in self.description:
            output = output + line + "<br>"
        return output

    @property
    def description_markdown(self):
        return
        # return Markup(markdown.Markdown(self.description))

    @property
    def url_issue_id(self):
        return self.url.split("/")[-1]


class Label():
    id = None
    name = None
    issues = None

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.issues = []


class Assignee():
    name = None
    assigned_to = None

    def __init__(self, name):
        self.name = name
        self.assigned_to = []


class ProjectCard():
    id = None
    note = None
    attached_issue = None
    project_column = None
    bookings = 0
    errors = None
    time_card = None

    def __init__(self, id, note, attached_issue):
        self.id = id
        self.note = note
        self.attached_issue: Issue = attached_issue
        self.errors = []
        self.time_blocks = None
        if not attached_issue and note:
            url = re.findall(URL_REGEX, note)
            if url and str(url[0]).startswith("https://github"):
                url = url[0]
                note = self.note
                if "\r\n" in self.note:
                    note = self.note.split("\r\n")[0]

                self.attached_issue = Issue(int(url.split("/")[-1]), note, url, "")

    @property
    def name(self):
        if self.attached_issue:
            return self.attached_issue.title
        return self.note

    @property
    def heading(self):
        if self.project_column.name[0] == "#":
            return True
        return False

    @property
    def get_errors(self):
        if "!all-day" in self.project_column.name:
            self.errors.append("All day session")
        return "\n".join(self.errors)

    @property
    def get_bgcolor(self):
        if self.errors and self.errors[0].startswith("Warning"):
            return "orange"
        elif "!all-day" in self.project_column.name:
            return "#e6e6ff"
        elif self.note and "To be filled" in self.note:
            return "#e6ffff"
        elif self.note and ("No session" in self.note or "lunch (no session)" in self.note.lower()):
            return "#e5e5e5"
        elif self.attached_issue:
            self.errors.append("No scheduling issues found for this session.")
            return "#90ee90" # Light green
        return ""

    @property
    def time(self):
        if self.time_card and self.time_blocks:
            t = self.time_card.note.split("-")
            return t[0]
        elif self.time_card and not self.time_blocks:
            t = self.time_card.note.split(" - ")
            t = re.findall(r'\d{1,2}(?:(?:am|pm)|(?::\d{1,2})(?:am|pm)?)', self.time_card.note)
            if t:
                return t[0].strip()
            return None
        if self.time_card:
            return self.time_card.note
        return None


class ProjectColumn():
    id = None
    name = None
    cards = None
    day = None

    def __init__(self, id, name):
        self.id: int = id
        self.name: str = name
        self.cards: List[ProjectCard] = []

    @property
    def heading(self):
        if self.name[0] == "#":
            return True
        return False

    @property
    def clean_name(self):
        if self.name[0] == "#":
            return self.name[1:]
        else:
            return self.name

    @property
    def day1(self):
        if "Friday" in self.name:
            return "Friday"
        elif "Saturday" in self.name:
            return "Saturday"
        elif "Sunday" in self.name:
            return "Sunday"
        else:
            return ""

    @property
    def cards_without_times(self):
        to_return = []
        for card in self.cards:
            if card and card.note and card.note[0].isdigit():
                pass
            else:
                to_return.append(card)
        return to_return


def build_project_objects(raw_columns):
    columns = []
    to_find_later_url_cards = []
    for raw_column in raw_columns:
        column = ProjectColumn(raw_column["id"], raw_column["name"])
        for raw_card in raw_column["cards"]["nodes"]:
            card_issue = None
            card = ProjectCard(raw_card["id"], raw_card["note"], card_issue)
            if raw_card["content"]:
                labels = []
                for label in raw_card["content"]["labels"]["nodes"]:
                    labels.append(Label(label["id"], label["name"]))
                card_issue = Issue(raw_card["content"]["id"], raw_card["content"]["title"], raw_card["content"]["url"], raw_card["content"]["body"])
                card_issue.labels = labels
            elif raw_card["note"]:
                url = re.findall(URL_REGEX, raw_card["note"])
                if url and str(url[0]).startswith("https://github"):  # If it is a referenced issue, aka one without a URL itself, but URL in the body
                    url = url[0]
                    card.url = url
                    to_find_later_url_cards.append(card)

            card.attached_issue = card_issue
            card.project_column = column
            column.cards.append(card)
            # card = models.ProjectCard(raw_card["id"], raw_card["note"], None, )
        columns.append(column)

    for column in columns:  # Add in the duplicate sessions by matching them to other entries that already exist
        for card in column.cards:
            for to_find_url_card in to_find_later_url_cards:
                if card.attached_issue and card.attached_issue.url and to_find_url_card.url and card.attached_issue.url == to_find_url_card.url:
                    to_find_url_card.attached_issue = card.attached_issue

                    # Set days
    day = "Friday"
    for column in columns:
        if "Saturday" in column.name:
            day = "Saturday"
        elif "Sunday" in column.name:
            day = "Sunday"
        column.day = day

    longest_column = 0  # Find the longest column to fill out each column with blank sessions
    for column in columns:
        if longest_column < len(column.cards_without_times):
            longest_column = len(column.cards_without_times)
    for column in columns:
        for card_id in range(len(column.cards), longest_column):
            column.cards.append(None)
            pass

    return columns


def add_times_to_schedule_items(project_columns: List[ProjectColumn], time_blocks=True):
    if time_blocks:
        # Basically iterate till find #, then iterate forward from that point till find next one, then apply times to those
        for project_column_id, project_column in enumerate(project_columns):
            if project_column.name.startswith("#"):
                for project_column_id2 in range(project_column_id + 1, len(project_columns)):
                    for card_id, card in enumerate(project_columns[project_column_id2].cards):
                        if card:
                            card.time_card = project_column.cards[card_id]
                            card.time_blocks = True
                    if project_columns[project_column_id2].name.startswith("#"):
                        break

    else:
        # For each session, check if the card is a time block or card/issue. If card/issue, check card before
        for project_column in project_columns:
            if not project_column.name.startswith("%"):
                for card_id, card in enumerate(project_column.cards):
                    if card and (card.attached_issue or (card.note and not card.note[0].isdigit())):
                        card.time_card = project_column.cards[card_id - 1]
                        card.time_blocks = False
                    elif card and card.note and card.note[0].isdigit():
                        card.time_card = card

        # Fill out the extra slots needed
        for project_column in project_columns:
            new_cards = []
            for card_id, card in enumerate(project_column.cards):

                if card and card.note and card.note[0].isdigit():  # If it is a time card
                    try:
                        if len(project_column.cards) > card_id + 1 and (project_column.cards[card_id + 1] and project_column.cards[card_id + 1].note and project_column.cards[card_id + 1].note[0].isdigit()):
                            # if len(project_column.cards) > card_id and (card.note and card.note[0].isdigit()):
                            new_cards.append(None)
                    except AttributeError as e:
                        print()
                new_cards.append(card)
            project_column.cards = new_cards

    return project_columns


def get_github_project_data():
    raw_data = get_organisation_project()
    columns = build_project_objects(raw_data)
    columns_times = add_times_to_schedule_items(columns)
    return columns_times