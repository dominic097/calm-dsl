# Bug fix

In this patch release, we have fixed a missing import statement in the blueprints CLI module that was causing import errors. The required import `from distutils.version import LooseVersion as LV` has been added to `calm/dsl/cli/bps.py` to ensure proper version comparison functionality in blueprint-related commands.