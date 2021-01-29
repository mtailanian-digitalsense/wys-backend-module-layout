import random

def layout(data):
    workspaces = data['workspaces']
    layout_data = []
    for space in workspaces:
        for i in range(space['quantity']):
            s = {
                'space_id': space['id'],
                'position_x': round(random.uniform(0, 500), 4),
                'position_y': round(random.uniform(0, 600), 4),
                'rotation': None,
            }
            layout_data.append(s)
    return layout_data