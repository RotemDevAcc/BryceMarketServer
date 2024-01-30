# Use the official Python image as a parent image
FROM python:3.9-slim

# Set environment variables for Python and Django
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Expose the port that Gunicorn will listen on
EXPOSE 8000

# Define the command to start the Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "project.wsgi:application"]
