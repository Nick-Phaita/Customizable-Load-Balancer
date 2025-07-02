# 1️⃣ Use a slim base image
FROM python:3.12-slim

# 2️⃣ Install Flask
COPY requirements.txt .
RUN pip install -r requirements.txt

# 3️⃣ Copy source
COPY app.py .

# 4️⃣ Set default env vars (can be overridden at runtime)
ENV PORT=5000 SERVER_ID=0

# 5️⃣ Expose port required by the assignment
EXPOSE 5000

# 6️⃣ Start the server
CMD ["python", "app.py"]
