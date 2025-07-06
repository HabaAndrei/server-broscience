# Use a lightweight Python 3.11 image
FROM python:3.13.2

# Set the working directory inside the container
WORKDIR /app

# Copy Pipenv dependency files
COPY Pipfile Pipfile.lock ./

# Install pipenv and install project dependencies in the virtual environment
RUN pip install --upgrade pip pipenv && \
    pipenv install --deploy --ignore-pipfile

# Copy the entire project into the container's working directory
COPY . .

# Expose the port your FastAPI app will run on
EXPOSE 8000

# Start the FastAPI app using uvicorn, through pipenv
CMD ["pipenv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]