import matplotlib.pyplot as plt
import svgElaborator as svg_elab

# Nome del file SVG da testare
SVG_FILE = "cat.svg"

# Genera la traiettoria usando la stessa logica del robot
tratti_svg = svg_elab.genera_traiettoria_svg(SVG_FILE)

if not tratti_svg:
  print("❌ Nessun tratto trovato.")
  exit()

# Configurazione del grafico di anteprima (finestra più larga e spaziosa)
fig, ax = plt.subplots(figsize=(10, 8))

# Scansiona tutti i tratti e tracciali a schermo
for tratto in tratti_svg:
  # Filtriamo solo i punti di disegno (ignorando i sollevamenti penna per pulizia visiva)
  x_vals = [punto[0] for punto in tratto if punto[3] == "DISEGNO"]
  y_vals = [punto[1] for punto in tratto if punto[3] == "DISEGNO"]

  if x_vals and y_vals:
    # Disegna la linea continua del tratto
    ax.plot(
        x_vals, y_vals, marker="o", markersize=3, color="blue", linewidth=1.5
    )

# Impostazioni grafiche con visualizzazione più larga
ax.set_xlim(-0.05, 0.05)  # Area X allargata (da -5 cm a +5 cm)
ax.set_ylim(0.14, 0.26)  # Area Y allargata (da 14 cm a 26 cm)
ax.set_aspect("equal")  # Mantiene le proporzioni reali (evita distorsioni)
ax.invert_yaxis()  # Adatta il sistema di riferimento cartesiano allo spazio del braccio
ax.grid(True, linestyle="--", alpha=0.6)
ax.set_title(f"Anteprima Traiettoria SVG: {SVG_FILE}")
ax.set_xlabel("Asse X (metri)")
ax.set_ylabel("Asse Y (metri)")

print(f"📊 Visualizzazione anteprima di {len(tratti_svg)} tratti...")
plt.show()