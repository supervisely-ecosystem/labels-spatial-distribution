import sly_globals as g


def init(data, state):
    data["projectId"] = g.project_info.id
    data["projectName"] = g.project_info.name
    data["projectImagesCount"] = g.project_info.items_count
    data["projectPreviewUrl"] = g.api.image.preview_url(g.project_info.reference_image_url, 100, 100)
    data["done1"] = True
    state["collapsed1"] = False
