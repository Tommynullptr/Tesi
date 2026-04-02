import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json

from scipy.stats import gaussian_kde


RESULTS_PATH = "Python/results/measures_batch/summary.csv"
RAW_RECORDS = "Python/results/measures_batch/raw_records.json"
PLOT_DIR = "Python/results/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# Carica il CSV unico e filtra per generatori usando label
if not os.path.exists(RESULTS_PATH):
    raise SystemExit(f"File mancante: {RESULTS_PATH}")

df_all = pd.read_csv(RESULTS_PATH)
generators = {
    "bsp": "bsp",
    "blind": "blind",
    "cellular": "cellular",
    "lookahead": "lookahead",
    "maze": "maze",
    "random": "random"
}

data = {}
for key, token in generators.items():
    sub = df_all[df_all["label"].str.contains(token, case=False, na=False)].copy()
    if not sub.empty:
        data[key] = sub
        print(f"✔ Caricato {key} ({len(sub)} mappe)")
    else:
        print(f"✘ Nessun record per {key}")

def save_plot(name):
    path = os.path.join(PLOT_DIR, name)
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"✔ Salvato: {path}")

# -------------------------
# Plot esistenti (invariati)
# -------------------------

# 1. SPEED: boxplot per fase raggruppato per generatore
def plot_speed(zoom_quantile=0.90, zoom_ylim=None):
    """
    Genera due plot:
    - speed_by_phase.png (grafico completo)
    - speed_by_phase_zoom.png (grafico separato con zoom sui valori piccoli)

    zoom_quantile: quantile usato per determinare il limite superiore dello zoom (default 0.90)
    zoom_ylim: se fornito (tuple: (ymin, ymax)) forza i limiti Y del plot zoomato
    """
    phases = ["dungeon_generation", "classify_cells", "terrain_generation", "objects_generation"]
    rows = []
    for gen, df in data.items():
        for p in phases:
            col = f"phase_{p}"
            if col in df.columns:
                for v in df[col].dropna():
                    rows.append({"generator": gen, "phase": p, "time": float(v)})
    if not rows:
        print("⚠ Nessun dato di timing disponibile")
        return
    df_long = pd.DataFrame(rows)

    # --- Plot completo ---
    plt.figure(figsize=(12,6))
    sns.barplot(x="phase", y="time", hue="generator", data=df_long)
    plt.title("Confronto tempi di generazione per fase")
    plt.ylabel("Tempo (s)")
    plt.xlabel("Fase")
    plt.legend(title="Generator", bbox_to_anchor=(1.02, 1), loc="upper left")
    save_plot("speed_by_phase.png")

    # --- Plot zoomato separato ---
    if zoom_ylim is None:
        try:
            upper = float(df_long["time"].quantile(zoom_quantile))
            if not np.isfinite(upper) or upper <= 0:
                upper = max(df_long["time"].median() * 1.5, 1.0)
        except Exception:
            upper = 1.5
        zoom_ymax = upper * 1.1
        zoom_ylim = (0, zoom_ymax)

    # medie esplicite con pandas (per generatore e fase)
    means = df_long.groupby(["generator", "phase"])["time"].mean().reset_index()
    means.to_csv("Python/results/measures_batch/phase_means_by_generator.csv", index=False)

    plt.figure(figsize=(12,6))
    sns.barplot(x="phase", y="time", hue="generator", data=df_long)
    plt.title("Confronto tempi di generazione per fase (zoom sui valori piccoli)")
    plt.ylabel("Tempo (s)")
    plt.xlabel("Fase")
    plt.ylim(zoom_ylim)
    plt.legend(title="Generator", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.axhline(zoom_ylim[1], color="gray", linestyle="--", linewidth=0.8)
    save_plot("speed_by_phase_zoom.png")


# 2. EXPRESSIVITY: scatter fv_floor_fraction vs fv_deadend_count
def plot_expressivity(f1, f2, zoom_x=2000, zoom_y=20):
    # --- Plot completo ---
    plt.figure(figsize=(10,6))
    any_plotted = False

    for gen, df in data.items():
        if f1 in df.columns and f2 in df.columns:
            plt.scatter(df[f1], df[f2], label=gen, alpha=0.6)
            any_plotted = True

    if not any_plotted:
        print(f"⚠ Nessun dato per {f1}, {f2}")
        return

    plt.xlabel(f1)
    plt.ylabel(f2)
    plt.title("Expressivity space")
    plt.legend()
    plt.grid(alpha=0.3)
    save_plot(f"expressivity_{f1}_{f2}.png")

    # --- Plot zoomato ---
    if zoom_x is None and zoom_y is None:
        return

    plt.figure(figsize=(10,6))
    any_zoom = False

    for gen, df in data.items():
        if f1 in df.columns and f2 in df.columns:
            x = df[f1]
            y = df[f2]

            mask = np.ones(len(x), dtype=bool)

            if zoom_x is not None:
                mask &= (x <= zoom_x)
            if zoom_y is not None:
                mask &= (y <= zoom_y)

            if not np.any(mask):
                continue

            plt.scatter(x[mask], y[mask], label=gen, alpha=0.6)
            any_zoom = True

    if not any_zoom:
        print(f"⚠ Nessun dato nello zoom per {f1}, {f2}")
        return

    if zoom_x is not None:
        plt.xlim(0, zoom_x)
    if zoom_y is not None:
        plt.ylim(0, zoom_y)

    plt.xlabel(f1)
    plt.ylabel(f2)
    plt.title(f"Expressivity space (zoom)")
    plt.legend()
    plt.grid(alpha=0.3)
    save_plot(f"expressivity_{f1}_{f2}_zoom.png")

# 3. DISTRIBUZIONI feature
def plot_feature_density_scatter(feature, bandwidth=None, scale=1.0, jitter=0.02):
    """
    Plot: X = feature, Y = density (punti).
    bandwidth: None (automatico) o float per la KDE.
    scale: moltiplicatore per la densità (adatta l'altezza dei punti).
    jitter: frazione della scala X per jitter orizzontale (opzionale).

    Produce:
      - dist_density_scatter_{feature}.png
      - dist_density_scatter_{feature}_zoom.png

    Nota: per lo zoom uso internamente `zoom_quantile` (default 0.90).
    """
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.stats import gaussian_kde

    # --- Plot principale (come nella tua versione originale) ---
    plt.figure(figsize=(12,6))
    any_plotted = False

    # raccolta valori per calcolo zoom
    all_vals_for_zoom = []

    for i, (gen, df) in enumerate(data.items()):
        if feature not in df.columns:
            continue
        vals = df[feature].dropna().values
        if vals.size == 0:
            continue

        # stima KDE sulla feature
        try:
            kde = gaussian_kde(vals, bw_method=bandwidth)
        except Exception:
            kde = None

        # per ogni sample calcola densità (o densità costante)
        if kde is not None:
            dens = kde(vals)
        else:
            dens = np.full_like(vals, fill_value=1.0, dtype=float)

        # scala densità per separare i generatori visivamente
        y = dens * scale

        # aggiungi un piccolo jitter verticale per evitare perfetta sovrapposizione
        y = y + (np.random.rand(len(y)) - 0.5) * (scale * 0.05)

        # opzionale: jitter orizzontale molto piccolo per evitare sovrapposizione esatta
        span = np.ptp(vals) if np.ptp(vals) > 0 else 1.0
        x = vals + (np.random.rand(len(vals)) - 0.5) * (jitter * span)

        plt.scatter(x, y, alpha=0.6, s=18, label=f"{gen} (n={len(vals)})")
        any_plotted = True

        # accumula valori per calcolo zoom
        all_vals_for_zoom.append(vals)

    if not any_plotted:
        print(f"⚠ Nessun dato per {feature}")
        return

    plt.xlabel(feature)
    plt.ylabel("Densità (punti ~ KDE)")
    plt.title(f"Distribuzione di {feature} (punti con densità su Y)")
    plt.legend(ncol=2, fontsize="small")
    plt.grid(alpha=0.2, axis="y")
    save_plot(f"dist_density_scatter_{feature}.png")

    # --- Plot separato: zoom sui valori piccoli (stile plot_speed) ---
    if len(all_vals_for_zoom) == 0:
        return

    all_vals_concat = np.concatenate(all_vals_for_zoom)
    # default: quantile usato per determinare limite superiore dello zoom
    zoom_quantile = 0.90  # cambia qui per meno/maggior zoom (es. 0.95, 0.99)
    try:
        upper = float(np.quantile(all_vals_concat, zoom_quantile))
        if not np.isfinite(upper) or upper <= 0:
            upper = max(np.median(all_vals_concat) * 1.5, 1.0)
    except Exception:
        upper = np.max(all_vals_concat) if len(all_vals_concat) > 0 else 1.0

    zoom_xmax = 1000  # piccolo margine come nel plot_speed

    # se zoom_xmax è troppo vicino al minimo, estendi un po' per evitare limiti nulli
    min_val = np.min(all_vals_concat)
    if zoom_xmax <= min_val:
        zoom_xmax = min_val + (abs(min_val) * 0.1 if min_val != 0 else 1.0)

    plt.figure(figsize=(12,6))
    any_zoom_plotted = False

    for i, (gen, df) in enumerate(data.items()):
        if feature not in df.columns:
            continue
        vals = df[feature].dropna().values
        if vals.size == 0:
            continue

        # stima KDE (di nuovo) o fallback
        try:
            kde = gaussian_kde(vals, bw_method=bandwidth)
        except Exception:
            kde = None

        if kde is not None:
            dens = kde(vals)
        else:
            dens = np.full_like(vals, fill_value=1.0, dtype=float)

        dens_scaled = dens * scale

        # filtro per lo zoom: valori piccoli <= zoom_xmax
        mask = vals <= zoom_xmax
        if not np.any(mask):
            continue

        vals_zoom = vals[mask]
        dens_zoom = dens_scaled[mask]

        # jitter orizzontale coerente (calcolato sullo span totale dei valori di quel generatore)
        span = np.ptp(vals) if np.ptp(vals) > 0 else 1.0
        x_zoom = vals_zoom + (np.random.rand(len(vals_zoom)) - 0.5) * (jitter * span)
        y_zoom = dens_zoom + (np.random.rand(len(dens_zoom)) - 0.5) * (scale * 0.05)

        plt.scatter(x_zoom, y_zoom, alpha=0.6, s=18, label=f"{gen} (n={len(vals_zoom)})")
        any_zoom_plotted = True

    if not any_zoom_plotted:
        print(f"⚠ Nessun dato rientra nel range di zoom (<= {zoom_xmax}) per {feature}")
        return

    plt.xlim(left=min_val, right=zoom_xmax)
    plt.xlabel(feature)
    plt.ylabel("Densità (punti ~ KDE) — zoom")
    plt.title(f"Zoom (valori piccoli) di {feature} (<= {zoom_xmax:.3g}, quantile {zoom_quantile})")
    plt.legend(ncol=2, fontsize="small")
    plt.grid(alpha=0.2, axis="y")
    save_plot(f"dist_density_scatter_{feature}_zoom.png")

# 4. RELIABILITY
def plot_reliability():
    names, vals = [], []
    col = "feat_reachable_from_start"
    for gen, df in data.items():
        if col in df.columns:
            valid_ratio = df[col].gt(0).mean()
            names.append(gen)
            vals.append(valid_ratio)
    if not names:
        print("⚠ Nessun dato di reliability")
        return
    plt.figure(figsize=(8,5))
    sns.barplot(x=names, y=vals)
    plt.ylim(0,1)
    plt.title("Affidabilità: percentuale mappe raggiungibili")
    plt.ylabel("Percentuale mappe valide")
    save_plot("reliability.png")

# 5. SENSITIVITY (vecchio metodo basato su CSV, mantenuto per compatibilità)
def plot_sensitivity_from_csv():
    sens_cols = [c for c in df_all.columns if c.startswith("feat_") and c.endswith("_sens")]
    if not sens_cols:
        print("⚠ Nessuna colonna sensitivity trovata (feat_*_sens) nel CSV.")
        return
    rows = []
    for gen, df in data.items():
        for col in sens_cols:
            if col in df.columns:
                vals = pd.to_numeric(df[col], errors="coerce").dropna()
                if not vals.empty:
                    rows.append({"generator": gen, "param": col.replace("feat_","").replace("_sens",""), "slope_mean": vals.mean()})
    if not rows:
        print("⚠ Nessun valore sensivity disponibile per i generatori nel CSV.")
        return
    df_sens = pd.DataFrame(rows)
    plt.figure(figsize=(10,6))
    sns.barplot(x="param", y="slope_mean", hue="generator", data=df_sens)
    plt.title("Sensibilità media per parametro (da CSV)")
    plt.ylabel("Slope medio")
    save_plot("sensitivity_from_csv.png")

# -------------------------
# Nuovo: sensitivity per generatore leggendo raw_records.json
# -------------------------

def load_raw_records(path):
    if not os.path.exists(path):
        print(f"⚠ raw_records.json non trovato in {path}")
        return []
    with open(path, "r") as f:
        try:
            raw = json.load(f)
            return raw
        except Exception as e:
            print(f"⚠ Errore caricamento raw_records.json: {e}")
            return []

def extract_sensitivity_records(raw):
    """
    Estrae i record aggregati di sensitivity creati dal main.
    Cerca label che iniziano con 'sensitivity_agg_' oppure record che contengono chiavi '*_sens' nelle features.
    Ritorna una lista di tuple (generator_token, param_name, slope_value).
    """
    rows = []
    for r in raw:
        label = r.get("label", "") or ""
        # token generatore: preferiamo il formato sensitivity_agg_<token>
        if label.startswith("sensitivity_agg_"):
            token = label.split("sensitivity_agg_")[-1]
        else:
            # fallback: estrai prima parte della label
            token = label.split("_")[0] if "_" in label else label

        features = r.get("features", {}) or {}
        # cerca chiavi che finiscono con _sens
        for k, v in features.items():
            if k.endswith("_sens"):
                param = k[:-5]  # rimuove "_sens"
                try:
                    slope = float(v)
                except Exception:
                    # se il valore non è convertibile, skip
                    continue
                rows.append({"generator": token, "param": param, "slope": slope})
    return rows

def plot_sensitivity_per_generator():
    raw = load_raw_records(RAW_RECORDS)
    if not raw:
        print("⚠ raw_records.json vuoto o non disponibile; salto plot sensitivity per generatore.")
        return

    sens_rows = extract_sensitivity_records(raw)
    if not sens_rows:
        print("⚠ Nessuna sensitivity trovata in raw_records.json.")
        return

    df_sens = pd.DataFrame(sens_rows)

    # 1) plot combinato (param vs slope con hue generator)
    plt.figure(figsize=(12,6))
    sns.barplot(x="param", y="slope", hue="generator", data=df_sens)
    plt.title("Sensibilità per parametro (combinato, da raw_records.json)")
    plt.ylabel("Slope")
    plt.xlabel("Parametro")
    plt.xticks(rotation=45, ha="right")
    save_plot("sensitivity_combined_from_raw.json.png")

    # 2) plot separato per generatore (uno file per generator)
    for gen in sorted(df_sens["generator"].unique()):
        dfg = df_sens[df_sens["generator"] == gen].copy()
        if dfg.empty:
            continue
        plt.figure(figsize=(10,5))
        # ordina per valore assoluto della slope per leggibilità
        dfg = dfg.sort_values(by="slope", key=lambda s: s.abs(), ascending=False)
        sns.barplot(x="param", y="slope", data=dfg, palette="viridis")
        plt.title(f"Sensibilità per {gen}")
        plt.ylabel("Slope")
        plt.xlabel("Parametro")
        plt.xticks(rotation=45, ha="right")
        save_plot(f"sensitivity_{gen}.png")

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    plot_speed()
    plot_expressivity("fv_floor_fraction", "fv_corridor_count")
    plot_expressivity("fv_avg_room_size", "fv_room_count")
    plot_expressivity("fv_corridor_fraction", "fv_deadend_count")
    plot_expressivity("fv_object_density", "fv_room_count")
    plot_expressivity("fv_avg_lake_size", "fv_room_count")
    plot_expressivity("fv_avg_room_size", "fv_lake_count")
    plot_expressivity("fv_room_count", "fv_lake_count")
    plot_expressivity("fv_floor_fraction", "fv_lake_count")
    plot_feature_density_scatter("fv_floor_fraction")
    plot_feature_density_scatter("fv_room_count")
    plot_feature_density_scatter("fv_avg_room_size")
    plot_feature_density_scatter("fv_max_room_size")
    plot_feature_density_scatter("fv_lake_count")
    plot_feature_density_scatter("fv_avg_lake_size")
    plot_feature_density_scatter("fv_deadend_count")
    plot_feature_density_scatter("fv_corridor_fraction")
    plot_reliability()
    # mantieni il plot basato su CSV per retrocompatibilità
    plot_sensitivity_from_csv()
    # nuovo: plot sensitivity per generatore leggendo raw_records.json
    plot_sensitivity_per_generator()
    print("\n✔ Plot generati con successo.\n")
