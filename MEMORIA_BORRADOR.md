# Trabajo practico: Agentes para Catan con heuristicas y modelos de lenguaje

## Datos generales
- Asignatura: [pendiente]
- Integrantes: [nombre 1], [nombre 2]
- Fecha: 2026-04-20
- Repositorio: STOSKR/Master-pycatan

---

## Resumen
En este trabajo se desarrollo y evaluo un agente para PyCatan en dos fases. Primero se construyo un agente heuristico basado en funciones de evaluacion y reglas estrategicas sobre el estado del tablero. Segundo, se integro un agente asistido por LLM para tomar decisiones en `on_game_start` y `on_build_phase`, manteniendo un mecanismo de seguridad por fallback a heuristicas.

Los resultados muestran rendimiento muy alto del agente heuristico frente a random y buen rendimiento frente al pool estandar. En la fase LLM, el rendimiento global se mantiene, pero los experimentos actuales presentan `fallback_rate` muy alto (1.0 en los benchmarks largos), por lo que en esta iteracion la politica efectiva fue mayoritariamente heuristica.

---

## 1. Parte 1 - Desarrollo del agente heuristico

### 1.1 Desarrollo y descripcion
Se implemento el agente `AlexPelochoJaimeHeuristicAgent` con logica centrada en valor esperado de produccion, diversidad de recursos y potencial de expansion.

#### Decisiones implementadas
1. Colocacion inicial (`on_game_start`):
- Seleccion del mejor nodo con `choose_best_node`.
- Seleccion de carretera inicial con `choose_best_starting_road`.

2. Fase de construccion (`on_build_phase`):
- Prioridad de construccion: ciudad > pueblo > carretera > carta de desarrollo.
- Seleccion de nodo/carretera por puntuacion heuristica (`settlement_score`, `road_score`).

3. Fase de comercio (`on_commerce_phase`):
- Objetivo dinamico de construccion (`choose_target_building`).
- Intercambio con banca (`choose_bank_trade`) para reducir faltantes.
- Limite de acciones de comercio por turno (`max_commerce_actions_per_turn`).

4. Otras decisiones:
- Robo/ladron (`choose_thief_target`).
- Monopolio (`choose_material_for_monopoly`).
- Year of Plenty (`choose_materials_for_year_of_plenty`).
- Aceptacion de ofertas de comercio por valor esperado de recursos.

#### Informacion del estado utilizada
- Recursos en mano y faltantes para costes de construccion.
- Nodos validos para ciudad/pueblo/carretera.
- Probabilidades de dados por terreno adyacente.
- Diversidad de tipos de recurso.
- Puertos y ratio de intercambio con banca.
- Presencia de enemigo/propio para mover ladron.

#### Justificacion de las heuristicas
Las reglas priorizan acciones que maximizan produccion esperada y flexibilidad futura. La combinacion de peso por probabilidad, diversidad y expansion busca evitar bloqueos de recursos y mantener ritmo de construccion durante la partida.

### 1.2 Evaluacion por benchmarks
Se ejecutaron los dos benchmarks del proyecto:
- `PyCatan/benchmark_vs_agentes_estandar.py`
- `PyCatan/benchmark_vs_random.py`

#### Resultado vs agentes estandar
Fuente: `benchmark_vs_estandar_resultados.csv`

| Agente | Tipo | Partidas | Victorias | Win rate | Media puntos | Puesto medio |
|---|---|---:|---:|---:|---:|---:|
| AlexPelochoJaimeHeuristicAgent | Heuristico | 144 | 129 | 0.8958 | 9.56 | 1.17 |
| AlexPelochoJaimeLLMAgent | LLM | 144 | 120 | 0.8333 | 9.34 | 1.22 |

#### Resultado vs random
Fuente: `benchmark_vs_random_resultados.csv`

| Agente | Tipo | Partidas | Victorias | Win rate | Media puntos | Puesto medio |
|---|---|---:|---:|---:|---:|---:|
| AlexPelochoJaimeHeuristicAgent | Heuristico | 160 | 160 | 1.0000 | 10.01 | 1.00 |
| AlexPelochoJaimeLLMAgent | LLM | 160 | 160 | 1.0000 | 10.01 | 1.00 |

#### Analisis
- El agente heuristico supera claramente al baseline random.
- Frente al pool estandar, mantiene un rendimiento alto y estable.
- El rendimiento agregado sugiere que la seleccion de nodos y la politica de construccion tienen impacto fuerte.

---

## 2. Parte 2 - Uso de modelos de lenguaje

