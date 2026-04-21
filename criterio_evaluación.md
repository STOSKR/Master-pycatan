Trabajo práctico: Agentes para Catan con heurísticas y modelos de lenguaje
Objetivo de la práctica
En este trabajo se desarrollará y evaluará un agente inteligente para el juego Catan utilizando el simulador PyCatan. La práctica combina dos enfoques complementarios: por un lado, el diseño de agentes heurísticos clásicos, basados en reglas y funciones de evaluación; por otro, la exploración del uso de modelos de lenguaje (LLM) para apoyar o automatizar ciertas decisiones dentro del agente.

El objetivo es analizar cómo pueden utilizarse distintas técnicas de inteligencia artificial en un entorno complejo y multiagente, y evaluar de forma crítica hasta qué punto los modelos de lenguaje son viables para la toma de decisiones dentro de un sistema de simulación.

La entrega consistirá en una memoria explicativa y el código desarrollado. La práctica podrá realizarse individualmente o por parejas. La memoria tendrá una extensión máxima de 10 páginas.

1. Parte 1 — Desarrollo del agente heurístico
1.1 Desarrollo y descripción del agente
En la primera sesión se ha trabajado en el desarrollo de un agente heurístico para Catan utilizando el simulador PyCatan. En esta primera parte del trabajo cada grupo deberá completar y documentar el agente implementado.

La memoria debe describir qué heurísticas se han implementado, qué decisiones del juego controla el agente y qué información del estado de la partida utiliza para decidir. También debe justificarse brevemente por qué se espera que esas heurísticas funcionen bien en el contexto del juego.

Entre las decisiones que pueden haberse implementado o modificado se encuentran, por ejemplo, la colocación inicial, las decisiones de construcción, el uso o priorización de recursos o reglas estratégicas simples. No es necesario cubrir todas las decisiones posibles del juego, pero sí explicar claramente qué parte del comportamiento del agente se ha diseñado y con qué lógica.

1.2 Evaluación mediante benchmarks
El agente deberá evaluarse utilizando los benchmarks proporcionados, que incluyen agentes random y agentes estándar del simulador.

Se deben ejecutar los experimentos utilizando la configuración de benchmarks facilitada y analizar los resultados obtenidos. La memoria debe incluir una breve descripción de los experimentos realizados, los resultados obtenidos frente a los distintos agentes y un pequeño análisis de lo observado.

Se espera comentar aspectos como si el agente mejora claramente frente al agente random, cómo se comporta frente a los agentes estándar y qué heurísticas parecen tener mayor impacto en el rendimiento. Se pueden incluir tablas o gráficos si ayudan a interpretar los resultados.

2. Parte 2 — Uso de modelos de lenguaje en el agente
2.1 Diseño de la interacción con el LLM
En esta segunda parte se explorará el uso de modelos de lenguaje (LLM) para tomar decisiones dentro del agente. El objetivo no es necesariamente construir el agente más fuerte posible, sino analizar experimentalmente cómo se comportan los LLM en este tipo de tareas y qué limitaciones presentan.

En primer lugar se debe diseñar cómo el agente se comunicará con el modelo de lenguaje. Esto implica decidir qué información del estado del juego se envía al modelo, cómo se estructura el prompt y qué formato se utiliza para representar la decisión devuelta por el modelo.

Se recomienda utilizar JSON tanto para la entrada como para la salida, aunque pueden explorarse otras alternativas. También es importante intentar reducir el número de tokens utilizados, enviando únicamente la información relevante para la decisión.

Durante esta fase se deberán probar al menos 3 prompts distintos, analizando cómo afectan a la calidad de las decisiones generadas por el modelo.

2.2 Evaluación de distintos modelos
Se deberán probar al menos 3 modelos LLM distintos, utilizando diferentes entornos de ejecución:

