import serial  # <-- Importa pyserial
import time
import requests

URL_FASTAPI = "http://localhost:8000/compute"
SERIAL_PORT = "COM4"
BAUD_RATE = 115200

def apri_connessioni():
    """Inizializza la seriale e verifica il server FastAPI."""
    try:
        print(f"Apertura porta seriale {SERIAL_PORT}...")
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(1)
    except serial.SerialException as e:
        print(f"❌ Errore nell'apertura della porta seriale: {e}")
        exit()

    try:
        requests.get(URL_FASTAPI.replace("/compute", ""))
    except requests.exceptions.ConnectionError:
        print(f"❌ Errore: Impossibile connettersi al server su {URL_FASTAPI}.")
        print("Verifica che Uvicorn sia in esecuzione!")
        ser.close()
        exit()

    print("✅ Connessioni stabilite con successo!\n")
    return ser
