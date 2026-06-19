import os
import supervisely as sly
import sly_globals as g

train_set = None


def _selected_dataset_keys(selected_datasets):
    keys = set()
    if not selected_datasets:
        return keys
    if not isinstance(selected_datasets, list):
        selected_datasets = [selected_datasets]
    for dataset in selected_datasets:
        if isinstance(dataset, dict):
            for key in ["id", "value", "name", "label"]:
                if dataset.get(key) is not None:
                    keys.add(str(dataset[key]))
        else:
            keys.add(str(dataset))
    return keys


def _get_selected_datasets(api, selected_datasets):
    datasets = api.dataset.get_list(g.project_info.id)
    selected_keys = _selected_dataset_keys(selected_datasets)
    if not selected_keys:
        return datasets
    return [
        dataset
        for dataset in datasets
        if str(dataset.id) in selected_keys or dataset.name in selected_keys
    ]


def init(project_info, project_meta: sly.ProjectMeta, data, state):
    data["randomSplit"] = [
        {"name": "included_data", "type": "success"},
        {"name": "total", "type": "gray"},
    ]
    data["totalImagesCount"] = project_info.items_count

    train_percent = 80
    if project_info.items_count is not None:
        train_count = int(project_info.items_count / 100 * train_percent)
    else:
        sly.logger.warn("Project is empty.")
        raise RuntimeError("Project is empty. Please add data to the project to proceed.")
    state["randomSplit"] = {
        "count": {"total": project_info.items_count, "included_data": train_count},
        "percent": {"total": 100, "included_data": train_percent},
    }

    state["splitMethod"] = "random"
    state["datasets"] = []
    state["imagesCount"] = None
    data["done2"] = False
    state["collapsed2"] = False
    state["disabled2"] = False
    state["activeStep"] = 2


@g.my_app.callback("create_splits")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def create_splits(api: sly.Api, task_id, context, state, app_logger):
    images_count = state["randomSplit"]["count"]["included_data"]
    if state.get("splitMethod") == "datasets" and state.get("datasets"):
        datasets = _get_selected_datasets(api, state["datasets"])
        if len(datasets) == 0:
            raise RuntimeError("Selected datasets were not found. Please reselect datasets.")
        images_count = sum(dataset.items_count for dataset in datasets)

    fields = [
        {"field": f"data.done2", "payload": True},
        {"field": f"state.imagesCount", "payload": images_count},
        {"field": f"state.datasets", "payload": state["datasets"]},
        {"field": "state.collapsed3", "payload": False},
        {"field": "state.disabled3", "payload": False},
        {"field": "state.activeStep", "payload": 3},
    ]
    g.api.app.set_fields(g.task_id, fields)
