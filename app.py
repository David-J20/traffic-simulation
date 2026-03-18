"""
Simulacion de Trafico - Pagina Web
Carriles Exclusivos para Motos Electricas
"""

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import numpy as np
import random
from dataclasses import dataclass
from typing import List, Optional

# Configuracion de pagina
st.set_page_config(
    page_title="Simulacion de Trafico",
    page_icon="🚗",
    layout="wide"
)

# ============================================================================
# CONFIGURACION
# ============================================================================

CONFIG = {
    "num_carros": 25,
    "num_motos": 18,
    "velocidad_carro_min": 1.5,
    "velocidad_carro_max": 3.5,
    "velocidad_moto_min": 5.0,
    "velocidad_moto_max": 7.5,
    "longitud_via": 500,
    "pasos_simulacion": 200,
    "num_simulaciones": 10,
    "distancia_seguridad": 35,
    "factor_congestion_mixto": 0.25,
    "emision_moto_gasolina": 72,
}

# ============================================================================
# CLASES
# ============================================================================

@dataclass
class Vehiculo:
    id: int
    tipo: str
    posicion: float
    velocidad_base: float
    carril: int = 0
    tiempo_inicio: int = 0
    tiempo_llegada: Optional[int] = None
    distancia_recorrida: float = 0
    color: str = ""

    def __post_init__(self):
        self.velocidad_actual = self.velocidad_base
        if not self.color:
            if self.tipo == "carro":
                self.color = random.choice(['#3498db', '#2c3e50', '#7f8c8d', '#c0392b', '#8e44ad'])
            else:
                self.color = '#27ae60'

    def mover(self, velocidad_efectiva: float):
        self.posicion += velocidad_efectiva
        self.distancia_recorrida += velocidad_efectiva

    def ha_llegado(self, longitud_via: float) -> bool:
        return self.posicion >= longitud_via


def crear_vehiculo(id: int, tipo: str, config: dict, carril: int = 0) -> Vehiculo:
    if tipo == "carro":
        velocidad = random.uniform(config["velocidad_carro_min"], config["velocidad_carro_max"])
    else:
        velocidad = random.uniform(config["velocidad_moto_min"], config["velocidad_moto_max"])
    posicion = random.uniform(0, config["longitud_via"] * 0.3)
    return Vehiculo(id=id, tipo=tipo, posicion=posicion, velocidad_base=velocidad, carril=carril)


# ============================================================================
# SIMULACION BASICA
# ============================================================================

class SimulacionBasica:
    def __init__(self, config: dict):
        self.config = config
        self.vehiculos: List[Vehiculo] = []
        self.paso_actual = 0

    def inicializar_vehiculos(self):
        self.vehiculos = []
        for i in range(self.config["num_carros"]):
            self.vehiculos.append(crear_vehiculo(i, "carro", self.config))
        for i in range(self.config["num_motos"]):
            self.vehiculos.append(crear_vehiculo(i + self.config["num_carros"], "moto", self.config))

    def calcular_congestion(self, vehiculo: Vehiculo, es_mixto: bool) -> float:
        dist = self.config["distancia_seguridad"]
        adelante = [v for v in self.vehiculos
                   if v.id != vehiculo.id and v.tiempo_llegada is None
                   and v.posicion > vehiculo.posicion
                   and v.posicion - vehiculo.posicion < dist * 2]

        if not es_mixto:
            if vehiculo.tipo == "moto":
                return max(0.9, 1.0 - len(adelante) * 0.02)
            carros = [v for v in adelante if v.tipo == "carro"]
            return max(0.6, 1.0 - len(carros) * 0.1) if carros else 1.0

        if not adelante:
            return 1.0

        carros = sum(1 for v in adelante if v.tipo == "carro")
        motos = sum(1 for v in adelante if v.tipo == "moto")

        if vehiculo.tipo == "moto":
            factor = 1.0 - (carros * 0.15) - (motos * 0.05)
            factor *= (1 - self.config["factor_congestion_mixto"] * 0.3)
            return max(0.35, factor)
        return max(0.45, 1.0 - (carros * 0.12) - (motos * 0.03))

    def ejecutar_paso(self, es_mixto: bool):
        self.paso_actual += 1
        for v in self.vehiculos:
            if v.tiempo_llegada is not None:
                continue
            factor = self.calcular_congestion(v, es_mixto)
            v.mover(v.velocidad_base * factor)
            if v.ha_llegado(self.config["longitud_via"]):
                v.tiempo_llegada = self.paso_actual

    def ejecutar_simulacion(self, es_mixto: bool) -> dict:
        self.inicializar_vehiculos()
        self.paso_actual = 0
        for _ in range(self.config["pasos_simulacion"]):
            self.ejecutar_paso(es_mixto)
        return self.calcular_metricas()

    def calcular_metricas(self) -> dict:
        tiempos_carros, tiempos_motos = [], []
        for v in self.vehiculos:
            if v.tiempo_llegada is not None:
                t = v.tiempo_llegada - v.tiempo_inicio
                (tiempos_carros if v.tipo == "carro" else tiempos_motos).append(t)

        t_carros = sum(tiempos_carros) / len(tiempos_carros) if tiempos_carros else float('inf')
        t_motos = sum(tiempos_motos) / len(tiempos_motos) if tiempos_motos else float('inf')
        total = len(self.vehiculos)
        llegaron = len(tiempos_carros) + len(tiempos_motos)

        return {
            "tiempo_promedio_carros": t_carros,
            "tiempo_promedio_motos": t_motos,
            "carros_llegaron": len(tiempos_carros),
            "motos_llegaron": len(tiempos_motos),
            "eficiencia": (llegaron / total) * 100 if total > 0 else 0,
        }


