import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR
import numpy as np
import requests
import cvzone

# Initialize PaddleOCR
ocr = PaddleOCR()

# Initialize video capture
cap = cv2.VideoCapture('ADD PATH TO YOUR VIDEO SAMPLE HERE')

# Load YOLOv8 model
model = YOLO(r'license_plate_detector.pt')  # Update with your model's path

# Define area for polygon detection
area = [(5, 180), (3, 249), (984, 237), (950, 168)]

# Read class names (if applicable to your YOLOv8 model)
class_names = None  # YOLOv8 may not require this explicitly
try:
    with open("coco1.txt", "r") as f:
        class_names = f.read().splitlines()
except FileNotFoundError:
    print("Class names file not found. Ensure class names are correctly loaded.")

# Function to perform OCR on an image array
def perform_ocr(image_array):
    if image_array is None:
        raise ValueError("Image is None")
    
    # Perform OCR on the image array
    results = ocr.ocr(image_array, rec=True)  # rec=True enables text recognition
    detected_text = []
    
    # Process OCR results
    if results[0] is not None:
        for result in results[0]:
            text = result[1][0]
            detected_text.append(text)
    
    # Join all detected texts into a single string
    return ''.join(detected_text)

# Initialize tracking variables
counter = []
FASTAPI_URL = "http://127.0.0.1:8000/store_plate/"  # FastAPI endpoint

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (1020, 500))

    # Run YOLOv8 inference on the frame
    results = model(frame)

    for result in results:  # Iterate through detected results
        boxes = result.boxes.xyxy.cpu().numpy()  # Bounding boxes
        class_ids = result.boxes.cls.cpu().numpy()  # Class IDs
        confidences = result.boxes.conf.cpu().numpy()  # Confidence scores

        for box, class_id, conf in zip(boxes, class_ids, confidences):
            x1, y1, x2, y2 = map(int, box)
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            # Check if center point is within the defined area
            result = cv2.pointPolygonTest(np.array(area, np.int32), (cx, cy), False)
            if result >= 0:
                crop = frame[y1:y2, x1:x2]
                crop = cv2.resize(crop, (120, 70))
                
                text = perform_ocr(crop)
                text = text.replace('(', '').replace(')', '').replace(',', '').replace(']', '').replace('-', ' ')
                
                # Avoid duplicate entries by checking unique counter
                if text not in counter:
                    counter.append(text)
                    
                    # Send detected number plate to FastAPI server
                    try:
                        response = requests.post(FASTAPI_URL, json={"plate": text})
                        print("Server response:", response.json())
                    except Exception as e:
                        print("Error sending data to FastAPI server:", e)

    # Display the current count
    mycounter = len(counter)
    cvzone.putTextRect(frame, f'{mycounter}', (50, 60), 1, 1)
    cv2.polylines(frame, [np.array(area, np.int32)], True, (255, 0, 0), 2)
    cv2.imshow("RGB", frame)

    # Break loop on 'Esc' key
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Close video capture and cleanup
cap.release()
cv2.destroyAllWindows()
