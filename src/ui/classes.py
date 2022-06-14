import supervisely as sly
import sly_globals as g


def init(api: sly.Api, data, state, project_id, project_meta: sly.ProjectMeta):
    stats = api.project.get_stats(project_id)
    class_images = {}
    for item in stats["images"]["objectClasses"]:
        class_images[item["objectClass"]["name"]] = item["total"]
    class_objects = {}
    for item in stats["objects"]["items"]:
        class_objects[item["objectClass"]["name"]] = item["total"]

    classes_json = project_meta.obj_classes.to_json()
    for obj_class in classes_json:
        obj_class["imagesCount"] = class_images[obj_class["title"]]
        obj_class["objectsCount"] = class_objects[obj_class["title"]]

    unlabeled_count = 0
    for ds_counter in stats["images"]["datasets"]:
        unlabeled_count += ds_counter["imagesNotMarked"]

    data["done3"] = False
    state["collapsed3"] = True
    state["disabled3"] = True
    data["classes"] = classes_json
    state["selectedClasses"] = []
    state["classes"] = len(classes_json) * [True]
    data["unlabeledCount"] = unlabeled_count


@g.my_app.callback("select_classes")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def build_heatmap(api: sly.Api, task_id, context, state, app_logger):
    fields = [
        {"field": f"data.done3", "payload": True},
        {"field": "state.collapsed4", "payload": False},
        {"field": "state.disabled4", "payload": False},
        {"field": "state.activeStep", "payload": 4},
        {"field": "state.selectedClasses", "payload": state["selectedClasses"]},
    ]
    g.api.app.set_fields(g.task_id, fields)