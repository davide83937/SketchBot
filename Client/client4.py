import requests
import serial
import time
from svgpathtools import svg2paths

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


def elabora_e_invia_punto(ser, x, y, z, pausa_tra_punti=0.08, is_drawing=False):
    """
    Invia un punto a FastAPI.
    - Se is_drawing=False: applica le formule originali di calibrazione.
    - Se is_drawing=True: applica la compensazione Z, -100 agli angoli e +70 alla base.
    """
    if is_drawing:
        # Compensazione Z attiva solo in fase di disegno
        fattore_correzione = 0.05
        z_corretta = z - (y * fattore_correzione)
    else:
        z_corretta = z

    payload = {"x": x, "y": y, "z": z_corretta}

    try:
        response = requests.post(URL_FASTAPI, json=payload)
        if response.status_code == 200:
            res_json = response.json()
            r = res_json.get("output", None)

            if r:
                if is_drawing:
                    # ⚙️ REGOLE PER IL DISEGNO SVG (-100 su tutti e +70 sulla base)
                    r[0] = -(r[0] - 100) + 50
                    r[1] = r[1]
                    r[2] = r[2]
                    r[3] = r[3]
                    modalita_str = "DISEGNO SVG"
                else:
                    # 🎛️ REGOLE ORIGINALI PER LA CALIBRAZIONE MANUALE
                    r[0] = -(r[0] - 100) + 10
                    # r[1] = 93 - r[1]
                    # r[2] = 75 - r[2]
                    # r[3] = 171 - r[3]
                    modalita_str = "CALIBRAZIONE"

                stringa_da_inviare = f"{r[0]:.2f},{r[1]:.2f},{r[2]:.2f},{r[3]:.2f}\n"
                ser.write(stringa_da_inviare.encode('utf-8'))
                print(
                    f"-> [{modalita_str}] Target [X:{x:.3f}, Y:{y:.3f}, Z:{z_corretta:.3f}] | Angoli: {stringa_da_inviare.strip()}")

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


def carica_percorsi_da_svg(file_path, cx, cy, scala_x=1.0, scala_y=1.0, z_disegno=0.05, z_alzo=0.075, densita_punti=15):
    try:
        paths, attributes = svg2paths(file_path)
    except Exception as e:
        print(f"❌ Errore nella lettura del file SVG: {e}")
        return []

    if not paths:
        print("⚠️ Nessun percorso trovato nel file SVG.")
        return []

    xmin, xmax, ymin, ymax = paths[0].bbox()
    for path in paths[1:]:
        p_xmin, p_xmax, p_ymin, p_ymax = path.bbox()
        xmin = min(xmin, p_xmin)
        xmax = max(xmax, p_xmax)
        ymin = min(ymin, p_ymin)
        ymax = max(ymax, p_ymax)

    svg_cx = (xmin + xmax) / 2.0
    svg_cy = (ymin + ymax) / 2.0

    tratti_totali = []

    for path in paths:
        tratto_corrente = []
        num_campioni = int(path.length() * densita_punti) + 5

        for i in range(num_campioni + 1):
            t = i / float(num_campioni)
            punto_complesso = path.point(t)

            x = cx + ((punto_complesso.real - svg_cx) * scala_x)
            y = cy - ((punto_complesso.imag - svg_cy) * scala_y)

            tratto_corrente.append((x, y, z_disegno))

        if tratto_corrente:
            punto_inizio = tratto_corrente[0]
            punto_fine = tratto_corrente[-1]

            tratto_con_alzo = [
                (punto_inizio[0], punto_inizio[1], z_alzo),
                *tratto_corrente,
                (punto_fine[0], punto_fine[1], z_alzo)
            ]
            tratti_totali.append(tratto_con_alzo)

    return tratti_totali


def genera_linea_interpolata(x1, y1, z1, x2, y2, z2, risoluzione=12):
    linea = []
    if x1 == x2 and y1 == y2 and z1 == z2:
        return [(x1, y1, z1)]

    for i in range(risoluzione + 1):
        t = i / float(risoluzione)
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        z = z1 + t * (z2 - z1)
        linea.append((x, y, z))
    return linea


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

                # is_drawing=False: usa la calibrazione originale pura
                successo = elabora_e_invia_punto(ser, x, y, z, pausa_tra_punti=0.05, is_drawing=False)
                if successo:
                    ultimo_x, ultimo_y, ultimo_z = x, y, z
                    print(f"🎯 Punto di riferimento aggiornato a: X={x}, Y={y}, Z={z}")
            except ValueError:
                print("❌ Inserisci un valore numerico valido.")

        print("\n==================================================")
        print("MODO 2: ESECUZIONE DISEGNO DA FILE SVG")
        print(f"Partenza dall'ultimo punto: X={ultimo_x}, Y={ultimo_y}, Z={ultimo_z}")
        print("==================================================")

        Z_DISEGNO = ultimo_z
        Z_ALZO = ultimo_z + 0.025
        TEMPO_DI_PAUSA = 0.5

        file_svg = "cat.svg"

        print(f"Caricamento e centratura automatica del file SVG: {file_svg}...")

        raw_schema = carica_percorsi_da_svg(
            file_path=file_svg,
            cx=ultimo_x,
            cy=ultimo_y,
            scala_x=0.028,
            scala_y=0.028,
            z_disegno=Z_DISEGNO,
            z_alzo=Z_ALZO,
            densita_punti=15
        )

        schema_gatto = []
        for tratto in raw_schema:
            tratto_interpolato = []
            for i in range(len(tratto) - 1):
                p1 = tratto[i]
                p2 = tratto[i + 1]
                if p1[2] != p2[2]:
                    tratto_interpolato.append(p1)
                else:
                    segmento = genera_linea_interpolata(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2], risoluzione=10)
                    if i > 0 and segmento:
                        segmento = segmento[1:]
                    tratto_interpolato.extend(segmento)
            if tratto_interpolato:
                schema_gatto.append(tratto_interpolato)

        print(f"Totale tratti vettoriali pronti: {len(schema_gatto)}")
        input("Premi INVIO per far partire il braccio robotico...")

        for num_tratto, tratto in enumerate(schema_gatto):
            print(f"\n--- Esecuzione Tratto {num_tratto + 1}/{len(schema_gatto)} ({len(tratto)} punti) ---")

            for punto in tratto:
                x_p, y_p, z_p = punto[0], punto[1], punto[2]
                # is_drawing=True: attiva compensazione Z, -100 sugli angoli e +70 sulla base
                successo = elabora_e_invia_punto(ser, x_p, y_p, z_p, pausa_tra_punti=TEMPO_DI_PAUSA, is_drawing=True)
                if not successo:
                    print("⚠️ Attenzione: punto scartato o non raggiungibile.")

        print("\n✅ Disegno SVG completato con successo!")

    except KeyboardInterrupt:
        print("\n\n⏹️ Interruzione manuale da tastiera.")

    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("✅ Porta seriale chiusa correttamente.")