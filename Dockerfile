# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install necessary packages
RUN apt-get update && apt-get install -y wget unzip

# Install Chrome and Chromedriver
RUN wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y /tmp/google-chrome.deb \
    && CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1) \
    && CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}) \
    && wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/google-chrome.deb /tmp/chromedriver.zip \
    && echo "export CHROMEDRIVER_PATH=/usr/local/bin/chromedriver" >> /etc/profile

# Copy bot files into container
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Run the bot
CMD ["python", "bot.py"]
