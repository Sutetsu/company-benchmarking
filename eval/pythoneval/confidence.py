import math
import numpy as np

def confidence_value(data, confidence=0.95):

    z = None
    if confidence == 0.95:
        z = 1.96
    elif confidence == 0.99:
        z = 2.58
    else:
        raise ValueError("Unknown Z value for confidence %f" %confidence)

    std = np.std(data)
    n = len(data)

    return z * std / math.sqrt(n)
