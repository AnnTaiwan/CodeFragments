# 1. Use an official Python base image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy only the requirements first (optimizes Docker layer caching)
COPY requirements.txt .

# 4. Install dependencies when building the image
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your project code
COPY . .

# 6. Expose port 5000 for Flask web server
EXPOSE 5000

# 7. Run Flask web application by default
CMD ["python", "src/yt_download_flask.py"]