ARG BASE_IMAGE=python:3.10
FROM ${BASE_IMAGE}

# System dependencies are already installed in the base image

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH=$PATH:/usr/local/bin

# Add user
RUN useradd -m -s /bin/bash appuser
USER appuser

# Install ChromeDriver for user
RUN python -c 'from webdriver_manager.chrome import ChromeDriverManager;ChromeDriverManager().install()'
RUN chmod u+rwx /home/appuser/.wdm/drivers/chromedriver/linux64/136.0.7103.94/chromedriver-linux64/chromedriver

# Run the email checker
CMD ["python", "main.py"]
