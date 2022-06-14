import supervisely as sly
import sly_globals as g
import input_project as input_project
import splits as train_val_split
import classes
import heatmap_calculation
import result
# import artifacts as artifacts


@sly.timeit
def init(data, state):
    state["activeStep"] = 2
    state["restartFrom"] = None
    input_project.init(data, state)
    train_val_split.init(g.project_info, g.project_meta, data, state)
    classes.init(sly.Api.from_env(), data, state, g.project_info.id, g.project_meta)
    heatmap_calculation.init(data, state)
    result.init(data, state)


@g.my_app.callback("restart")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def restart(api: sly.Api, task_id, context, state, app_logger):
    restart_from_step = state["restartFrom"]
    data = {}
    state = {}

    if restart_from_step <= 2:
        train_val_split.init(g.project_info, g.project_meta, data, state)
    if restart_from_step <= 3:
        classes.init(sly.Api.from_env(), data, state, g.project_info.id, g.project_meta)
    if restart_from_step <= 4:
        heatmap_calculation.init(data, state)
    if restart_from_step <= 5:
        result.init(data, state)

    fields = [
        {"field": "data", "payload": data, "append": True, "recursive": False},
        {"field": "state", "payload": state, "append": True, "recursive": False},
        {"field": "state.restartFrom", "payload": None},
        {"field": f"state.collapsed{restart_from_step}", "payload": False},
        {"field": f"state.disabled{restart_from_step}", "payload": False},
        {"field": "state.activeStep", "payload": restart_from_step},
    ]
    g.api.app.set_fields(g.task_id, fields)
    g.api.app.set_field(task_id, "data.scrollIntoView", f"step{restart_from_step}")