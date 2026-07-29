import time
import connection as p
import functionPoints as fpt
import svgElaborator as svge

# --- CONFIGURAZIONE ---
SERIAL_PORT = "COM4"
BAUD_RATE = 115200
SVG_FILE = "cat.svg"  # Cambia qui il nome del file SVG quando vuoi

if __name__ == "__main__":
  ser = p.apri_connessioni()

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
      if in_x.lower() == "q":
        break

      in_y = input("Inserisci y: ")
      in_z = input("Inserisci z: ")

      try:
        x = float(in_x)
        y = float(in_y)
        z = float(in_z)

        successo = fpt.elabora_e_invia_punto(
            ser, x, y, z, pausa_tra_punti=0.05
        )
        if successo:
          ultimo_x, ultimo_y, ultimo_z = x, y, z
          print(f"🎯 Punto di riferimento aggiornato a: X={x}, Y={y}, Z={z}")
      except ValueError:
        print("❌ Inserisci un valore numerico valido.")

    print("\n==================================================")
    print(f"MODO 2: ESECUZIONE TRAIETTORIA DA FILE SVG ({SVG_FILE})")
    print("==================================================")

    # Genera la traiettoria strutturata richiamando la funzione nel modulo esterno
    tratti_svg = svge.genera_traiettoria_svg(SVG_FILE, ultimo_z, ultimo_z+0.02)

    if not tratti_svg:
      print("❌ Errore: Nessun tratto trovato nell'SVG.")
      exit()

    print(f"Totale tratti (path) da tracciare: {len(tratti_svg)}")
    input("Premi INVIO per far partire il braccio robotico...")

    TEMPO_DI_PAUSA = 0.7  # Regola la velocità di esecuzione

    for path_idx, tratto in enumerate(tratti_svg):
      print(f"\n--- Tracciamento Tratto {path_idx + 1}/{len(tratti_svg)} ---")

      for x, y, z, stato in tratto:
        print(f"[{stato}] -> X: {x:.3f}, Y: {y:.3f}, Z: {z:.3f}")
        successo = fpt.elabora_e_invia_punto(
            ser, x, y, z, pausa_tra_punti=TEMPO_DI_PAUSA
        )
        if not successo:
          print("⚠️ Attenzione: punto scartato o non raggiungibile.")

    print("\n✅ Traiettoria SVG completata con successo!")

  except KeyboardInterrupt:
    print("\n\n⏹️ Interruzione manuale da tastiera.")

  finally:
    if "ser" in locals() and ser.is_open:
      ser.close()
      print("✅ Porta seriale chiusa correttamente.")