import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
import types
import zoneinfo
import importlib

class DummySecrets:
    def __getitem__(self, key):
        if key == "SMTP_PORT":
            return "587"
        return "dummy"

class DummyStreamlit:
    secrets = DummySecrets()
    def error(self, msg):
        pass
    def warning(self, msg):
        pass

class Response:
    def __init__(self, data):
        self.data = data
        self.error = None
        self.status_code = 200

class FakeQuery:
    def __init__(self, supabase, name):
        self.supabase = supabase
        self.name = name
        self.operation = None
        self.data = None
        self.filters = []
        self.single_result = False
        self.order_column = None
    def insert(self, data):
        self.operation = 'insert'
        self.data = data
        return self
    def update(self, data):
        self.operation = 'update'
        self.data = data
        return self
    def select(self, *args):
        self.operation = 'select'
        return self
    def eq(self, column, value):
        self.filters.append((column, value))
        return self
    def order(self, column):
        self.order_column = column
        return self
    def single(self):
        self.single_result = True
        return self
    def execute(self):
        table = self.supabase.tables.setdefault(self.name, [])
        if self.operation == 'insert':
            if self.name == 'employees' and 'id' not in self.data:
                self.data['id'] = len(table) + 1
            table.append(self.data)
            return Response([self.data])
        elif self.operation == 'update':
            updated = None
            for row in table:
                if all(row.get(c) == v for c, v in self.filters):
                    row.update(self.data)
                    updated = row
            return Response([updated] if updated else [])
        elif self.operation == 'select':
            results = [row for row in table if all(row.get(c) == v for c, v in self.filters)]
            if self.order_column:
                results.sort(key=lambda r: r.get(self.order_column))
            if self.single_result:
                return Response(results[0] if results else None)
            return Response(results)
        return Response([])

class FakeSupabase:
    def __init__(self):
        self.tables = {}
    def table(self, name):
        return FakeQuery(self, name)

@pytest.fixture
def utils_module(monkeypatch):
    fake_supabase = FakeSupabase()
    class SimpleTZ(zoneinfo.ZoneInfo):
        def __new__(cls, name):
            return zoneinfo.ZoneInfo.__new__(cls, name)
        def localize(self, dt):
            return dt.replace(tzinfo=self)
    pytz_mod = types.ModuleType("pytz")
    pytz_mod.timezone = lambda name: SimpleTZ(name)
    pytz_mod.UTC = SimpleTZ("UTC")
    monkeypatch.setitem(sys.modules, "pytz", pytz_mod)
    supabase_mod = types.SimpleNamespace(create_client=lambda url, key: fake_supabase, Client=object)
    monkeypatch.setitem(sys.modules, 'supabase', supabase_mod)
    monkeypatch.setitem(sys.modules, 'streamlit', DummyStreamlit())
    import utils
    importlib.reload(utils)
    return utils, fake_supabase