# ============================================================================
# FUNCIONES DE VISUALIZACION
# ============================================================================

def ejecutar_simulaciones(config, progress_bar=None):
    resultados_mixto = {"tiempo_promedio_carros": [], "tiempo_promedio_motos": [], "eficiencia": []}
    resultados_exclusivo = {"tiempo_promedio_carros": [], "tiempo_promedio_motos": [], "eficiencia": []}

    for i in range(config["num_simulaciones"]):
        sim = SimulacionBasica(config)

        r_mixto = sim.ejecutar_simulacion(es_mixto=True)
        for k in resultados_mixto:
            resultados_mixto[k].append(r_mixto[k])

        r_excl = sim.ejecutar_simulacion(es_mixto=False)
        for k in resultados_exclusivo:
            resultados_exclusivo[k].append(r_excl[k])

        if progress_bar:
            progress_bar.progress((i + 1) / config["num_simulaciones"])

    def prom(lista):
        v = [x for x in lista if x != float('inf')]
        return sum(v) / len(v) if v else 0

    return {k: prom(v) for k, v in resultados_mixto.items()}, {k: prom(v) for k, v in resultados_exclusivo.items()}


def crear_graficas(mixto, exclusivo):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Comparacion: Trafico Mixto vs Carril Exclusivo', fontsize=14, fontweight='bold')

    colores = ['#e74c3c', '#27ae60']
    labels = ['Mixto', 'Exclusivo']

    # Grafica 1
    ax1 = axes[0]
    tiempos = [mixto["tiempo_promedio_carros"], exclusivo["tiempo_promedio_carros"],
               mixto["tiempo_promedio_motos"], exclusivo["tiempo_promedio_motos"]]
    bars = ax1.bar([0, 1, 2, 3], tiempos, color=[colores[0], colores[1], colores[0], colores[1]], edgecolor='black')
    ax1.set_xticks([0, 1, 2, 3])
    ax1.set_xticklabels(['Carros\nMixto', 'Carros\nExcl', 'Motos\nMixto', 'Motos\nExcl'])
    ax1.set_ylabel('Tiempo promedio (pasos)')
    ax1.set_title('Tiempos de Viaje')
    for bar, t in zip(bars, tiempos):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{t:.0f}', ha='center', fontweight='bold')

    # Grafica 2
    ax2 = axes[1]
    bars2 = ax2.bar(labels, [mixto["tiempo_promedio_motos"], exclusivo["tiempo_promedio_motos"]], color=colores, edgecolor='black')
    ax2.set_ylabel('Tiempo promedio (pasos)')
    ax2.set_title('Tiempo de Viaje - MOTOS')
    if mixto["tiempo_promedio_motos"] > 0:
        mejora = (mixto["tiempo_promedio_motos"] - exclusivo["tiempo_promedio_motos"]) / mixto["tiempo_promedio_motos"] * 100
        ax2.annotate(f'{mejora:.0f}% menos\ntiempo', xy=(1, exclusivo["tiempo_promedio_motos"]),
                    xytext=(0.5, (mixto["tiempo_promedio_motos"] + exclusivo["tiempo_promedio_motos"])/2),
                    fontsize=11, color='green', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='green', lw=2))

    # Grafica 3
    ax3 = axes[2]
    bars3 = ax3.bar(labels, [mixto["eficiencia"], exclusivo["eficiencia"]], color=colores, edgecolor='black')
    ax3.set_ylabel('Eficiencia (%)')
    ax3.set_title('Vehiculos que Llegaron')
    ax3.set_ylim(0, 110)
    ax3.axhline(y=100, color='gray', linestyle='--', alpha=0.5)
    for bar, e in zip(bars3, [mixto["eficiencia"], exclusivo["eficiencia"]]):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f'{e:.0f}%', ha='center', fontweight='bold')

    plt.tight_layout()
    return fig


