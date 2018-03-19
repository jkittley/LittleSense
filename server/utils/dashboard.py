import json
from unipath import Path
from config import settings

class DashBoards():

    def __init__(self):
        self.dashes = []
        self.update()

    def get(self, **kwargs):
        seek_slug = kwargs.get('slug', None)
        if seek_slug is not None:
            results = [d for d in self.dashes if d.slug == seek_slug]
            if len(results) > 0:
                return results[0]
        return None

    def update(self):
        self.dashes = []
        for x in Path(settings.DASHBOARDS_PATH).listdir(pattern="*.json"):
            self.dashes.append(Dashboard(x))

    def __len__(self):
        return len(self.dashes)

    def __getitem__(self, index):
        return self.dashes[index]

    def __iter__(self):
        return (d for d in self.dashes)

    def __str__(self):
        return "Dashboard List"

    def __repr__(self):
        return "Dashboards()"


class Dashboard():

    def __init__(self, file_path):
        self.file_path = file_path
        self.loadJSON(file_path)

    def loadJSON(self, file_path):
        p = Path(file_path)
        self.path = p
        self.title = str(p.stem).capitalize().replace('_',' ')
        self.slug = p.stem

        json_data = json.load(open(self.path.absolute()))

        for key, value in json_data.items():
            setattr(self, key, value)
    
    def __str__(self):
        return "Dashboard"

    def __repr__(self):
        return "Dashboard({})".format(self.file_path)
        