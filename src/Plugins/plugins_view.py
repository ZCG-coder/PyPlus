from src.modules import json, ttk
from src.Utils.images import get_image
from src.Widgets.winframe import WinFrame


class PluginView(WinFrame):
    def __init__(self, master):
        super().__init__(master, "Plugins", icon=get_image("info"))
        with open("Config/plugin-data.json") as f:
            self.settings = json.load(f)
        self.plugins = ttk.Treeview(self, columns=("name", "desc"))
        self.plugins.heading("name", text="Name", anchor="w")
        self.plugins.heading("desc", text="Description", anchor="w")

        self.plugins.column("#0", width=15, minwidth=15, stretch=False)
        self.plugins.column("name", width=50, minwidth=50)
        self.plugins.column("desc", width=80, minwidth=80)
        self.plugins.pack(fill="both", expand=True)
        self.update_plugins()

    def update_plugins(self):
        node = self.plugins.insert(
            "",
            "end",
            values=("Bundled", "Comes with PyPlus, you cannot uninstall."),
            open=True,
        )
        docs = []
        for index, item in enumerate(self.settings.keys()):
            exec(
                f"""\
from src.{self.settings[item]} import Plugin
doc = Plugin.__doc__
docs.append(doc)""",
                locals(),
                globals(),
            )
            self.plugins.insert(node, "end", values=(item, docs[index]))
