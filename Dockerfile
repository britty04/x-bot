FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Run the bot
CMD ["python", "bot.py"]
