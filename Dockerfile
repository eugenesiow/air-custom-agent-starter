# Use a slim Python base image for a smaller final image size
FROM python:3.12-slim-bookworm
# Set the working directory inside the container
WORKDIR /app
# Copy the rest of your application's code into the container
COPY . .
# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Expose the port that the application will run on
EXPOSE 7070
# The command to run the uvicorn server for your main.py file
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7070"]