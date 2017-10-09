import rocksdb
import os
import json
from . import datalayer

class History:

    def __init__(self, base_path):
        self.base_path = base_path
        self.db_path = os.path.join(self.base_path, "sheets-history.db")
        self.db = rocksdb.DB(self.db_path, rocksdb.Options(create_if_missing=True))

    def save_command(self, command):
        id = command.id.encode('ascii')
        self.db.put(id, json.dumps(command.asJson).encode('UTF-8'))

    def get_commands(self, return_invalid=False):
        it = self.db.itervalues()
        it.seek_to_first()
        commands = [json.loads(c.decode('UTF-8')) for c in it]
        if return_invalid:
            commands = [datalayer.hydrate(c, if_invalid=c) for c in commands]
        else:
            commands = [datalayer.hydrate(c, if_invalid=None) for c in commands]
            commands = [c for c in commands if c is not None]
        return list(commands)

    def clean_commands(self):
        commands = self.get_commands(return_invalid=True)
        remove_ids = []
        while commands:
            last = commands.pop()
            if isinstance(last, dict):
                # Some invalid command in history
                remove_ids.append(last["id"])
                continue
            to_remove = last.scan_back(commands)
            if to_remove:
                for c in to_remove:
                    if c is not last:
                        commands.remove(c)
                    remove_ids.append(c.id)
        batch = rocksdb.WriteBatch()
        for id in remove_ids:
            id = id.encode('ascii')
            print("Deleting", id)
            batch.delete(id)
            self.db.write(batch)
