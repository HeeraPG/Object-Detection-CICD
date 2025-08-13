# Base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY yolov8n.pt /app 
COPY server_w_time_object_detector_simplified.py /app

# Installiere systemweite Abh�ngigkeiten 
RUN apt-get update && apt-get install --no-install-recommends -y \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*


# Install any needed packages specified in requirements.txt
RUN pip install numpy==2.2.0 && \ 
pip install opencv-python-headless

# Clean up 
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Make port 51820 available to the world outside this container
EXPOSE 51821

# Define environment variable
ENV NAME=World

# Run app.py when the container launches
CMD ["python", "server_w_time_object_detector_simplified.py"]
