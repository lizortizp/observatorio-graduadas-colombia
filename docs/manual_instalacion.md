# Manual de instalación del tablero y la API

**Observatorio de participación femenina entre graduados en Colombia (SNIES 2020-2025)**

El tablero (Streamlit, puerto 8501) y la API del modelo (FastAPI, puerto 8000) se despliegan con Docker Compose.

## 1. Requisitos

- Docker y Docker Compose v2.
- Git.
- Los archivos de datos y del modelo descargados con DVC (ver paso 3).
- Para despliegue en la nube: una instancia EC2 (se usó Ubuntu 24.04, t3.medium) con el grupo de seguridad abierto en los puertos 22, 8000 y 8501.

## 2. Clonar el repositorio

```bash
git clone https://github.com/lizortizp/observatorio-graduadas-colombia.git entrega-final
cd entrega-final
```

## 3. Obtener datos y modelo con DVC

Los datos y el modelo (`resultados/modelos/modelo_seleccionado.joblib`) se versionan con DVC; el almacenamiento remoto es un bucket S3 (`s3://dvc-observatorio-graduadas-lortiz/dvc`).

```bash
pip install dvc[s3]
dvc remote modify --local almacenamiento access_key_id <ACCESS_KEY>
dvc remote modify --local almacenamiento secret_access_key <SECRET_KEY>
dvc remote modify --local almacenamiento session_token <SESSION_TOKEN>
dvc pull
```

Las credenciales quedan en `.dvc/config.local`, que Git ignora. **No las publique.**

Si el repositorio ya contiene los archivos necesarios en el contexto de Docker (`data/derivado`, `data/geo`, `resultados/modelos`), este paso ya está cubierto.

## 4. Construir y ejecutar

```bash
docker compose up --build -d
docker compose ps
```

Debe verse `api` y `dashboard` en estado *Up (healthy)*.

Archivos Docker del proyecto:

- `Dockerfile.api`: imagen de la API (Python 3.12, `requirements-api.txt`, copia `src/` y el modelo).
- `Dockerfile.dashboard`: imagen del tablero (Python 3.12, `requirements.txt`, copia `dashboard/`, `src/`, datos y resultados).
- `docker-compose.yml`: define ambos servicios; el tablero usa `OBSERVATORIO_API_URL=http://api:8000/predict` y espera a que la API esté sana.

## 5. Verificar

- Tablero: `http://<IP-PUBLICA>:8501`
- Documentación de la API: `http://<IP-PUBLICA>:8000/docs`
- Salud de la API: `http://<IP-PUBLICA>:8000/health`

Prueba rápida de la API:

```bash
curl -X POST http://<IP-PUBLICA>:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"area_conocimiento":"Agronomía, veterinaria y afines","nivel_formacion_normalizado":"DOCTORADO","sector_normalizado":"OFICIAL","caracter_institucion":"Institución Tecnológica","departamento_normalizado":"AMAZONAS","anio":2025}'
```

La respuesta incluye `proporcion_esperada`, `porcentaje_esperado`, `modelo` y `anio`.

## 6. Despliegue en AWS EC2 (resumen de lo realizado)

1. Lanzar una instancia Ubuntu 24.04 (t3.medium) y abrir en el grupo de seguridad los puertos 22, 8000 y 8501.
2. Conectarse (EC2 Instance Connect, usuario `ubuntu`) e instalar Docker:
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose-v2 git
   ```
3. Clonar el repositorio y ejecutar `sudo docker compose up --build -d`.
4. La IP pública cambia cada vez que se detiene y se inicia la instancia; use la IP vigente.

## 7. Operación

```bash
sudo docker compose logs -f      # ver registros
sudo docker compose down         # detener servicios
sudo docker compose up -d        # reiniciar sin reconstruir
```

## 8. Ejecución local sin Docker (opcional)

```bash
python -m venv .venv
.venv\Scripts\activate           # en Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api:app --port 8000
set OBSERVATORIO_API_URL=http://localhost:8000/predict
streamlit run dashboard/app.py
```

## 9. Problemas frecuentes

| Problema | Solución |
|---|---|
| `dvc pull` dice "Unable to locate credentials" | Las credenciales temporales de AWS Academy vencieron; renuévelas con `dvc remote modify --local`. |
| La página no abre | Revise la IP actual, use `http://` y confirme que el puerto esté abierto en el grupo de seguridad. |
| Falta memoria al construir | Use una instancia con al menos 4 GB de RAM (t3.medium). |