def crear_animacion_estatica(num_frames=100):
    """Crea una secuencia de frames para mostrar como animacion."""
    random.seed(42)

    # Inicializar vehiculos
    vehiculos_mixto = []
    vehiculos_exclusivo = []

    for i in range(CONFIG["num_carros"]):
        v_m = crear_vehiculo(i, "carro", CONFIG, random.choice([0, 1]))
        v_e = crear_vehiculo(i, "carro", CONFIG, random.choice([0, 1]))
        v_e.posicion = v_m.posicion
        v_e.color = v_m.color
        vehiculos_mixto.append(v_m)
        vehiculos_exclusivo.append(v_e)

    for i in range(CONFIG["num_motos"]):
        id_m = i + CONFIG["num_carros"]
        v_m = crear_vehiculo(id_m, "moto", CONFIG, random.choice([0, 1]))
        v_e = crear_vehiculo(id_m, "moto", CONFIG, 2)
        v_e.posicion = v_m.posicion
        vehiculos_mixto.append(v_m)
        vehiculos_exclusivo.append(v_e)

    def calcular_cong(v, vehiculos, es_excl):
        dist = CONFIG["distancia_seguridad"]
        adelante = [x for x in vehiculos if x.id != v.id and x.carril == v.carril
                   and x.tiempo_llegada is None and x.posicion > v.posicion]
        dist_min = min([x.posicion - v.posicion for x in adelante], default=float('inf'))

        if es_excl and v.tipo == "moto":
            return 0.95 if dist_min > dist else max(0.6, dist_min / dist)
        if not es_excl and v.tipo == "moto":
            for x in vehiculos:
                if x.tipo == "carro" and x.tiempo_llegada is None and x.posicion > v.posicion:
                    if x.posicion - v.posicion < dist * 2:
                        return CONFIG["factor_congestion_mixto"]
        return 1.0 if dist_min > dist * 3 else max(0.15, dist_min / dist * 0.5)

    def mover_todos(vehiculos, es_excl, paso):
        for v in vehiculos:
            if v.tiempo_llegada:
                continue
            f = calcular_cong(v, vehiculos, es_excl)
            v.mover(v.velocidad_base * f)
            if v.posicion >= CONFIG["longitud_via"]:
                v.tiempo_llegada = paso

    def contar_llegados(vehiculos):
        return {
            "carros": sum(1 for v in vehiculos if v.tipo == "carro" and v.tiempo_llegada),
            "motos": sum(1 for v in vehiculos if v.tipo == "moto" and v.tiempo_llegada)
        }

    def dibujar_frame(paso):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
        fig.patch.set_facecolor('#1a1a2e')
        fig.suptitle(f'Simulacion de Trafico - Paso {paso}', fontsize=14, fontweight='bold', color='white')

        L = CONFIG["longitud_via"]

        for ax, vehiculos, es_excl, titulo, color_t in [
            (ax1, vehiculos_mixto, False, 'SIN CARRIL EXCLUSIVO - Motos bloqueadas', '#e74c3c'),
            (ax2, vehiculos_exclusivo, True, 'CON CARRIL EXCLUSIVO - Motos fluyen libres', '#27ae60')
        ]:
            ax.set_facecolor('#16213e')
            ax.set_xlim(-10, L + 50)
            ax.set_ylim(-3, 25)
            ax.axis('off')

            ax.text(L/2, 23, titulo, ha='center', fontsize=12, fontweight='bold', color=color_t)

            # Carriles
            for i in range(2):
                ax.add_patch(patches.Rectangle((0, i*7), L, 6, facecolor='#2c3e50', edgecolor='white', lw=1))
            if es_excl:
                ax.add_patch(patches.Rectangle((0, 14), L, 5, facecolor='#0a4d1c', edgecolor='#00ff00', lw=2))
                ax.text(L/2, 16.5, 'CARRIL EXCLUSIVO MOTOS', ha='center', color='#00ff00', fontsize=9, fontweight='bold')

            # Meta
            ax.add_patch(patches.Rectangle((L-8, 0), 8, 19 if es_excl else 14, facecolor='#27ae60', alpha=0.8))
            ax.text(L-4, 9 if es_excl else 7, 'META', ha='center', va='center', color='white', fontweight='bold')

            # Vehiculos
            for v in vehiculos:
                if v.tiempo_llegada:
                    continue
                y = v.carril * 7 + 3 if v.carril < 2 else 16.5
                if v.tipo == "carro":
                    ax.add_patch(patches.FancyBboxPatch((v.posicion-8, y-2), 16, 4,
                                boxstyle="round,pad=0.2", facecolor=v.color, edgecolor='black', lw=1))
                else:
                    color = '#00ff00' if es_excl else '#ff6b35'
                    ax.add_patch(patches.Circle((v.posicion, y), 2.5, facecolor=color, edgecolor='black', lw=1))

            llegados = contar_llegados(vehiculos)
            ax.text(10, -1.5, f"Carros: {llegados['carros']}/{CONFIG['num_carros']}  |  Motos: {llegados['motos']}/{CONFIG['num_motos']}",
                   fontsize=10, color='white')

        plt.tight_layout()
        return fig

    # Simular y crear frames
    frames = []
    for paso in range(num_frames):
        mover_todos(vehiculos_mixto, False, paso)
        mover_todos(vehiculos_exclusivo, True, paso)
        if paso % 5 == 0:  # Guardar cada 5 frames para eficiencia
            frames.append((paso,
                          [(v.posicion, v.carril, v.tipo, v.color, v.tiempo_llegada) for v in vehiculos_mixto],
                          [(v.posicion, v.carril, v.tipo, v.color, v.tiempo_llegada) for v in vehiculos_exclusivo]))

    return frames, dibujar_frame, vehiculos_mixto, vehiculos_exclusivo


