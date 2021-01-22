import requests
from numpy import ndarray, np
from PIL import Image

from ..lambda_function import SUFFIX


def read(dataset, version, implementation, x, y, z, **kwargs) -> ndarray:
    url = f"https://tiles{SUFFIX}.globalforestwatch.org/{dataset}/{version}/{implementation}/{z}/{x}/{y}.png"
    png = Image.open(requests.get(url, stream=True).raw)
    data = np.array(png)

    # convert data from (height, width, bands) to (bands, height, width)
    shape = data.shape
    return data.transpose((2, 1, 0)).reshape(shape[::-1])
