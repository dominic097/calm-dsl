import uuid
import os
import pytest
import json
from distutils.version import LooseVersion as LV

from calm.dsl.store.version import Version
from calm.dsl.runbooks import *
from calm.dsl.runbooks import (
    RunbookTask as CalmTask,
)
from calm.dsl.builtins import CalmTask as CalmVarTask, Metadata


@runbook
def DslAllEscriptTasks(endpoints=[], default=False):
    "Runbook example with All Escript Type Tasks"

    with CalmTask.Decision.escript.py3(
        name="escript_decision",
        filename=os.path.join("scripts", "escript_decision_true.py"),
    ) as d:
        if d.ok:
            CalmTask.Exec.escript.py3(
                name="escript_exec", filename=os.path.join("scripts", "escript_exec.py")
            )
            CalmTask.SetVariable.escript.py3(
                name="escript_setvar",
                filename=os.path.join("scripts", "escript_setvariable.py"),
                variables=["var1"],
            )
        else:
            CalmTask.Exec.escript.py3(
                name="escript_exec_print", script="""print ("Decision else part")"""
            )

    with CalmTask.Decision.escript.py3(
        name="escript2_decision",
        filename=os.path.join("scripts", "escript_decision_false.py"),
    ) as d:
        if d.ok:
            CalmTask.Exec.escript.py3(
                name="escript3_exec_print", script="""print ("Decision if part")"""
            )
        else:
            CalmTask.Exec.escript.py3(
                name="escript2_exec",
                filename=os.path.join("scripts", "escript_exec.py"),
            )
            CalmTask.SetVariable.escript.py3(
                name="escript2_setvar",
                filename=os.path.join("scripts", "escript_setvariable.py"),
                variables=["var1"],
            )

    with CalmTask.Decision.escript.py3(
        name="escript3_decision",
        filename=os.path.join("scripts", "escript_decision_true.py"),
    ) as d:
        if d.ok:
            CalmTask.Exec.escript.py3(
                name="escript3_exec",
                filename=os.path.join("scripts", "escript_exec.py"),
            )
            CalmTask.SetVariable.escript.py3(
                name="escript3_setvar",
                filename=os.path.join("scripts", "escript_setvariable.py"),
                variables=["var1"],
            )
        else:
            CalmTask.Exec.escript.py3(
                name="escript3_exec_print", script="""print("Decision else part")"""
            )


def _test_compare_compile_result(Runbook, json_file):
    """compares the runbook compilation and known output"""

    print("JSON compilation test for {}".format(Runbook.action_name))
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, json_file)

    generated_json = json.loads(runbook_json(Runbook))
    known_json = json.loads(open(file_path).read())
    CALM_VERSION = Version.get_version("Calm")
    if LV(CALM_VERSION) < LV("3.9.0"):
        for task in known_json["runbook"]["task_definition_list"]:
            if "status_map_list" in task:
                task.pop("status_map_list")
    keys_to_remove = {
        "global_variable_reference_list",
        "execution_name",
        "output_variable_list",
    }
    remove_keys_recursive(known_json, keys_to_remove)
    remove_keys_recursive(generated_json, keys_to_remove)
    assert sorted(known_json.items()) == sorted(generated_json.items())
    print("JSON compilation successful for {}".format(Runbook.action_name))


def remove_keys_recursive(obj, keys):
    """Recursively remove any dict keys in `keys` from obj (in-place)."""
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            if k in keys:
                obj.pop(k, None)
        for v in obj.values():
            remove_keys_recursive(v, keys)
    elif isinstance(obj, list):
        for item in obj:
            remove_keys_recursive(item, keys)


@pytest.mark.runbook
@pytest.mark.escript
def test_all_escript_type_tasks():
    _test_compare_compile_result(DslAllEscriptTasks, "./jsons/escript_all_tasks.json")
