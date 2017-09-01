# -*- coding: utf-8 -*-

"""Console script for sheets."""

import click
import os
import threading

default_data_path = os.path.normpath(os.path.join(os.path.abspath(__file__), "../../data"))

@click.command()
@click.argument("path", default=default_data_path)
def main(path):
    """Console script for sheets."""
    from . import http
    path = os.path.abspath(path)
    os.chdir(path)
    t = threading.Thread(target=http.start)
    t.start()
    print("Starting socket server on http://localhost:10101")
    from .server import run_server
    from .env import Environment
    from .datalayer import Model
    from .router import Router
    env = Environment(path)
    model = Model(env)
    router = Router(env=env, model=model)
    router.register()
    print("Saving files in %s" % env.path)
    run_server(10101)


if __name__ == "__main__":
    main()
