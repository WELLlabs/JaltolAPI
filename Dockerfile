# Use an official Python runtime as a parent image
FROM python:3.10

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /code

# Copy the current directory contents into the container at /code
COPY . /code/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80
# Run the Django development server
RUN python manage.py runserver 0.0.0.0:80 &

CMD bash