modelos locales ejecutados mediante Ollama
modelos disponibles en AWS Bedrock (contactar con Juanmi Alberola para solicitar una API key de 1-2 días de duración)
modelos accesibles a través de la API de la UPV
Para cada modelo se analizarán aspectos como el tiempo de respuesta, los tokens (en caso de que sea factible), la calidad de las decisiones generadas, la facilidad de integración y el coste o consumo de recursos cuando sea relevante.

2.3 Integración en el agente
El modelo de lenguaje deberá integrarse en el agente para tomar al menos dos tipos de decisiones distintas:

la decisión inicial on_game_start
otra decisión que se produzca con frecuencia durante la partida
Dado el coste computacional de las llamadas a modelos de lenguaje, no es necesario ejecutar benchmarks completos en esta parte. En su lugar pueden realizarse experimentos más ligeros con un número reducido de partidas que permitan observar la tendencia del comportamiento del agente y evaluar la calidad de las decisiones generadas.

2.4 Análisis y conclusiones
La memoria debe incluir una comparación entre los distintos modelos y prompts utilizados, así como una reflexión sobre la viabilidad del uso de LLM en este contexto.

Se espera discutir qué modelos parecen funcionar mejor para este tipo de decisiones, qué tipo de prompts producen mejores resultados, qué impacto tiene la latencia en la simulación y en qué partes del agente resulta razonable utilizar LLM y en cuáles no.

3. Uso de herramientas de IA durante el desarrollo
3.1 Uso transversal en ambas partes del trabajo
Durante todo el trabajo se permite y se fomenta el uso de herramientas de inteligencia artificial generativa para apoyar el desarrollo.

Esto incluye herramientas como asistentes de programación integrados en editores, herramientas de desarrollo asistido como Opencode o Antigravity, y modelos conversacionales como ChatGPT, Claude u otros.

En la memoria se debe explicar brevemente qué herramientas se han utilizado, para qué tareas se han empleado y cómo de útiles han resultado en el proceso de desarrollo. También es interesante comentar limitaciones o problemas encontrados al utilizar estas herramientas.

4. Entrega
4.1 Memoria
Se deberá entregar una memoria con una extensión máxima de 10 páginas. La memoria debe describir el trabajo realizado, incluyendo el diseño del agente heurístico, los resultados de los benchmarks, el uso de herramientas de IA, el diseño de prompts y experimentos con LLM, así como un análisis final de los resultados obtenidos.

4.2 Código
Se debe entregar el código desarrollado, incluyendo el agente heurístico, la integración con modelos de lenguaje y cualquier script o herramienta utilizada para realizar los experimentos.

El código debe estar correctamente organizado y comentado.

4.3 Modalidad de trabajo
La práctica podrá realizarse individualmente o por parejas. En caso de realizarse en pareja, ambos miembros deberán ser capaces de explicar el trabajo desarrollado.

5. Evaluación
Se valorará especialmente la calidad del agente heurístico desarrollado, la claridad de la memoria, la calidad del análisis experimental, el diseño y evaluación de prompts y modelos LLM, la capacidad crítica en el análisis de resultados y la calidad y funcionamiento del código entregado.

6. Rúbrica de evaluación
Criterio	Descripción	Puntos
Agente heurístico	Calidad de las heurísticas implementadas, claridad en la lógica del agente y correcta integración en el simulador PyCatan.	3
Resultados de benchmarks	Ejecución correcta de los benchmarks proporcionados, presentación clara de resultados y análisis razonado del comportamiento del agente frente a random y agentes estándar.	2
Uso de LLM en el agente	Implementación de decisiones con LLM (al menos on_game_start y otra decisión frecuente), experimentación con distintos prompts y modelos.	2
Análisis experimental	Comparación entre modelos y prompts, análisis de latencia, calidad de decisiones y reflexión sobre la viabilidad del uso de LLM en el agente.	2
Memoria y código	Claridad de la memoria, estructura del trabajo, código organizado y comentado, reproducibilidad de los experimentos.	1
Total: 10 puntos

