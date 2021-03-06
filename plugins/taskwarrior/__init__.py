"""Interact with Taskwarrior."""

import re
import datetime
import os
import sys
import traceback
from importlib import import_module
from pathlib import Path
from shutil import which
from subprocess import PIPE, Popen
from typing import Optional, Tuple, Union

import gi
import taskw
from dateutil import tz
from fuzzywuzzy import process
from overrides import overrides
from taskw_gcal_sync import TaskWarriorSide

import albertv0 as v0

gi.require_version("Notify", "0.7")  # isort:skip
from gi.repository import GdkPixbuf, Notify  # isort:skip


# metadata ------------------------------------------------------------------------------------
__iid__ = "PythonInterface/v0.2"
__prettyname__ = "Taskwarrior interaction"
__version__ = "0.1.0"
__trigger__ = "t "
__author__ = "Nikos Koukis"
__dependencies__ = ["task"]
__homepage__ = "https://github.com/bergercookie/awesome-albert-plugins"
__simplename__ = "taskwarrior"

# initial checks ------------------------------------------------------------------------------

# icon ----------------------------------------------------------------------------------------
icon_path = os.path.join(os.path.dirname(__file__), "taskwarrior.svg")
icon_path_b = os.path.join(os.path.dirname(__file__), "taskwarrior_blue.svg")
icon_path_r = os.path.join(os.path.dirname(__file__), "taskwarrior_red.svg")
icon_path_y = os.path.join(os.path.dirname(__file__), "taskwarrior_yellow.svg")
icon_path_c = os.path.join(os.path.dirname(__file__), "taskwarrior_cyan.svg")
icon_path_g = os.path.join(os.path.dirname(__file__), "taskwarrior_green.svg")

# initial configuration -----------------------------------------------------------------------
cache_path = Path(v0.cacheLocation()) / __simplename__
config_path = Path(v0.configLocation()) / __simplename__
data_path = Path(v0.dataLocation()) / __simplename__

reminders_tag_path = config_path / "reminders_tag"

tw_side = TaskWarriorSide(enable_caching=True)
tw_side.start()

dev_mode = True

