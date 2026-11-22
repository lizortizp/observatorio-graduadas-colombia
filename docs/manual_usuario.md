# Manual de usuario del tablero

**Observatorio de participación femenina entre graduados en Colombia (SNIES 2020-2025)**

## 1. ¿Para qué sirve?

El tablero permite explorar qué proporción de los graduados de educación superior en Colombia son mujeres, y comparar esa proporción con la que un modelo de aprendizaje automático (Random Forest) estima como esperable según las características del programa. Está pensado para analistas y tomadores de decisión del sector educativo.

**Importante:** los valores esperados son estimaciones estadísticas. No son metas normativas ni explicaciones causales.

## 2. Cómo acceder

Abra en el navegador la dirección donde esté desplegado el tablero:

`http://<IP-PUBLICA>:8501`

(La IP cambia cada vez que se reinicia la máquina en la nube; ver el manual de instalación.) El navegador puede mostrar "No seguro" porque se usa HTTP; es normal.

## 3. Filtros (barra lateral izquierda)

Los filtros se aplican a todas las secciones del tablero.

| Filtro | Qué hace |
|---|---|
| Año de referencia | Año de graduación que se resume en el panorama general y en el mapa (2020-2025). |
| Área de conocimiento | Una o varias áreas de conocimiento (selección múltiple). |
| Nivel de formación | Pregrado, especialización, maestría, doctorado, etc. |
| Sector institucional | Oficial o privado. |
| Carácter de la institución | Universidad, institución universitaria, tecnológica, etc. |
| Departamento | Departamento donde se ofrece el programa. |

Para quitar un filtro, deje la opción por defecto ("Todos...") o use la **x** en la selección.

## 4. Secciones del tablero

1. **Panorama general.** Tres indicadores para la selección actual: total de graduados, mujeres graduadas y participación femenina (%). El universo son los programas con al menos 15 graduados por año; los porcentajes se ponderan por número de graduados.
2. **Evolución de la participación femenina.** Línea con la participación femenina por año (2020-2025).
3. **Participación femenina por área de conocimiento.** Barras para comparar áreas.
4. **Participación femenina por departamento.** Mapa de Colombia y gráfico de barras por departamento.
5. **Participación observada frente a esperada.** Compara la participación real con la estimada por el modelo. La brecha es *observado menos esperado*: positiva significa más mujeres de lo esperado; negativa, menos. Use el selector **"Comparar brechas por"** (área de conocimiento, departamento, nivel de formación o sector). Solo hay predicciones fuera de muestra para 2024 y 2025; si la selección no los incluye, el tablero lo indica. La brecha es una señal para revisar, no un veredicto.
6. **¿Qué variables influyen en las predicciones?** Importancia por permutación de las variables del modelo: cuánto empeora el error cuando se altera cada variable.
7. **Simulador de participación femenina esperada.** Estima la participación esperada para un programa hipotético.

## 5. Cómo usar el simulador

1. Baje hasta "Simulador de participación femenina esperada".
2. Elija: área de conocimiento, nivel de formación, sector, carácter de la institución, departamento y año de referencia.
3. Pulse **Calcular participación esperada**.
4. Aparece el mensaje "Predicción generada correctamente" y el porcentaje esperado (por ejemplo, 50.81 %).

El cálculo lo realiza la API del modelo desplegada junto al tablero.

## 6. Problemas frecuentes

| Situación | Qué hacer |
|---|---|
| La página no carga | Verifique que la máquina en la nube esté encendida, que use la IP actual y `http://` (no `https://`). |
| El simulador muestra error | Verifique que la API responda en `http://<IP-PUBLICA>:8000/health`. |
| "No hay predicciones fuera de muestra" | Cambie el año de referencia a 2024 o 2025 o amplíe los filtros. |
| Los gráficos quedan vacíos | La combinación de filtros no tiene programas con al menos 15 graduados; amplíe los filtros. |
