# Esquema de calificación

Cada problema ejecuta **10 casos en orden creciente de dificultad**. Cada caso aprobado vale **1 punto**.

- Nota por problema: `0–10`.
- Nota global: `(puntos de los 3 problemas / 30) × 10`.
- La interfaz conserva el mejor puntaje de cada problema durante la sesión del navegador.

## 1. Suffix Array

| Caso | Perfil |
|---:|---|
| 1 | Cadena mínima |
| 2 | Repeticiones idénticas |
| 3 | Patrón clásico pequeño |
| 4 | Repeticiones y solapamientos |
| 5 | Cadena periódica mediana |
| 6 | Aleatoria, 128 caracteres |
| 7 | Mezcla periódica/aleatoria |
| 8 | Aleatoria, 1,500 caracteres |
| 9 | Aleatoria, 12,000 caracteres |
| 10 | Aleatoria, 60,000 caracteres; penaliza materializar todos los sufijos |

## 2. Longest Common Substring

| Caso | Perfil |
|---:|---|
| 1 | Coincidencia mínima |
| 2 | Coincidencia corta |
| 3 | Solapamientos |
| 4 | Sin coincidencia |
| 5 | Patrón periódico |
| 6 | Aleatorias medianas |
| 7 | Coincidencia implantada |
| 8 | ~1,200 × ~1,300 caracteres |
| 9 | ~4,000 × ~4,200 caracteres |
| 10 | ~8,000 × ~8,500 caracteres; penaliza DP cuadrática lenta |

## 3. Trie

| Caso | Perfil |
|---:|---|
| 1 | Inserción y búsqueda básica |
| 2 | Diferencia entre palabra y prefijo |
| 3 | Prefijos anidados |
| 4 | Inserciones duplicadas |
| 5 | 30 palabras + 50 consultas |
| 6 | 100 palabras + 180 consultas |
| 7 | 300 palabras + 500 consultas |
| 8 | 800 palabras + 1,300 consultas |
| 9 | 2,500 palabras + 4,000 consultas |
| 10 | 12,000 palabras + 20,000 consultas; penaliza buscar linealmente en una lista |

## Casos visibles y ocultos

Los casos 1 y 2 de cada problema están marcados como visibles. Los casos 3–10 son ocultos para la interfaz: el frontend recibe únicamente si pasaron, el tiempo de ejecución y el tipo de error. Los datos exactos de las pruebas permanecen en el servidor.

Para una evaluación real, despliega desde un repositorio privado. Si los estudiantes tienen acceso al código fuente del backend, también podrán inspeccionar los generadores de casos ocultos.