# ============================================================================
# INTERFAZ DE STREAMLIT
# ============================================================================

# Titulo principal
st.title("🚗 Simulacion de Trafico")
st.markdown("### Carriles Exclusivos para Motos Electricas")

st.markdown("""
Esta simulacion compara dos escenarios:
- **Trafico Mixto**: Carros y motos comparten los mismos carriles
- **Carril Exclusivo**: Las motos electricas tienen su propio carril
""")

st.divider()

# Configuracion en sidebar
with st.sidebar:
    st.header("Configuracion")
    num_carros = st.slider("Numero de carros", 10, 50, CONFIG["num_carros"])
    num_motos = st.slider("Numero de motos", 5, 30, CONFIG["num_motos"])
    num_sims = st.slider("Simulaciones a promediar", 5, 20, CONFIG["num_simulaciones"])

    CONFIG["num_carros"] = num_carros
    CONFIG["num_motos"] = num_motos
    CONFIG["num_simulaciones"] = num_sims

# Botones principales
st.markdown("### Selecciona que deseas ver:")

col1, col2, col3 = st.columns(3)

with col1:
    btn_graficas = st.button("📊 Ver Graficas", use_container_width=True, type="primary")

with col2:
    btn_animacion = st.button("🎬 Ver Animacion", use_container_width=True, type="primary")

with col3:
    btn_ambos = st.button("📊🎬 Ver Ambos", use_container_width=True, type="secondary")

st.divider()

# Ejecutar segun el boton presionado
if btn_graficas or btn_ambos:
    st.markdown("## 📊 Graficas Comparativas")

    with st.spinner("Ejecutando simulaciones..."):
        progress = st.progress(0)
        mixto, exclusivo = ejecutar_simulaciones(CONFIG, progress)

    # Mostrar metricas
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ❌ Trafico Mixto")
        st.metric("Tiempo promedio motos", f"{mixto['tiempo_promedio_motos']:.1f} pasos")
        st.metric("Eficiencia", f"{mixto['eficiencia']:.1f}%")

    with col2:
        st.markdown("#### ✅ Carril Exclusivo")
        mejora = 0
        if mixto['tiempo_promedio_motos'] > 0:
            mejora = (mixto['tiempo_promedio_motos'] - exclusivo['tiempo_promedio_motos']) / mixto['tiempo_promedio_motos'] * 100
        st.metric("Tiempo promedio motos", f"{exclusivo['tiempo_promedio_motos']:.1f} pasos", f"-{mejora:.1f}%")
        st.metric("Eficiencia", f"{exclusivo['eficiencia']:.1f}%", f"+{exclusivo['eficiencia'] - mixto['eficiencia']:.1f}%")

    # Mostrar graficas
    fig = crear_graficas(mixto, exclusivo)
    st.pyplot(fig)
    plt.close()

    st.divider()

