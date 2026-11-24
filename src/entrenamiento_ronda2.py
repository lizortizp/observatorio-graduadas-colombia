"""Ronda 2 de experimentos - Observatorio de participación femenina.

Nuevas versiones de los modelos respecto a la ronda 1 (src/entrenamiento_modelos.py):
  A) Random Forest sin la variable `anio`.
  B) Random Forest con malla de hiperparámetros ampliada (más árboles, max_features).
  C) HistGradientBoosting (otra familia de boosting) con malla propia.
  D) Ridge con búsqueda de alpha.
Mismo protocolo que la ronda 1: ajuste en 2020-2022, validación 2023, reentreno 2020-2023
y evaluación final en 2024-2025. No sobrescribe el modelo del tablero/API.

Uso:  python src/entrenamiento_ronda2.py --tracking-uri http://IP:5000
"""
import argparse, itertools, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from entrenamiento_modelos import CAT, SEMILLA, cargar, metricas

try:
    import mlflow, mlflow.sklearn
except ImportError:
    mlflow = None


def construir_pipe(modelo, num, denso=False):
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=not denso), CAT),
        ("num", "passthrough", num)])
    return Pipeline([("pre", pre), ("m", modelo)])


def experimentos():
    """(nombre, num, denso, clase, lista de parámetros candidatos, descripción)"""
    rf_base = [dict(n_estimators=150, max_depth=d, min_samples_leaf=l, n_jobs=-1, random_state=SEMILLA)
               for d, l in itertools.product([8, 16, None], [5, 20])]
    rf_amp = [dict(n_estimators=300, max_depth=d, min_samples_leaf=l, max_features=mf,
                   n_jobs=-1, random_state=SEMILLA)
              for d, l, mf in itertools.product([None, 24], [2, 5, 10], [0.3, 0.6])]
    hgb = [dict(max_iter=300, learning_rate=lr, max_leaf_nodes=ml, l2_regularization=l2,
                random_state=SEMILLA)
           for lr, ml, l2 in itertools.product([0.05, 0.1], [31, 63], [0.0, 1.0])]
    ridge = [dict(alpha=a) for a in (0.1, 1.0, 10.0, 30.0)]
    return [
        ("rf_sin_anio", [], False, RandomForestRegressor, rf_base,
         "Random Forest sin la variable anio"),
        ("rf_malla_ampliada", ["anio"], False, RandomForestRegressor, rf_amp,
         "Random Forest, 300 árboles, max_features y min_samples_leaf ampliados"),
        ("hist_gradient_boosting", ["anio"], True, HistGradientBoostingRegressor, hgb,
         "HistGradientBoosting con malla de tasa de aprendizaje, hojas y L2"),
        ("ridge_alpha", ["anio"], False, Ridge, ridge,
         "Ridge con búsqueda de alpha"),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ruta", default="data/derivado/programas_anio.xls")
    ap.add_argument("--salida", default="resultados/modelos_ronda2")
    ap.add_argument("--tracking-uri", default=None)
    ap.add_argument("--experimento", default="observatorio_prop_mujeres")
    a = ap.parse_args()
    out = Path(a.salida); out.mkdir(parents=True, exist_ok=True)

    if mlflow:
        if a.tracking_uri:
            mlflow.set_tracking_uri(a.tracking_uri)
        mlflow.set_experiment(a.experimento)
    else:
        print("MLflow no instalado: se omite el registro (los CSV sí se generan).")

    df = cargar(a.ruta)
    tr_int, va_int = df[df.anio <= 2022], df[df.anio == 2023]
    train, test = df[df.anio <= 2023], df[df.anio >= 2024]
    print(f"train={len(train)} test={len(test)} (validación interna 2023={len(va_int)})")

    filas = []
    for nombre, num, denso, clase, cands, desc in experimentos():
        cols = CAT + num
        mejor, mejor_mae = None, np.inf
        for p in cands:
            pipe = construir_pipe(clase(**p), num, denso)
            pipe.fit(tr_int[cols], tr_int.prop_mujeres, m__sample_weight=tr_int.total)
            pv = pipe.predict(va_int[cols])
            mae = mean_absolute_error(va_int.prop_mujeres, pv, sample_weight=va_int.total)
            if mae < mejor_mae:
                mejor, mejor_mae = p, mae
        pipe = construir_pipe(clase(**mejor), num, denso)
        pipe.fit(train[cols], train.prop_mujeres, m__sample_weight=train.total)
        pred = np.clip(pipe.predict(test[cols]), 0, 1)
        m = metricas(test.prop_mujeres, pred, test.total)
        m["mae_pond_validacion"] = mejor_mae
        print(f"{nombre:24s} MAE_pond={m['mae_pond']:.4f} RMSE_pond={m['rmse_pond']:.4f} R2_pond={m['r2_pond']:.3f}")
        filas.append({"modelo": nombre, "descripcion": desc, **m, "params": json.dumps(mejor)})

        if mlflow:
            with mlflow.start_run(run_name=f"ronda2__{nombre}"):
                mlflow.set_tag("ronda", "2")
                mlflow.log_params({**mejor, "modelo": nombre, "descripcion": desc,
                                   "variables_numericas": ",".join(num) or "ninguna",
                                   "train": "2020-2023", "test": "2024-2025"})
                mlflow.log_metrics({k: float(v) for k, v in m.items()})
                mlflow.sklearn.log_model(pipe, name="modelo", serialization_format="cloudpickle")

    res = pd.DataFrame(filas).sort_values("mae_pond")
    res.to_csv(out / "metricas_ronda2.csv", index=False)

    # comparación con el modelo seleccionado en la ronda 1 (si existe su CSV)
    r1 = Path("resultados/modelos/metricas.csv")
    if r1.exists():
        m1 = pd.read_csv(r1)
        m1 = m1[m1.variante == "solo_caracteristicas"].sort_values("mae_pond").iloc[0]
        print(f"\nRonda 1 (seleccionado): {m1['modelo']} MAE_pond={m1['mae_pond']:.4f} "
              f"RMSE_pond={m1['rmse_pond']:.4f} R2_pond={m1['r2_pond']:.3f}")
        mejor2 = res.iloc[0]
        print(f"Ronda 2 (mejor): {mejor2['modelo']} MAE_pond={mejor2['mae_pond']:.4f}")
    print("\nResultados en", out / "metricas_ronda2.csv")


if __name__ == "__main__":
    main()
