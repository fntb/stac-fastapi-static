from typing import Optional
import tempfile
import uuid
from os import path

import numpy as np
import matplotlib
import matplotlib.colors
import matplotlib.pyplot

from .brownian_surface import brownian_surface


def generate_heightmap_image(dir: Optional[str] = None):
    if not dir:
        dir = tempfile.mkdtemp()

    file = path.join(dir, uuid.uuid4().hex + ".png")

    field = brownian_surface()

    norm_field = 16000 * (field - np.min(field)) / \
        (np.max(field) - np.min(field)) - 8000

    newcolors = matplotlib.colormaps.get_cmap(
        'gist_earth')(np.linspace(0, 1, 256))
    newcolors[:128, :] = np.array([23/256, 28/256, 92/256, 1])

    cmap = matplotlib.colors.ListedColormap(newcolors)

    matplotlib.pyplot.imsave(file, norm_field, cmap=cmap)

    return file