if btn_animacion or btn_ambos:
    st.markdown("## 🎬 Animacion de la Simulacion")

    with st.spinner("Generando animacion..."):
        frames, dibujar_frame, v_mixto, v_excl = crear_animacion_estatica(150)

    # Slider para controlar el frame
    frame_idx = st.slider("Paso de la simulacion", 0, len(frames)-1, 0, key="frame_slider")

    # Reconstruir estado para el frame seleccionado
    random.seed(42)
    vehiculos_mixto = []
    vehiculos_exclusivo = []

    for i in range(CONFIG["num_carros"]):
        v_m = crear_vehiculo(i, "carro", CONFIG, random.choice([0, 1]))
        v_e = crear_vehiculo(i, "carro", CONFIG, random.choice([0, 1]))
        v_e.posicion = v_m.posicion
        v_e.color = v_m.color
        vehiculos_mixto.append(v_m)
        vehiculos_exclusivo.append(v_e)

    for i in range(CONFIG["num_motos"]):
        id_m = i + CONFIG["num_carros"]
        v_m = crear_vehiculo(id_m, "moto", CONFIG, random.choice([0, 1]))
        v_e = crear_vehiculo(id_m, "moto", CONFIG, 2)
        v_e.posicion = v_m.posicion
        vehiculos_mixto.append(v_m)
        vehiculos_exclusivo.append(v_e)

    # Aplicar estado del frame
    paso, datos_mixto, datos_excl = frames[frame_idx]
    for i, (pos, carril, tipo, color, llegada) in enumerate(datos_mixto):
        vehiculos_mixto[i].posicion = pos
        vehiculos_mixto[i].tiempo_llegada = llegada
    for i, (pos, carril, tipo, color, llegada) in enumerate(datos_excl):
        vehiculos_exclusivo[i].posicion = pos
        vehiculos_exclusivo[i].tiempo_llegada = llegada

    # Dibujar
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
    fig.patch.set_facecolor('#1a1a2e')
    fig.suptitle(f'Simulacion de Trafico - Paso {paso}', fontsize=14, fontweight='bold', color='white')

    L = CONFIG["longitud_via"]

    for ax, vehiculos, es_excl, titulo, color_t in [
        (ax1, vehiculos_mixto, False, 'SIN CARRIL EXCLUSIVO - Motos bloqueadas', '#e74c3c'),
        (ax2, vehiculos_exclusivo, True, 'CON CARRIL EXCLUSIVO - Motos fluyen libres', '#27ae60')
    ]:
        ax.set_facecolor('#16213e')
        ax.set_xlim(-10, L + 50)
        ax.set_ylim(-3, 25)
        ax.axis('off')

        ax.text(L/2, 23, titulo, ha='center', fontsize=12, fontweight='bold', color=color_t)

        for i in range(2):
            ax.add_patch(patches.Rectangle((0, i*7), L, 6, facecolor='#2c3e50', edgecolor='white', lw=1))
        if es_excl:
            ax.add_patch(patches.Rectangle((0, 14), L, 5, facecolor='#0a4d1c', edgecolor='#00ff00', lw=2))
            ax.text(L/2, 16.5, 'CARRIL EXCLUSIVO MOTOS', ha='center', color='#00ff00', fontsize=9, fontweight='bold')

        ax.add_patch(patches.Rectangle((L-8, 0), 8, 19 if es_excl else 14, facecolor='#27ae60', alpha=0.8))
        ax.text(L-4, 9 if es_excl else 7, 'META', ha='center', va='center', color='white', fontweight='bold')

        for v in vehiculos:
            if v.tiempo_llegada:
                continue
            y = v.carril * 7 + 3 if v.carril < 2 else 16.5
            if v.tipo == "carro":
                ax.add_patch(patches.FancyBboxPatch((v.posicion-8, y-2), 16, 4,
                            boxstyle="round,pad=0.2", facecolor=v.color, edgecolor='black', lw=1))
            else:
                color = '#00ff00' if es_excl else '#ff6b35'
                ax.add_patch(patches.Circle((v.posicion, y), 2.5, facecolor=color, edgecolor='black', lw=1))

        llegados_c = sum(1 for v in vehiculos if v.tipo == "carro" and v.tiempo_llegada)
        llegados_m = sum(1 for v in vehiculos if v.tipo == "moto" and v.tiempo_llegada)
        ax.text(10, -1.5, f"Carros: {llegados_c}/{CONFIG['num_carros']}  |  Motos: {llegados_m}/{CONFIG['num_motos']}",
               fontsize=10, color='white')

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.info("💡 Mueve el slider para ver como avanza la simulacion en el tiempo")

# Footer
st.divider()
st.markdown("""
---
**Proyecto Universitario** - Simulacion de Trafico
Demuestra el beneficio de carriles exclusivos para motos electricas
""")
