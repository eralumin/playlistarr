# Use a Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt if you have one, and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code to the container
COPY ./src /app/src

# Set the default command to run your script (adjust if necessary)
CMD ["python", "/app/src/your_scripts.py"]
