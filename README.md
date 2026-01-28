# AI Travel Planner 🌍

Aplicación web en Streamlit que genera itinerarios de viaje con IA, mapas interactivos y recomendaciones basadas en platos locales, intereses o presupuesto. Usa herramientas externas (Google Maps y búsqueda web) y un agente conversacional para decidir qué plan crear y formatear la respuesta.

## Funcionalidades principales

- Chat interactivo para pedir planes por ciudad.
- Tres tipos de planes:
  - **General** (enriquecido) cuando no hay preferencias.
  - **Intereses** (arte, historia, naturaleza, etc.).
  - **Presupuesto** (económico o lujo).
- **Mapa interactivo** con puntos de interés y restaurantes.
- Recomendaciones con **enlaces clicables** a Google Maps.
- Resúmenes en Markdown listos para copiar.

## Arquitectura rápida

1. **Usuario** escribe la petición en Streamlit.
2. **Agente** decide qué herramienta usar siguiendo reglas del system prompt:
   - Primero busca platos locales.
   - Luego ejecuta el plan adecuado (interés/presupuesto/general).
3. **Herramientas** llaman a:
   - **Tavily Search** para platos tradicionales.
   - **Google Maps Places** para atracciones/restaurantes.
4. El resultado se renderiza en:
   - **Chat** (texto Markdown).
   - **Mapa** (HTML con JSON).

## Requisitos

- Python 3.12
- API keys:
  - `OPENAI_API_KEY`
  - `GOOGLE_API_KEY`
  - `TAVILY_API_KEY` (si usas Tavily)

## Instalación

1) Crear entorno virtual:
```bash
python3.12 -m venv venv
source venv/bin/activate
```

2) Instalar dependencias:
```bash
pip install -r requirements.txt
```

3) Variables de entorno:
```bash
cp .env.example .env
```
Edita `.env` con tus claves.

## Ejecutar la app

```bash
streamlit run main.py
```

Abre la URL que imprime Streamlit (por defecto `http://localhost:8501`).

## Uso

Ejemplos de prompts:

- `Plan general para Roma`
- `Quiero un plan barato en Lisboa`
- `Un plan de arte y museos en París`

El agente:
1. Busca platos locales.
2. Genera el plan adecuado.
3. Devuelve un resumen con enlaces y muestra el mapa.

## Estructura del proyecto

```
travel_agent/
├─ agent/
│  └─ agent_builder.py
├─ main.py
├─ tools.py
├─ utils.py
├─ interface.html
├─ .env
└─ venv/
```

## Archivos clave

- `main.py`: UI en Streamlit, chat y render del mapa.
- `agent/agent_builder.py`: creación del agente y salida compatible.
- `tools.py`: herramientas (dishes, plan general, plan budget, plan por interés).
- `utils.py`: helpers para geocoding, links y precios.
- `interface.html`: plantilla del mapa.

## Configuración del agente

El sistema de reglas del agente vive en `agent/agent_builder.py`. Resumen:

- Siempre busca platos locales primero.
- Si detecta **interés**, usa `create_interest_focused_plan`.
- Si detecta **presupuesto**, usa `create_budget_focused_plan`.
- Si no hay preferencias, usa `create_enriched_discovery_plan`.
- Si falla una herramienta específica, aplica fallback al plan general.

## Logs en consola

El agente imprime salida legible en consola usando Rich (paneles por usuario, herramientas y asistente).  
Si no ves color, asegúrate de tener `rich` instalado:

```bash
pip install rich
```

## Salida del mapa

El mapa se genera con `interface.html` y un bloque JSON inyectado desde el output de las herramientas.  
En `main.py` se usa el último tool output válido para pintar el mapa.

## Errores comunes

**1) No aparecen resultados o el mapa queda vacío**  
Revisa que `GOOGLE_API_KEY` sea válido y tenga habilitados:
- Geocoding API
- Places API

**2) Error en búsqueda de platos**
- `TAVILY_API_KEY` no configurada o límite de uso.
- La tool `find_traditional_dishes_deep` devuelve un error JSON.

**3) Import errors de LangChain**
Si actualizaste paquetes manualmente, revisa compatibilidad:
- `langchain`
- `langchain-core`
- `langchain-openai`
- `langchain-community`

## Personalización rápida

- Cambiar el modelo: edita `model=` en `agent/agent_builder.py`.
- Ajustar el número de lugares: en `tools.py` (cortes con `[:10]`, `[:7]`, etc.).
- Cambiar el radio de búsqueda: `city_radius` en `tools.py`.
- Modificar la UI: `main.py` + `interface.html`.

## Seguridad

No publiques tu `.env`. Usa variables de entorno reales en producción.
