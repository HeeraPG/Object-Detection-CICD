
import socket
import time
import cv2
import numpy as np
from datetime import datetime
import os 
os.system("pip install ultralytics")
from ultralytics import YOLO

# Ensure necessary directories exist
os.makedirs("/output", exist_ok=True)

# File Paths
received_image_path = "/output/received_data.jpg"

def get_container_ip():
    """Get the IP address of the Docker container."""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except Exception as e:
        return f"Error: {e}"

def receive_data(conn, save_path):
    """Receive image data from the client and save it."""
    try:
        size = conn.recv(8)
        size = int.from_bytes(size, byteorder='big')

        with open(save_path, 'wb') as f:
            received = 0
            while received < size:
                data = conn.recv(4096)
                if not data:
                    break
                f.write(data)
                received += len(data)

        print(f"Image received and saved at {save_path}")
    except Exception as e:
        print(f"Error receiving data: {e}")

def send_string(conn, string):
    """Send string data to the client."""
    try:
        size = len(string)
        conn.sendall(size.to_bytes(8, byteorder='big'))
        conn.sendall(string.encode())
        print("Data sent back to client")
    except Exception as e:
        print(f"Error sending data: {e}")

def process_vehicle_detection(image, model, confidence_score=0.5):
    """Perform vehicle detection on the received image."""
    results = model(image)
    detection_results = []

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            if confidence > confidence_score:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detection_info = {
                    'class_id': class_id,
                    'confidence': confidence,
                    'bbox': (x1, y1, x2, y2)
                }
                detection_results.append(detection_info)

    return detection_results

def detection_results_to_string(detection_results): 
    """Convert detection results into a readable string format."""
    return "\n".join(
        f"Class ID: {res['class_id']}, Confidence: {res['confidence']:.2f}, BBox: {res['bbox']}"
        for res in detection_results
    )

def main():
    """Main server function to handle incoming connections."""
    host = get_container_ip()
    port = 51821
    connected = False

    # Load YOLOv8 model
    model = YOLO("/app/yolov8n.pt")  # Ensure the model exists in the container

    while True:
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, port))
            server_socket.listen(5)
            print(f"Server listening on {host}:{port}")
            
            conn, addr = server_socket.accept()
            print(f"Connected by {addr}")
            connected = True
        except socket.error as e:
            print(f"Socket error: {e}")
            time.sleep(2)
            continue

        try:
            while connected:
                print("Receiving new image data...")
                receive_data(conn, received_image_path)

                original_image = cv2.imread(received_image_path)
                if original_image is None:
                    print("Error: Image not loaded correctly")
                    continue

                start_time = time.time_ns()
                detection_results = process_vehicle_detection(original_image, model)
                processing_time = (time.time_ns() - start_time)

                print(f"Processing time: {processing_time} ns")
                conn.sendall(processing_time.to_bytes(8, byteorder='big'))

                # Send detection results
                send_string(conn, detection_results_to_string(detection_results))

                rcv_message = conn.recv(1024).decode()
                if rcv_message == "STOP":
                    print("Connection closing...")
                    break
        except socket.error as e:
            print(f"Connection lost: {e}")
        finally:
            conn.close()
            connected = False
            time.sleep(1)

if __name__ == "__main__":
    main()
