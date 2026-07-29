import requests
import serial  # <-- Importa pyserial
import time

# --- CONFIGURAZIONE SERIALE ---
# Modifica 'COM3' con la porta corretta del tuo STM32 (es. /dev/ttyACM0 su Linux/Mac)
# Assicurati che il baudrate (115200) sia lo stesso che usa lo STM32
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200

try:
    print(f"Apertura porta seriale {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(1)  # Piccola pausa per stabilizzare la connessione
except serial.SerialException as e:
    print(f"❌ Errore nell'apertura della porta seriale: {e}")
    print("Controlla che lo STM32 sia collegato e che la porta sia corretta.")
    exit()  # Esce dallo script se non trova il braccio robotico



# --- RICHIESTA FASTAPI ---
# URL dell'endpoint FastAPI esposto sulla porta 8000
url = "http://localhost:8000/compute"

# Coordinate cartesiane target X, Y, Z per il robot
payload = {
    "x": 0.05,
    "y": 0.15,
    "z": 0.05
}

try:
    while True:
        x = float(input("\nInserisci x: "))
        y = float(input("\nInserisci y: "))
        z = float(input("\nInserisci z: "))

        payload = {
            "x": x,
            "y": y,
            "z": z
        }

        print(f"\nInizio invio richiesta POST a {url}...")
        print(f"Coordinate target inviate: {payload}")

        try:
            response = requests.post(url, json=payload)

            if response.status_code == 200:
                print("\n✅ Risposta ricevuta dal server con successo!")

                r = response.json()
                r = r["output"]

                if r:
                    print("\nRisultato BASE (Angoli calcolati):")
                    print(f"Motore 0: {r[0]:.2f}")
                    print(f"Motore 1: {r[1]:.2f}")
                    print(f"Motore 2: {r[2]:.2f}")
                    print(f"Motore 3: {r[3]:.2f}")

                    # 1. Calcoli eventuali correzioni sugli angoli
                    r[0] = -(r[0] - 100) + 10
                    #r[1] = 93 - r[1]
                    # 3. GOMITO E POLSO: RIPRISTINIAMO LE SOTTRAZIONI ORIGINALI
                    #r[2] = 75 - r[2]
                    #r[3] = 171 - r[3]

                    # 4. 🔥 SALVAVITA ANTI-STALLO PER IL GOMITO
                    # Impediamo al motore fisico di scendere sotto i 10 gradi per evitare collisioni/blocchi


                    # 2. Stampi a schermo per debug
                    print("\nRisultato (Angoli calcolati):")
                    print(f"Motore 0: {r[0]:.2f}")
                    print(f"Motore 1: {r[1]:.2f}")
                    print(f"Motore 2: {r[2]:.2f}")
                    print(f"Motore 3: {r[3]:.2f}")

                    # 3. FORMATTI LA STRINGA E LA INVII ALLO STM32
                    stringa_da_inviare = f"{r[0]:.2f},{r[1]:.2f},{r[2]:.2f},{r[3]:.2f}\n"

                    print(f"\nInviando al braccio robotico: {stringa_da_inviare.strip()}")

                    # Invia i byte sulla seriale
                    ser.write(stringa_da_inviare.encode('utf-8'))


                else:
                    print("Risultato (Angoli calcolati): niente angoli")

            else:
                print(f"\n❌ Errore HTTP {response.status_code}:")
                print(response.text)

        except requests.exceptions.ConnectionError:
            print("\n❌ Errore: Impossibile connettersi al server su http://localhost:8000.")
            print("Verifica che Uvicorn sia in esecuzione dentro il container!")

except KeyboardInterrupt:
    # Questo intercetta la pressione di Ctrl+C per uscire in modo pulito
    print("\n\n⏹️ Uscita dal programma richiesta dall'utente...")

finally:
    # Questo finally ORA è fuori dal ciclo while.
    # Si attiva SOLO quando esci dal programma.
    print("Chiusura della porta seriale...")
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("✅ Porta seriale chiusa correttamente.")