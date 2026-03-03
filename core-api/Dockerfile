# Usa un'immagine Python ufficiale
FROM python:3.10-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i requisiti e installali
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il codice della cartella core-api
COPY . .

# Hugging Face Spaces usa la porta 7860 per impostazione predefinita
ENV PORT=7860

# Comando per avviare l'app
# Usiamo 0.0.0.0 per permettere connessioni esterne
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
