# Use an official Python runtime as the base image
FROM python:3.10

# Set the working directory in the container
WORKDIR /src

# Copy the application files into the container
COPY . .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your app runs on (adjust if needed)
EXPOSE 8501

# Define the command to run your app
CMD ["streamlit", "run orchestrator.py"]