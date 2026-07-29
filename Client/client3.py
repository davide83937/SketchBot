import requests
import serial
import time

# --- CONFIGURAZIONE SERIALE E SERVER ---
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200
URL_FASTAPI = "http://localhost:8000/compute"


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


def elabora_e_invia_punto(ser, x, y, z, pausa_tra_punti=0.08):
    """
    Invia un punto a FastAPI applicando un fattore correttivo sulla Z
    per compensare la flessione meccanica.
    """

    # 🎛️ FATTORE CORRETTIVO DI ALTEZZA (Z-COMPENSATION)
    # Calcoliamo la distanza sul piano (raggio o coordinata Y di allontanamento).
    # Più y è grande, più il braccio si allontana e tende ad alzarsi.
    # Modifica '0.1' o '0.05' per aumentare o diminuire la correzione.

    # Esempio 1: Correzione lineare basata su Y (più ti allontani, più abbassi la Z)
    correzione_z = y * 0.08  # Se Y=0.15, sottrae 0.012 metri (1.2 mm) alla Z

    # Esempio 2 (Alternativa): Correzione basata sulla distanza totale dal centro (ipotenusa)
    # distanza_centro = (x**2 + y**2)**0.5
    # correzione_z = distanza_centro * 0.05

    fattore_correzione = 0.05  # Prova a partire con un valore piccolo (es. 0.03 o 0.05)

    # Sottraiamo una quota proporzionale a Y
    z_corretta = z - (y * fattore_correzione)

    # Inviamo la Z corretta al server invece di quella originale
    payload = {"x": x, "y": y, "z": z_corretta}

    try:
        response = requests.post(URL_FASTAPI, json=payload)
        if response.status_code == 200:
            res_json = response.json()
            r = res_json.get("output", None)

            if r:
                # Correzioni di calibrazione
                r[0] = -(r[0] - 100) + 10
                # r[1] = 93 - r[1]
                # r[2] = 75 - r[2]
                # r[3] = 171 - r[3]

                stringa_da_inviare = f"{r[0]:.2f},{r[1]:.2f},{r[2]:.2f},{r[3]:.2f}\n"
                ser.write(stringa_da_inviare.encode('utf-8'))
                print(
                    f"-> Target originale [Y:{y:.3f}, Z:{z:.3f}] | Corretto Z:{z_corretta:.3f} | Angoli: {stringa_da_inviare.strip()}")

                time.sleep(pausa_tra_punti)
                return True
            else:
                print(f"⚠️ Nessun angolo valido per il punto: X={x}, Y={y}, Z={z_corretta}")
                return False
        else:
            print(f"❌ Errore HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Connessione con il server persa durante l'invio.")
        return False


def genera_quadrato_da_punto(start_x, start_y, z_fissa, lato=0.04, risoluzione=10):
    punti = []
    x_min, y_min = start_x, start_y
    x_max, y_max = start_x + lato, start_y + lato

    def crea_linea(x_start, y_start, x_end, y_end, steps):
        linea = []
        for i in range(steps + 1):
            t = i / float(steps)
            x = x_start + t * (x_end - x_start)
            y = y_start + t * (y_end - y_start)
            linea.append((x, y, z_fissa))
        return linea

    # Tracciamento in senso orario
    punti.extend(crea_linea(x_min, y_min, x_min, y_max, risoluzione))
    punti.extend(crea_linea(x_min, y_max, x_max, y_max, risoluzione))
    punti.extend(crea_linea(x_max, y_max, x_max, y_min, risoluzione))
    punti.extend(crea_linea(x_max, y_min, x_min, y_min, risoluzione))

    return punti


# --- PROGRAMMA PRINCIPALE ---
if __name__ == "__main__":
    ser = apri_connessioni()

    ultimo_x = 0.0
    ultimo_y = 0.18
    ultimo_z = 0.05

    try:
        print("==================================================")
        print("MODO 1: CALIBRAZIONE MANUALE")
        print("Digita 'q' quando sei pronto per far partire il disegno.")
        print("==================================================")

        while True:
            in_x = input("\nInserisci x (o 'q' per disegnare): ")
            if in_x.lower() == 'q':
                break

            in_y = input("Inserisci y: ")
            in_z = input("Inserisci z: ")

            try:
                x = float(in_x)
                y = float(in_y)
                z = float(in_z)

                # Durante la calibrazione usiamo una pausa minima (es. 0.05s)
                successo = elabora_e_invia_punto(ser, x, y, z, pausa_tra_punti=0.05)
                if successo:
                    ultimo_x, ultimo_y, ultimo_z = x, y, z
                    print(f"🎯 Punto di riferimento aggiornato a: X={x}, Y={y}, Z={z}")
            except ValueError:
                print("❌ Inserisci un valore numerico valido.")

        print("\n==================================================")
        print("MODO 2: ESECUZIONE TRAIETTORIA (DISEGNO QUADRATO)")
        print(f"Partenza dall'ultimo punto: X={ultimo_x}, Y={ultimo_y}, Z={ultimo_z}")
        print("==================================================")

        dimensione_lato = 0.03
        punti_per_lato = 15

        # ⚙️ IMPOSTA QUI LA PAUSA (in secondi) TRA UN PUNTO E L'ALTRO DEL DISEGNO
        # Aumentala (es. 0.15 o 0.2) se il braccio è troppo scattoso o pesante.
        # Diminuiscala (es. 0.05) se vuoi che vada più veloce.
        TEMPO_DI_PAUSA = 0.5

        print(f"Generazione quadrato (lato {dimensione_lato * 100} cm) a Z={ultimo_z}...")
        traiettoria = genera_quadrato_da_punto(ultimo_x, ultimo_y, ultimo_z, dimensione_lato, punti_per_lato)

        print(f"Totale punti da tracciare: {len(traiettoria)}")
        input("Premi INVIO per far partire il braccio robotico...")

        for i, punto in enumerate(traiettoria):
            print(
                f"[{i + 1}/{len(traiettoria)}] Tracciamento -> X: {punto[0]:.3f}, Y: {punto[1]:.3f}, Z: {punto[2]:.3f}")

            # Inviamo il punto applicando la pausa stabilita per il disegno
            successo = elabora_e_invia_punto(ser, punto[0], punto[1], punto[2], pausa_tra_punti=TEMPO_DI_PAUSA)
            if not successo:
                print("⚠️ Attenzione: punto scartato o non raggiungibile.")

        print("\n✅ Traiettoria completata con successo!")

    except KeyboardInterrupt:
        print("\n\n⏹️ Interruzione manuale da tastiera.")

    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("✅ Porta seriale chiusa correttamente.")