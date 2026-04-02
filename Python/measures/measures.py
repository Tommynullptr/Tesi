import time
import json
import csv
import statistics
import math

from contextlib import contextmanager
from pathlib import Path
from collections import defaultdict


class Measures:
    """
    Contenitore per misure PCG:
    - timing per fase
    - features e feature_vector per expressivity/diversity
    - reliability violations e flags
    - input_params e strutture per controllability (sensitivity/coverage)
    """
    def __init__(self, seed = None, label = "default", input_params = None):

        self.seed = seed
        self.label = label
        self.input_params = input_params or {}
        self.phase_totals = {}          # fase -> secondi, tempi per qualsiasi fase
        self.features = {}
        self.meta = {}                  # dati liberi o di default
        self.wall_start = None          # tempo totale di esecuzione
        self.wall_end = None

        # expressivity/diversity
        self.features_vector = None     # dict name -> numeric
        # per confronti con altre mappe

        # controllability
        self.sensitivity_data = defaultdict(list)  # list of (param_value, feature_value)
        self.control_coverage = {}      # {min,max,unique} info su quanto si ha esplorato i parametri di controllo

    # timer totale
    def start_wall(self):
        self.wall_start = time.perf_counter()

    def end_wall(self):
        self.wall_end = time.perf_counter()

    # Timing di una fase (name)
    def start_phase(self, name):
        setattr(self, f"start_{name}", time.perf_counter())

    def end_phase(self, name):
        start = getattr(self, f"start_{name}", None)
        if start is None:
            return

        elapsed = time.perf_counter() - start
        self.phase_totals[name] = self.phase_totals.get(name, 0.0) + elapsed
        delattr(self, f"start_{name}") # pulisco la variabile temporanea

    @contextmanager # utilizzare con "with"
    def time_phase(self, name):
        self.start_phase(name)

        try:
            yield
        finally:
            self.end_phase(name)

    # Features
    def add_feature(self, name, value):
        if name in self.features:
            v = self.features[name]

            if isinstance(v, list):
                v.append(value)

            else:
                self.features[name] = [v, value]

        else:
            self.features[name] = value

    def set_meta(self, name, value):
        self.meta[name] = value

    # Feature vector for diversity/expressivity
    def set_features_vector(self, vec):
        # Imposta il feature vector (rappresentazione numerica del contenuto generato)
        self.features_vector = vec # per accesso rapido
        self.features["feature_vector"] = vec # per serializzazione

    # Controllability helpers
    def record_control_sample(self, param_name, param_value, feature_value):
        # dato un certo parametro ottengo una certa feature
        self.sensitivity_data[param_name].append((param_value, feature_value)) # lega un valore di una feature
        # con il valore di un parametro
        vals = [v for v,_ in self.sensitivity_data[param_name]]
        # calcola copertura del parametro:
        # la copertura quanto bene si è esplorato i possibili valori di un parametro tra
        # min e max, unique mi dice la varietà dei valori nei test e quindi quanti valori ho coperto tra min e max
        # più ho valori unici in un intervallo ristretto migliore è la copertura
        self.control_coverage[param_name] = {
            "min": min(vals), "max": max(vals), "unique": len(set(vals))
        }

    # Sensivity: quanto una feature cambia a seconda di un parametro
    def compute_sensitivity(self, param_name):
        samples = self.sensitivity_data.get(param_name, []) # ricavo i samples registrati per un parametro
        # è una lista di tuple param_value/feature_value

        if len(samples) < 2:
            return None

        xs = [float(x) for x,_ in samples] # valori del parametro
        ys = [float(y) for _,y in samples] # valori delle feature
        n = len(xs) # numero di campioni
        mean_x = statistics.mean(xs); mean_y = statistics.mean(ys)
        # retta di regressione lineare: per stimare la relazione tra param_value e feature_value
        num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
        den = sum((xs[i] - mean_x) ** 2 for i in range(n))

        if den == 0:
            return None

        slope = num/den # slope: quanto cambia la feature/pendenza, mi indica la sensibilità ai valori diversi del parametro
        ss_tot = sum((y - mean_y) ** 2 for y in ys) # ss: samples
        ss_res = sum((ys[i] - (slope * (xs[i] - mean_x) + mean_y)) ** 2 for i in range(n))
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else None # r2: qualità del modello, mi dice quanto è affidabile
        # ad esempio uno slope alto e r2 alto vuol dire che il parametro è efficace e prevedibile
        # slope alto ma r2 basso, non è uno slope affidabile
        # slope basso allora ho un parametro inutile e se ho r2 alto sono sicuro di ciò

        self.add_feature(param_name + "_sens", slope)

        return {"param": param_name, "slope": slope, "r2": r2}

    # Serializzazione
    def to_dict(self):
        # serializza sensitivity_data: {param: [[x,y],[x,y],...], ...}
        sens = {k: [[float(x), float(y)] for x, y in v] for k, v in self.sensitivity_data.items()}

        return {
            "seed": self.seed,
            "label": self.label,
            "wall_time": (self.wall_end - self.wall_start) if (self.wall_start and self.wall_end) else None,
            "phase_totals": self.phase_totals,
            "features": self.features,
            "meta": self.meta,
            "control_coverage": self.control_coverage,
            "sensitivity_data": sens
        }

    # salva file json
    def to_json(self, path):
        Path(path).parent.mkdir(parents = True, exist_ok = True)

        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent = 2)

    # Salva batch e crea CSV (ogni riga = una misura)
    @classmethod
    def save_batch(cls, measures_list, out_dir="Python/results/measures_batch", csv_name="summary.csv"):
        out = Path(out_dir)
        out.mkdir(parents = True, exist_ok = True)
        raw = [m.to_dict() if isinstance(m, Measures) else m for m in measures_list]

        with open(out / "raw_records.json", "w") as f:
            json.dump(raw, f, indent = 2)

        phase_keys = set()
        feat_keys = set()

        for r in raw:
            # raccolgo le chiavi di features e fasi
            phase_keys.update(r.get("phase_totals", {}).keys())
            feat_keys.update(r.get("features", {}).keys())

        phase_keys = sorted(phase_keys)
        # prendi tutte le chiavi del feature_vector
        fv_keys = set()

        for r in raw:
            fv = r.get("features", {}).get("feature_vector", {})

            if isinstance(fv, dict):
                fv_keys.update(fv.keys())

        fv_keys = sorted(fv_keys)

        feat_keys = sorted(k for k in feat_keys if k != "feature_vector")

        headers = (
                ["seed", "label", "wall_time"]
                + [f"phase_{k}" for k in phase_keys]
                + [f"feat_{k}" for k in feat_keys]
                + [f"fv_{k}" for k in fv_keys]
        )

        with open(out / csv_name, "w", newline = "") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for r in raw:
                row = [r.get("seed"), r.get("label"), r.get("wall_time")]

                for k in phase_keys:
                    row.append(r.get("phase_totals", {}).get(k, ""))

                # features normali
                for k in feat_keys:
                    row.append(r.get("features", {}).get(k, ""))

                # feature_vector flattenato
                fv = r.get("features", {}).get("feature_vector", {})
                for k in fv_keys:
                    row.append(fv.get(k, ""))

                writer.writerow(row)

    # Helpers per aggregazione
    # percentile: per capire come sono distribuiti i dati, valore sotto il quale ricadono
    @classmethod
    def percentile(cls, arr, q): # q -> percentile
        if not arr:
            return None

        arr_sorted = sorted(arr)
        idx = int(max(0, min(len(arr_sorted) - 1, int(len(arr_sorted) * q) - 1)))

        return arr_sorted[idx] # restituisce il valore dell'array sotto il quale ricadono il q% dei dati

    @classmethod
    def aggregate(cls, measures_list, numeric_phase_keys = None):
        # Per ciascuna fase ho: media, stdev, percentili
        dicts = [m.to_dict() if isinstance(m, Measures) else m for m in measures_list]

        if numeric_phase_keys is None:
            keys = set()

            for d in dicts:
                keys.update(d.get("phase_totals", {}).keys())

            numeric_phase_keys = sorted(keys)

        summary = {}
        totals = []

        for k in numeric_phase_keys:
            arr = [d.get("phase_totals", {}).get(k, 0.0) for d in dicts]

            if not arr:
                continue

            n = len(arr)
            summary[k] = {
                "count": n,
                "mean": statistics.mean(arr),
                "stdev": statistics.pstdev(arr) if n > 1 else 0.0
            }
            totals.extend(arr)

        total_time = sum(totals) if totals else None
        summary["throughput_maps_per_sec"] = (len(dicts) / total_time) if total_time and total_time > 0 else None
        # quantità mappe al secondo

        return summary

    # utility per la diversità di uno stesso batch
    @staticmethod
    def feature_vector_distance(v1, v2): # vettori delle feature
        # distanza euclidea tra due feature vector rappresentati come dict name->numeric, considerando solo le chiavi in comune
        # mi dice quanto sono diverse le mappe
        keys = sorted(set(v1.keys()) & set(v2.keys()))

        if not keys:
            return None

        s = 0.0

        for k in keys: # confronto solo ciò che è in comune
            # formula della distanza euclidea
            a = float(v1[k]); b = float(v2[k])
            s += (a - b) ** 2

        return math.sqrt(s) # valore grande -> feature molto diverse

    @classmethod
    def diversity_stats(cls, measures_list): # diversità tra tutti i contenuti
        # calcola le distanze a coppie resituendo media, mediana e max/min
        # estrazione vettori features
        vecs = [m.features_vector for m in measures_list if getattr(m, "feature_vector", None) is not None]
        n = len(vecs)

        if n < 2:
            return {"count": n, "mean_pairwise": None}

        dists = [] # distanze

        for i in range(n):
            for j in range(i + 1, n): # esploro tutte le coppie uniche
                d = cls.feature_vector_distance(vecs[i], vecs[j])

                if d is not None:
                    dists.append(d)

        if not dists:
            return {"count": n, "mean_pairwise": None}

        return {
            "count": n,
            "mean_pairwise": statistics.mean(dists), # distanza media tra i contenuti, alta -> molta varietà
            "median_pairwise": statistics.median(dists), # media tipica dei contenuti
            "max_pairwise": max(dists), # contenuti più diversi
            "min_pairwise": min(dists) # contenuti più simili
        }