# regular expression to match URLs
# https://gist.github.com/gruber/8891611
url_re = re.compile(r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""")

# plugin main functions -----------------------------------------------------------------------


def do_notify(msg: str, image=None):
    app_name = "Taskwarrior"
    Notify.init(app_name)
    image = image
    print("msg: ", msg)
    print("image: ", image)
    n = Notify.Notification.new(app_name, msg, image)
    n.show()


def get_tasks_of_date(date: datetime.date):
    tasks = tw_side.get_all_items(include_completed=False)

    return [
        t
        for t in tasks
        # acount for hack in taskw_gcal_sync - tasks scheduled for yesterday 23:59:00 are
        # actually today's tasks
        if "due" in t.keys()
        and t["due"]
        != datetime.datetime(
            year=date.year,
            month=date.month,
            day=date.day,
            hour=23,
            minute=0,
            tzinfo=tz.tzutc(),
        )
        and (
            t["due"].date() == date
            or t["due"]
            == datetime.datetime(
                year=date.year,
                month=date.month,
                day=date.day - 1,
                hour=23,
                minute=0,
                tzinfo=tz.tzutc(),
            )
        )
    ]


def initialize():
    # Called when the extension is loaded (ticked in the settings) - blocking

    # create cache location
    config_path.mkdir(parents=False, exist_ok=True)


def finalize():
    pass


def handleQuery(query):
    results = []

    if query.isTriggered:
        try:
            if "disableSort" in dir(query):
                query.disableSort()

            results_setup = setup(query)
            if results_setup:
                return results_setup
            tasks = tw_side.get_all_items(include_completed=False)

            query_str = query.string

            if len(query_str) < 2:
                tw_side.reload_items = True
                results.extend([s.get_as_albert_item() for s in subcommands])

                tasks.sort(key=lambda t: t["urgency"], reverse=True)
                results.extend([get_tw_item(task) for task in tasks])

            else:
                subcommand_query = get_subcommand_query(query_str)

                if subcommand_query:
                    results.extend(
                        subcommand_query.command.get_as_albert_items_full(
                            subcommand_query.query
                        )
                    )

                    if not results:
                        results.append(get_as_item(text="No results"))

                else:
                    # find relevant results
                    desc_to_task = {task["description"]: task for task in tasks}
                    matched = process.extract(query_str, list(desc_to_task.keys()), limit=30)
                    for m in [elem[0] for elem in matched]:
                        task = desc_to_task[m]
                        results.append(get_tw_item(task))

        except Exception:  # user to report error
            if dev_mode:
                print(traceback.format_exc())
                raise

            results.insert(
                0,
                v0.Item(
                    id=__prettyname__,
                    icon=icon_path,
                    text="Something went wrong! Press [ENTER] to copy error and report it",
                    actions=[
                        v0.ClipAction(
                            f"Copy error - report it to {__homepage__[8:]}",
                            f"{traceback.format_exc()}",
                        )
                    ],
                ),
            )

    return results


def get_as_item(**kargs) -> v0.Item:
    if "icon" in kargs:
        icon = kargs.pop("icon")
    else:
        icon = icon_path
    return v0.Item(id=__prettyname__, icon=icon, **kargs)


# supplementary functions ---------------------------------------------------------------------


def setup(query):

    results = []

    if not which("task"):
        results.append(
            v0.Item(
                id=__prettyname__,
                icon=icon_path,
                text=f'"taskwarrior" is not installed.',
                subtext='Please install and configure "taskwarrior" accordingly.',
                actions=[
                    v0.UrlAction(
                        'Open "taskwarrior" website', "https://taskwarrior.org/download/"
                    )
                ],
            )
        )
        return results

    return results


def save_data(data: str, data_name: str):
    """Save a piece of data in the configuration directory."""
    with open(config_path / data_name, "w") as f:
        f.write(data)


def load_data(data_name) -> str:
    """Load a piece of data from the configuration directory."""
    with open(config_path / data_name, "r") as f:
        data = f.readline().strip().split()[0]

    return data


def get_as_subtext_field(field, field_title=None):
    s = ""
    if field:
        s = f"{field} | "
    else:
        return ""

    if field_title:
        s = f"{field_title}:" + s

    return s


def urgency_to_visuals(prio: Union[float, None]) -> Tuple[Union[str, None], Path]:
    if prio is None:
        return None, icon_path
    elif prio < 4:
        return "↓", icon_path_b
    elif prio < 8:
        return "↘", icon_path_c
    elif prio < 11:
        return "-", icon_path_g
    elif prio < 15:
        return "↗", icon_path_y
    else:
        return "↑", icon_path_r


def run_tw_action(args_list: list, need_pty=False):
    args_list = ["task", "rc.recurrence.confirmation=no", "rc.confirmation=off", *args_list]

    if need_pty:
        args_list.insert(0, "x-terminal-emulator")
        args_list.insert(1, "-e")

    proc = Popen(args_list, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()

    if proc.returncode != 0:
        image = icon_path_r
        msg = f'stdout: {stdout.decode("utf-8")} | stderr: {stderr.decode("utf-8")}'
    else:
        image = icon_path
        msg = stdout.decode("utf-8")

    do_notify(msg=msg, image=image)
    tw_side.reload_items = True


def add_reminder(task_id, reminders_tag: list):
    args_list = ["modify", task_id, f"+{reminders_tag}"]
    run_tw_action(args_list)


def get_tw_item(task: taskw.task.Task) -> v0.Item:
    """Get a single TW task as an Albert Item."""
    field = get_as_subtext_field

    actions = [
        v0.FuncAction(
            "Complete task",
            lambda args_list=["done", tw_side.get_task_id(task)]: run_tw_action(args_list),
        ),
        v0.FuncAction(
            "Delete task",
            lambda args_list=["delete", tw_side.get_task_id(task)]: run_tw_action(args_list),
        ),
        v0.FuncAction(
            "Start task",
            lambda args_list=["start", tw_side.get_task_id(task)]: run_tw_action(args_list),
        ),
        v0.FuncAction(
            "Stop task",
            lambda args_list=["stop", tw_side.get_task_id(task)]: run_tw_action(args_list),
        ),
        v0.FuncAction(
            "Edit task interactively",
            lambda args_list=["edit", tw_side.get_task_id(task)]: run_tw_action(args_list,
                                                                                need_pty=True),
        ),
        v0.ClipAction("Copy task UUID", f"{tw_side.get_task_id(task)}"),
    ]

    found_urls = url_re.findall(task["description"])
    if "annotations" in task.keys():
        found_urls.extend(url_re.findall(" ".join(task["annotations"])))

    for url in found_urls[-1::-1]:
        actions.insert(0, v0.UrlAction(f"Open {url}", url))

    if reminders_tag_path.is_file():
        reminders_tag = load_data(reminders_tag_path)
        actions.append(
            v0.FuncAction(
                f"Add to Reminders (+{reminders_tag})",
                lambda args_list=[
                    "modify",
                    tw_side.get_task_id(task),
                    f"+{reminders_tag}",
                ]: run_tw_action(args_list),
            )
        )

    urgency_str, icon = urgency_to_visuals(task.get("urgency"))
    return get_as_item(
        text=f'{task["description"]}',
        subtext="{}{}{}{}{}".format(
            field(urgency_str),
            "ID: {}... | ".format(tw_side.get_task_id(task)[:8]),
            field(task["status"]),
            field(task.get("tags"), "tags"),
            field(task.get("due"), "due"),
        )[:-2],
        icon=icon,
        completion="",
        actions=actions,
    )


# subcommands ---------------------------------------------------------------------------------
class Subcommand:
    def __init__(self, *, name, desc):
        self.name = name
        self.desc = desc

    def get_as_albert_item(self):
        return get_as_item(text=self.desc, completion=f"{__trigger__} {self.name} ")

    def get_as_albert_items_full(self, query_str):
        return [self.get_as_albert_item()]

    def __str__(self) -> str:
        return f"Name: {self.name} | Description: {self.desc}"


class AddSubcommand(Subcommand):
    def __init__(self, **kargs):
        super(AddSubcommand, self).__init__(**kargs)

    @overrides
    def get_as_albert_items_full(self, query_str):
        item = self.get_as_albert_item()
        item.subtext = query_str
        item.addAction(
            v0.FuncAction(
                "Add task",
                lambda args_list=["add", *query_str.split()]: run_tw_action(args_list),
            )
        )
        return [item]


class TodayTasks(Subcommand):
    def __init__(self, **kargs):
        super(TodayTasks, self).__init__(**kargs)

    @overrides
    def get_as_albert_items_full(self, query_str):
        return [get_tw_item(t) for t in get_tasks_of_date(datetime.datetime.today())]


class YesterdayTasks(Subcommand):
    def __init__(self, **kargs):
        super(YesterdayTasks, self).__init__(**kargs)

    @overrides
    def get_as_albert_items_full(self, query_str):
        date = datetime.datetime.today().date() - datetime.timedelta(days=1)
        return [get_tw_item(t) for t in get_tasks_of_date(date)]


class TomorrowTasks(Subcommand):
    def __init__(self, **kargs):
        super(TomorrowTasks, self).__init__(**kargs)

    @overrides
    def get_as_albert_items_full(self, query_str):
        date = datetime.datetime.today().date() + datetime.timedelta(days=1)
        return [get_tw_item(t) for t in get_tasks_of_date(date)]


class SubcommandQuery:
    def __init__(self, subcommand: Subcommand, query: str):
        """
        Query for a specific subcommand.

        :query: Query text - doesn't include the subcommand itself
        """

        self.command = subcommand
        self.query = query

    def __str__(self) -> str:
        return f"Command: {self.command}\nQuery Text: {self.query}"


subcommands = [
    AddSubcommand(name="add", desc="Add a new task"),
    TodayTasks(name="today", desc="Today's tasks"),
    YesterdayTasks(name="yesterday", desc="Yesterday's tasks"),
    TomorrowTasks(name="tomorrow", desc="Tomorrow's tasks"),
]


def get_subcommand_for_name(name: str) -> Optional[Subcommand]:
    """Get a subcommand with the indicated name."""
    matching = [s for s in subcommands if s.name.lower() == name.lower()]
    if matching:
        return matching[0]


def get_subcommand_query(query_str: str) -> Optional[SubcommandQuery]:
    """
    Determine whether current query is of a subcommand.

    If so first returned the corresponding SubcommandQeury object.
    """
    if not query_str:
        return None

    # spilt:
    # "subcommand_name rest of query" -> ["subcommand_name", "rest of query""]
    query_parts = query_str.strip().split(None, maxsplit=1)

    if len(query_parts) < 2:
        query_str = ""
    else:
        query_str = query_parts[1]

    subcommand = get_subcommand_for_name(query_parts[0])
    if subcommand:
        return SubcommandQuery(subcommand=subcommand, query=query_str)
