import supervisely_lib as sly
import matplotlib.pyplot as plt
import numpy as np
import sly_globals as g
import random
from datetime import datetime
import os


def init_progress(index, state):
    state[f"progress{index}"] = False
    state[f"progressCurrent{index}"] = 0
    state[f"progressTotal{index}"] = None
    state[f"progressPercent{index}"] = 0


def init(data, state):
    init_progress("AvgSize", state)
    init_progress("Heatmap", state)
    init_progress("Classes", state)
    state["heatmapInProgress"] = False
    data["done4"] = False
    data["avgSize"] = None
    state["currentClass"] = None
    state["collapsed4"] = True
    state["disabled4"] = True


def calculate_avg_img_size(datasets, imagesCount, imagesPart, max_imgs_for_average = 30):
    fields = [
        {"field": "state.progressAvgSize", "payload": True},
        {"field": "state.progressTotalAvgSize", "payload": min(imagesCount, max_imgs_for_average)},
    ]
    g.api.app.set_fields(g.task_id, fields)
    sizes = []
    included_images = 0

    for ds_idx, dataset in enumerate(datasets):
        images = g.api.image.get_list(dataset.id)
        random.shuffle(images)
        if imagesCount > 0:
            if ds_idx >= len(datasets) - 1:
                img_cnt = imagesCount - included_images
                if included_images + img_cnt >= max_imgs_for_average:
                    img_cnt = max_imgs_for_average - included_images
                images = images[:img_cnt]
            else:
                img_cnt = int(len(images) * imagesPart)
                if included_images + img_cnt >= max_imgs_for_average:
                    img_cnt = max_imgs_for_average - included_images
                images = images[:img_cnt]

        for img_idx, item_name in enumerate(images):
            sizes.append((item_name.height, item_name.width))
            included_images += 1
            fields = [
                {"field": "state.progressCurrentAvgSize", "payload": included_images},
                {"field": "state.progressPercentAvgSize", "payload": int(included_images / min(imagesCount, max_imgs_for_average) * 100)},
            ]
            g.api.app.set_fields(g.task_id, fields)

    g.api.app.set_field(g.task_id, "state.progressAvgSize", False)
    sizes = np.array(sizes)
    avg_img_size = (sizes[:, 0].mean().astype(np.int32).item(), sizes[:, 1].mean().astype(np.int32).item())
    return avg_img_size

def get_heatmap_image(api, state, class_name, class_idx, avg_img_size):
    datasets_to_heatmap = state["datasets"]
    imagesCount = state["imagesCount"]
    geometry_types_to_heatmap = ["polygon", "rectangle", "bitmap"]
    cmap = plt.cm.get_cmap('viridis')
    meta_json = api.project.get_meta(g.project_info.id)
    meta = sly.ProjectMeta.from_json(meta_json)
    imagesPart = imagesCount / g.project_info.items_count

    if datasets_to_heatmap:
        datasets = [dataset for dataset in api.dataset.get_list(g.project_info.id) if dataset.name in datasets_to_heatmap]
    else:
        datasets = api.dataset.get_list(g.project_info.id)
    if avg_img_size is None:
        avg_img_size = calculate_avg_img_size(datasets, imagesCount, imagesPart)

    fields = [
        {"field": "state.progressHeatmap", "payload": True},
        {"field": "state.progressClasses", "payload": True},
        {"field": "state.progressTotalHeatmap", "payload": imagesCount},
        {"field": "state.progressTotalClasses", "payload": len(state["selectedClasses"])},
        {"field": "state.currentClass", "payload": class_name},
        {"field": "state.progressCurrentClasses", "payload": class_idx + 1},
        {"field": "state.progressPercentClasses", "payload": int((class_idx + 1) / len(state["selectedClasses"]) * 100)},
    ]
    g.api.app.set_fields(g.task_id, fields)

    heatmap = np.zeros(avg_img_size + (3,), dtype=np.float32)
    included_images = 0
    for ds_idx, dataset in enumerate(datasets):

        images = api.image.get_list(dataset.id)
        random.shuffle(images)
        if imagesCount > 0:
            if ds_idx >= len(datasets) - 1:
                images = images[:imagesCount-included_images]
            else:
                img_cnt = int(len(images) * imagesPart)
                images = images[:img_cnt]

        for img_idx, item_infos in enumerate(sly.batched(images)):
            img_ids = [x.id for x in item_infos]
            ann_infos = api.annotation.download_batch(dataset.id, img_ids)
            anns = [sly.Annotation.from_json(x.annotation, meta) for x in ann_infos]
            for ann in anns:
                ann = ann.resize(avg_img_size)
                temp_canvas = np.zeros(avg_img_size + (3,), dtype=np.uint8)
                for label in ann.labels:
                    if label.obj_class.name == class_name and label.geometry.geometry_name() in geometry_types_to_heatmap:
                        ann = ann.delete_label(label)
                        label.draw(temp_canvas, color=(1, 1, 1))
                heatmap += temp_canvas

            included_images += len(item_infos)
            fields = [
                {"field": "state.progressCurrentHeatmap", "payload": included_images},
                {"field": "state.progressPercentHeatmap", "payload": int(included_images / imagesCount * 100)},
            ]
            g.api.app.set_fields(g.task_id, fields)


    os.makedirs("imgs", exist_ok=True)
    local_filename = os.path.join("imgs", f"heatmap_{class_name}_{datetime.now()}.png")
    fig = plt.figure(figsize=(avg_img_size[1] / 80.0, avg_img_size[0] / 80.0))

    plt.imshow(heatmap[:,:,0], cmap=cmap)
    plt.colorbar(cmap=cmap)
    plt.savefig(local_filename, fig=fig, bbox_inches='tight',pad_inches = 0)

    return heatmap, local_filename, avg_img_size

@g.my_app.callback("build_heatmap")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def build_heatmap(api: sly.Api, task_id, context, state, app_logger):
    step_done = False
    g.api.app.set_field(task_id, "state.heatmapInProgress", True)
    filenames = []
    avg_img_size = None
    try:
        classes = state["selectedClasses"]
        for class_idx, class_name in enumerate(classes):
            heatmap, filename, avg_img_size = get_heatmap_image(api, state, class_name, class_idx, avg_img_size)
            file_info = api.file.upload(g.team_id, filename, filename)
            filenames.append({"class": class_name, "url": file_info.full_storage_url})
        step_done = True
    except Exception as e:
        step_done = False
        filenames = None
        raise e
    finally:
        fields = [
            {"field": "state.heatmapInProgress", "payload": False},
            {"field": f"data.done4", "payload": step_done},
            {"field": f"data.resultFilenames", "payload": filenames},
        ]
        if step_done is True:
            fields.extend([
                {"field": "state.collapsed5", "payload": False},
                {"field": "state.disabled5", "payload": False},
                {"field": "state.activeStep", "payload": 5},
            ])
        g.api.app.set_fields(g.task_id, fields)

