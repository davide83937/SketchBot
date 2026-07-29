from svgpathtools import svg2paths
import functionPoints as fp

from svgpathtools import svg2paths
import functionPoints as fp


def genera_traiettoria_svg(svg_file, z_disegno=0.022, z_sollevato=0.05):
  """Legge un file SVG e calcola i punti adattando la densità

  in base alla lunghezza reale di ogni singolo tratto.
  """
  paths, attributes = svg2paths(svg_file)

  if not paths:
    return []

  # 1. Calcolo del bounding box globale (usando un campionamento proporzionale alla lunghezza)
  all_points = []
  for path in paths:
    length = path.length()
    if length == 0:
      continue
    # Scegliamo un numero di punti proporzionale alla lunghezza del tratto (es. circa 1 punto ogni 0.5 mm)
    num_punti_temp = max(3, int(length * 200))
    for i in range(num_punti_temp):
      t = i / (num_punti_temp - 1) if num_punti_temp > 1 else 0.0
      all_points.append(path.point(t))

  if not all_points:
    return []

  min_x = min(p.real for p in all_points)
  max_x = max(p.real for p in all_points)
  min_y = min(p.imag for p in all_points)
  max_y = max(p.imag for p in all_points)

  traiettoria_completa = []

  for path in paths:
    length = path.length()
    if length == 0:
      continue

    # 🔥 CAMPIONAMENTO ADATTIVO:
    # Se il tratto è corto (es. occhio), avrà pochi punti. Se è lungo, ne avrà di più.
    # Modifica il fattore '150' se vuoi più o meno punti in totale.
    num_punti = max(3, int(length*2.5))
    divisore = float(num_punti - 1) if num_punti > 1 else 1.0

    path_punti = []
    for i in range(num_punti):
      t = i / divisore
      p_orig = path.point(t)
      p_trasf = fp.trasforma_punto(p_orig, min_x, max_x, min_y, max_y)
      path_punti.append((p_trasf.real, p_trasf.imag))

    if not path_punti:
      continue

    primo_x, primo_y = path_punti[0]
    ultimo_x, ultimo_y = path_punti[-1]

    azioni_path = []
    # 1. Spostamento in alto sopra l'inizio del tratto
    azioni_path.append((primo_x, primo_y, z_sollevato, "PENNA ALZATA"))
    # 2. Abbassamento della penna sullo stesso punto
    azioni_path.append((primo_x, primo_y, z_disegno, "PENNA GIÙ"))
    # 3. Tracciamento dei punti intermedi adattati
    for x, y in path_punti:
      azioni_path.append((x, y, z_disegno, "DISEGNO"))
    # 4. Sollevamento finale sull'ultimo punto del tratto
    azioni_path.append((ultimo_x, ultimo_y, z_sollevato, "PENNA ALZATA"))

    traiettoria_completa.append(azioni_path)

  return traiettoria_completa