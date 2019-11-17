import pandas as pd


class EventStore:
    _df_columns = ("timestamp", "action", "type", "payload")

    def __init__(self):
        self.df = pd.DataFrame(columns=self._df_columns)

    def add_event(self, adict):
        event_dict = self._extract_values(adict)
        self.df = self.df.append(event_dict, ignore_index=True)

    def all(self):
        records = self.df.to_records()
        return self._format_records(records)

    def _extract_values(self, adict):
        return {key: adict.get(key) for key in self._df_columns}

    def _format_records(self, records):
        return [{key: rec[key] for key in self._df_columns} for rec in records]
