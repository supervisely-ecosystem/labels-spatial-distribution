import os
import supervisely_lib as sly
import sly_globals as g

train_set = None


def init(project_info, project_meta: sly.ProjectMeta, data, state):
    data["randomSplit"] = [
        {"name": "included_data", "type": "success"},
        {"name": "total", "type": "gray"},
    ]
    data["totalImagesCount"] = project_info.items_count

    train_percent = 80
    train_count = int(project_info.items_count / 100 * train_percent)
    state["randomSplit"] = {
        "count": {
            "total": project_info.items_count,
            "included_data": train_count
        },
        "percent": {
            "total": 100,
            "included_data": train_percent
        },
        "shareImagesBetweenSplits": False,
        "sliderDisabled": False,
    }

    state["splitMethod"] = "random"
    state["datasets"] = []
    state["untaggedImages"] = "train"
    state["imagesCount"] = None
    data["done2"] = False
    state["collapsed2"] = True
    state["disabled2"] = True


@g.my_app.callback("create_splits")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def create_splits(api: sly.Api, task_id, context, state, app_logger):
    fields = [
        {"field": f"data.done2", "payload": True},
        {"field": f"state.imagesCount", "payload": state["randomSplit"]["count"]["included_data"]},
        {"field": f"state.datasets", "payload": state["datasets"]},
        {"field": "state.collapsed3", "payload": False},
        {"field": "state.disabled3", "payload": False},
        {"field": "state.activeStep", "payload": 3},
    ]
    g.api.app.set_fields(g.task_id, fields)