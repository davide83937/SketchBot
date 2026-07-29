import requests
import time
URL_FASTAPI = "http://localhost:8000/compute"

def elabora_e_invia_punto(
    ser, x, y, z, pausa_tra_punti=0.5, applica_correzione=False
):
  """Invia un punto al server.

  Se applica_correzione=False (default), usa ESATTAMENTE le coordinate originali
  (fondamentale per la calibrazione manuale).
  """

  if applica_correzione:
    # Eventuale formula di correzione (attiva solo se esplicitamente richiesta)
    fattore_correzione = 0.13
    z_effettiva = z - (y * fattore_correzione)
  else:
    # In calibrazione o per default usiamo la Z pulita che hai digitato
    z_effettiva = z

  payload = {"x": x, "y": y, "z": z_effettiva}

  try:
    response = requests.post(URL_FASTAPI, json=payload)
    if response.status_code == 200:
      res_json = response.json()
      r = res_json.get("output", None)

      if r:
        # Correzioni di calibrazione dei motori
        r[0] = -(r[0] - 100) + 10
        # r[1] = 93 - r[1]
        # r[2] = 75 - r[2]
        # r[3] = 171 - r[3]

        stringa_da_inviare = f"{r[0]:.2f},{r[1]:.2f},{r[2]:.2f},{r[3]:.2f}\n"
        ser.write(stringa_da_inviare.encode("utf-8"))
        print(
            f"-> Target [X:{x:.3f}, Y:{y:.3f}, Z:{z_effettiva:.3f}] | Angoli:"
            f" {stringa_da_inviare.strip()}"
        )

        time.sleep(pausa_tra_punti)
        return True
      else:
        print(
            f"⚠️ Nessun angolo valido per il punto: X={x}, Y={y},"
            f" Z={z_effettiva}"
        )
        return False
    else:
      print(f"❌ Errore HTTP {response.status_code}: {response.text}")
      return False
  except requests.exceptions.ConnectionError:
    print("❌ Connessione con il server persa durante l'invio.")
    return False

def trasforma_punto(
    p, min_x, max_x, min_y, max_y, target_min_x=-0.05, target_max_x=0.05, target_min_y=0.15, target_max_y=0.25
):
  """Trasforma un punto (complesso o (x,y)) mappandolo nel nuovo intervallo

  mantenendo le proporzioni (aspect ratio).
  """
  # Supporta sia il formato complesso di svgpathtools che una tupla/lista (x, y)
  if isinstance(p, complex):
    x, y = p.real, p.imag
    is_complex = True
  else:
    x, y = p[0], p[1]
    is_complex = False

  # Span originali
  span_x = max_x - min_x if max_x != min_x else 1.0
  span_y = max_y - min_y if max_y != min_y else 1.0

  # Span target
  target_span_x = target_max_x - target_min_x
  target_span_y = target_max_y - target_min_y

  # Fattore di scala uniforme per mantenere le proporzioni
  scale = min(target_span_x / span_x, target_span_y / span_y)

  # Normalizzazione e centraggio
  norm_x = (x - min_x) * scale
  norm_y = (y - min_y) * scale

  offset_x = target_min_x + (target_span_x - (span_x * scale)) / 2
  offset_y = target_min_y + (target_span_y - (span_y * scale)) / 2

  new_x = norm_x + offset_x
  new_y = norm_y + offset_y

  return complex(new_x, new_y) if is_complex else (new_x, new_y)