### 2.1 Diseno de la interaccion con el LLM
El agente LLM devuelve decisiones por indice de accion legal (`action_index`) en JSON estricto. Se envia un estado reducido con informacion relevante para minimizar tokens y reducir ruido.

#### Variantes de prompt probadas
Definidas en `PyCatan/Agents/llm_prompts.py`:
1. `compact_json`
2. `resource_focus`
3. `safe_legal`

Todas comparten restriccion de salida JSON-only con esquema controlado.

### 2.2 Evaluacion de modelos
En los benchmarks actuales se uso:
- Proveedor: Ollama
- Modelo: `qwen2.5:0.5b`

Pendiente para completar requisitos de la practica:
- Probar al menos un modelo en Bedrock.
- Probar al menos un modelo via API UPV.
- Consolidar comparativa de 3 modelos minimos en total.

### 2.3 Integracion en el agente
El LLM se integra en:
1. `on_game_start` (decision inicial).
2. `on_build_phase` (decision frecuente durante partida).

Cuando el LLM no responde correctamente (timeout, error de red, JSON invalido, etc.), el sistema aplica fallback a la accion heuristica para mantener robustez.

### 2.4 Analisis de fallback y viabilidad
En los resultados actuales se observa:
- `fallback_rate = 1.0` para el agente LLM en benchmarks largos.
- Evidencia de causa en ejecucion de prueba: `provider_error: Network error ... Connection refused` hacia `http://127.0.0.1:11434/api/chat`.

Interpretacion:
- El agente LLM ejecuto intentos de decision (`Decisiones LLM` no nulo), pero casi todas las decisiones terminaron en fallback.
- Por eso el comportamiento real fue practicamente heuristico.

Implicacion para la memoria:
- Con estos datos no se puede concluir calidad intrinseca del modelo para decision en Catan, solo robustez del mecanismo de fallback.
- Es necesario repetir experimentos con conectividad estable y medir latencia, tokens y calidad de decision efectiva del LLM.

---

## 3. Uso de herramientas de IA durante el desarrollo
- Herramienta principal: GitHub Copilot Chat para apoyo en refactor, instrumentacion de benchmarks y analisis de resultados.
- Utilidad observada:
  - Acelera cambios repetitivos y conversion de logs/resultados a formato reproducible.
  - Facilita detectar inconsistencias de imports y errores de integracion.
- Limitaciones:
  - Requiere verificacion manual de resultados y trazabilidad en CSV.
  - Puede introducir cambios validos tecnicamente pero no alineados con el protocolo experimental si no se controla el alcance.

---

## 4. Estructura de codigo y reproducibilidad
### Archivos clave
- `PyCatan/Agents/AlexPelochoJaimeHeuristicAgent.py`
- `PyCatan/Agents/heuristic_core.py`
- `PyCatan/Agents/AlexPelochoJaimeLLMAgent.py`
- `PyCatan/Agents/llm_prompts.py`
- `PyCatan/benchmark_vs_agentes_estandar.py`
- `PyCatan/benchmark_vs_random.py`
- `benchmark_vs_estandar_resultados.csv`
- `benchmark_vs_random_resultados.csv`

### Parametros de benchmark (corrida larga actual)
- Estandar: `CATAN_BENCH_N_MATCHES_PER_PERM=3`, `CATAN_BENCH_MAX_PERMUTATIONS=12`, `CATAN_BENCH_MAX_ROUNDS=120`.
- Random: `CATAN_BENCH_N_MATCHES=40`, `CATAN_BENCH_MAX_ROUNDS=120`.
- LLM: `CATAN_LLM_PROVIDER=ollama`, `CATAN_LLM_MODEL=qwen2.5:0.5b`.

---

## 5. Conclusiones (borrador)
1. El agente heuristico alcanza rendimiento competitivo y consistente, especialmente frente a random.
2. La integracion LLM esta implementada en dos decisiones clave y es robusta gracias al fallback.
3. En la configuracion actual, los errores de proveedor provocan fallback masivo, por lo que falta evidencia experimental limpia para comparar calidad real entre prompts y modelos.
4. Como siguiente paso, se deben ejecutar pruebas con conectividad estable y completar la comparativa requerida (Ollama + Bedrock + UPV) con igual presupuesto de partidas por configuracion.

---

## 6. Trabajo pendiente para cerrar entrega final
1. Completar matriz 3 prompts x 3 modelos con el mismo presupuesto de partidas.
2. Anadir tabla de latencia media y, cuando sea posible, tokens de entrada/salida por configuracion.
3. Incluir un grafico comparando win rate y fallback rate por modelo/prompt.
4. Revisar el texto final para ajustarlo a maximo 10 paginas.
