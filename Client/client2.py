import requests
import serial  # <-- Importa pyserial
import time
import threading

# --- CONFIGURAZIONE SERIALE ---
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200

# Variabili globali per condividere i dati con il Thread
ultimo_comando = None
lock = threading.Lock()  # Per evitare conflitti di lettura/scrittura tra thread
running = True

"""
try:
    print(f"Apertura porta seriale {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(1)
except serial.SerialException as e:
    print(f"❌ Errore nell'apertura della porta seriale: {e}")
    exit()
"""


# --- THREAD DEDICATO ALL'INVIO CONTINUO (Alta frequenza verso STM32) ---
def thread_invio_continuo():
    """Questo thread invia continuamente l'ultimo comando salvato sulla seriale."""
    global ultimo_comando, running

    frequenza_invio = 0.02  # 50 Hz (invio ogni 20ms)

    while running:
        with lock:
            comando = ultimo_comando

        if comando is not None:
            # Se la Seriale è attiva, invia ripetutamente i byte
            if 'ser' in locals() and ser.is_open:
                ser.write(comando.encode('utf-8'))

        time.sleep(frequenza_invio)


# Avviamo il thread in background
t = threading.Thread(target=thread_invio_continuo, daemon=True)
t.start()

# --- RICHIESTA FASTAPI E INPUT UTENTE ---
url = "http://localhost:8000/compute"

try:
    while True:
        try:
            x = float(input("\nInserisci x: "))
            y = float(input("\nInserisci y: "))
            z = float(input("\nInserisci z: "))
        except ValueError:
            print("❌ Valore non valido. Inserisci numeri decimali.")
            continue

        payload = {"x": x, "y": y, "z": z}

        print(f"\n🚀 Avvio invio richieste POST a {url} (5 volte/sec per 10 secondi)...")

        # --- CICLO DI 10 SECONDI A 5 HZ (5 richieste/sec) ---
        durata = 10.0      # 10 secondi totali
        intervallo = 0.2    # 1/5 = 0.2 secondi tra le richieste
        start_time = time.time()

        while time.time() - start_time < durata:
            loop_start = time.time()

            try:
                response = requests.post(url, json=payload)

                if response.status_code == 200:
                    r = response.json().get("output")

                    if r:
                        stringa_da_inviare_base = f"{r[0]:.2f},{r[1]:.2f},{r[2]:.2f},{r[3]:.2f}\n"
                        # Correzione e offset angoli
                        r[0] = -(r[0] - 100) + 10
                        #r[1] = 93 - r[1]
                        #r[2] = 75 - r[2]
                        #r[3] = 171 - r[3]

                        stringa_da_inviare = f"{r[0]:.2f},{r[1]:.2f},{r[2]:.2f},{r[3]:.2f}\n"

                        # Aggiorniamo la variabile globale condivisa col thread
                        with lock:
                            ultimo_comando = stringa_da_inviare

                        tempo_trascorso = time.time() - start_time
                        print(f"[{tempo_trascorso:.1f}s] ✅ Risposta ricevuta base -> Target: {stringa_da_inviare_base.strip()}")
                        print(f"[{tempo_trascorso:.1f}s] ✅ Risposta ricevuta -> Target: {stringa_da_inviare.strip()}")

                    else:
                        print("⚠️ Nessun angolo restituito dal server.")

                else:
                    print(f"❌ Errore HTTP {response.status_code}: {response.text}")

            except requests.exceptions.ConnectionError:
                print("❌ Impossibile connettersi al server FastAPI.")

            # Calcolo pausa per mantenere la frequenza esatta di 5 Hz (0.2s)
            elapsed = time.time() - loop_start
            time_to_sleep = max(0.0, intervallo - elapsed)
            time.sleep(time_to_sleep)

        print("\n🏁 Finito il blocco di invio di 10 secondi.")

except KeyboardInterrupt:
    print("\n\n⏹️ Uscita richiesta dall'utente...")

finally:
    running = False  # Ferma il thread
    print("Chiusura della porta seriale...")
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("✅ Porta seriale chiusa correttamente.")

#x
#0
#0.04
#0.002
#0.015
