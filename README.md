# AlgoGrader — mini clon de LeetCode en Python

Aplicación web con tres problemas de estructuras de datos/algoritmos:

1. **Suffix Array** — `suffix_array(s) -> list[int]`
2. **Longest Common Substring** — `longest_common_substring(a, b) -> int`
3. **Trie** — clase con `insert`, `search` y `starts_with`

Cada problema tiene **10 casos de prueba progresivos**. Cada caso vale 1 punto, por lo que cada problema se califica sobre 10. La nota global mostrada en la interfaz es `casos aprobados / 30 × 10`.

## Características

- FastAPI como backend y frontend estático sin build step.
- 10 casos por problema; los dos primeros se marcan como visibles y los demás como ocultos.
- El navegador nunca recibe los datos de los casos ocultos.
- El editor bloquea `paste`, `Ctrl/Cmd+V`, `beforeinput` de pegado y drag & drop.
- Ejecución de soluciones en procesos separados con timeout y límites de recursos en Linux.
- Sin imports en las soluciones y con un conjunto reducido de builtins.
- Rate limit básico por IP: 12 envíos/minuto por instancia.
- `Dockerfile`, `render.yaml` y endpoint `/api/health` listos para Render.

## Importante sobre seguridad y “no copiar”

El bloqueo de pegado es una **restricción de interfaz**, no un mecanismo invulnerable: un alumno con DevTools o llamando la API directamente puede saltárselo. Del mismo modo, ejecutar Python ajeno dentro del mismo host nunca debe considerarse un sandbox fuerte solo por usar AST + `subprocess` + `rlimit`.

Este proyecto es apropiado para un **grupo de estudiantes de confianza / laboratorio controlado**. Si el sitio será público o recibirá código hostil, sustituye `app/judge.py` por un juez aislado (por ejemplo, contenedores efímeros fuera del proceso web, gVisor/Firecracker o un servicio especializado de ejecución de código). Render no debe tratarse como frontera de seguridad para ejecutar código arbitrario dentro de tu web service.

## Ejecutar localmente

Requiere Docker, o Python 3.12+.

### Con Docker

```bash
docker build -t algograder .
docker run --rm -p 10000:10000 algograder
```

Abre `http://localhost:10000`.

### Sin Docker

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 10000
```

## Pruebas

```bash
pytest -q
```

## Desplegar en Render desde un repo

1. Crea un repositorio Git (idealmente **privado**, para no publicar los casos ocultos) y sube estos archivos.
2. En Render, crea un **Blueprint** desde el repositorio; Render leerá `render.yaml`. Como alternativa, crea un **Web Service** y selecciona Docker.
3. El contenedor escucha en `0.0.0.0` y usa la variable `PORT` que entrega Render.
4. El health check está configurado en `/api/health`.
5. Al hacer push a la rama conectada, Render puede reconstruir y desplegar automáticamente el servicio.

El filesystem del servicio no se usa para guardar calificaciones. La nota actual se mantiene en `sessionStorage` del navegador. Si necesitas un libro de calificaciones persistente, añade autenticación y una base de datos externa/persistente antes de usarlo como sistema oficial de evaluación.

## Subirlo a GitHub

```bash
git init
git add .
git commit -m "Initial AlgoGrader"
git branch -M main
git remote add origin TU_REPO
git push -u origin main
```

## API

- `GET /api/health`
- `GET /api/problems`
- `GET /api/problems/{slug}`
- `POST /api/submit`

Ejemplo de payload:

```json
{
  "problem": "longest-common-substring",
  "code": "def longest_common_substring(a, b):\n    ..."
}
```

## Estructura

```text
algograder/
├── app/
│   ├── __init__.py
│   ├── judge.py
│   ├── main.py
│   ├── problems.py
│   └── static/
│       ├── app.js
│       ├── index.html
│       └── styles.css
├── tests/
│   └── test_api.py
├── Dockerfile
├── render.yaml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Editor

El editor incluye resaltado de sintaxis de Python para palabras clave, built-ins, strings, comentarios, números y operadores. El resaltado es local y no habilita pegado de código.
