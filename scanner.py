import cv2
from pyzbar.pyzbar import decode
import numpy as np

def decode_barcode(frame):
    """
    Decodes barcodes from a frame.
    Returns the barcode data and type if found, else None.
    """
    decoded_objects = decode(frame)
    for obj in decoded_objects:
        barcode_data = obj.data.decode('utf-8')
        barcode_type = obj.type
        
        # Draw rectangle around barcode (optional, for visualization if returning frame)
        # points = obj.polygon
        # if len(points) > 4:
        #     hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
        #     hull = list(map(tuple, np.squeeze(hull)))
        # else:
        #     hull = points
        # n = len(hull)
        # for j in range(0, n):
        #     cv2.line(frame, hull[j], hull[(j + 1) % n], (0, 255, 0), 3)

        return barcode_data, barcode_type
    
    return None, None
