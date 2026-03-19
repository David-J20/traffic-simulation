"""
================================================================================
SIMULACION DE TRAFICO - CARRILES EXCLUSIVOS PARA MOTOS ELECTRICAS
================================================================================

Sistema unificado de simulacion de trafico que compara:
1. Trafico mixto: carros y motos comparten carriles
2. Carril exclusivo: motos electricas tienen su propio carril

Incluye:
- Simulacion basica con graficas comparativas
- Simulacion visual avanzada con animacion en tiempo real
- Metricas de sostenibilidad y medio ambiente

Proyecto universitario
================================================================================
"""

import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple

# ============================================================================
# CONFIGURACION GLOBAL
# ============================================================================

CONFIG = {
    # === VEHICULOS ===
    "num_carros": 25,
    "num_motos": 18,

    # === VELOCIDADES (unidades por paso) ===
    # Carros: mas lentos
    "velocidad_carro_min": 1.5,
    "velocidad_carro_max": 3.5,
    # Motos: mas rapidas
    "velocidad_moto_min": 5.0,
    "velocidad_moto_max": 7.5,

    # === VIA ===
    "longitud_via": 500,
    "ancho_carril": 3.5,

    # === SIMULACION ===
    "pasos_simulacion": 250,
    "intervalo_animacion_ms": 50,
    "num_simulaciones": 10,

    # === CONGESTION ===
    "distancia_seguridad": 35,
    "factor_congestion_mixto": 0.25,

    # === SOSTENIBILIDAD ===
    "emision_carro_gasolina": 120,      # g CO2/km
    "emision_moto_gasolina": 72,        # g CO2/km
    "emision_moto_electrica": 0,        # g CO2/km (cero directo)
    "consumo_carro_litros_km": 0.08,
    "consumo_moto_elec_kwh_km": 0.025,
    "costo_gasolina_litro": 1.2,        # USD
    "costo_electricidad_kwh": 0.15,     # USD
}


# ============================================================================
# CLASES DE DATOS
# ============================================================================

@dataclass
class Vehiculo:
    """Representa un vehiculo en la simulacion."""
    id: int
    tipo: str                           # 'carro' o 'moto'
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
                self.color = random.choice([
                    '#3498db', '#2c3e50', '#7f8c8d', '#c0392b', '#8e44ad'
                ])
            else:
                self.color = '#27ae60'  # Verde para motos electricas

    def mover(self, velocidad_efectiva: float) -> None:
        """Mueve el vehiculo segun su velocidad efectiva."""
        self.posicion += velocidad_efectiva
        self.distancia_recorrida += velocidad_efectiva

    def ha_llegado(self, longitud_via: float) -> bool:
        """Verifica si el vehiculo llego al final de la via."""
        return self.posicion >= longitud_via


@dataclass
class MetricasSostenibilidad:
    """Metricas ambientales de la simulacion."""
    co2_ahorrado_kg: float = 0
    energia_ahorrada_kwh: float = 0
    dinero_ahorrado_usd: float = 0
    arboles_equivalentes: float = 0
    km_recorridos_electrico: float = 0


# ============================================================================
# FUNCIONES DE CREACION DE VEHICULOS
# ============================================================================

def crear_vehiculo(id: int, tipo: str, config: dict, carril: int = 0) -> Vehiculo:
    """Crea un vehiculo con parametros aleatorios."""
    if tipo == "carro":
        velocidad = random.uniform(
            config["velocidad_carro_min"],
            config["velocidad_carro_max"]
        )
    else:
        velocidad = random.uniform(
            config["velocidad_moto_min"],
            config["velocidad_moto_max"]
        )

    posicion_inicial = random.uniform(0, config["longitud_via"] * 0.3)

    return Vehiculo(
        id=id,
        tipo=tipo,
        posicion=posicion_inicial,
        velocidad_base=velocidad,
        carril=carril
    )


# ============================================================================
# SIMULACION BASICA (texto + graficas)
# ============================================================================

class SimulacionBasica:
    """
    Simulacion simple que compara trafico mixto vs carril exclusivo.
    Genera graficas comparativas y metricas.
    """

    def __init__(self, config: dict):
        self.config = config
        self.vehiculos: List[Vehiculo] = []
        self.paso_actual = 0

    def inicializar_vehiculos(self) -> None:
        """Crea todos los vehiculos."""
        self.vehiculos = []

        for i in range(self.config["num_carros"]):
            self.vehiculos.append(crear_vehiculo(i, "carro", self.config))

        for i in range(self.config["num_motos"]):
            id_moto = i + self.config["num_carros"]
            self.vehiculos.append(crear_vehiculo(id_moto, "moto", self.config))

    def calcular_congestion(self, vehiculo: Vehiculo, es_mixto: bool) -> float:
        """Calcula el factor de congestion para un vehiculo."""
        dist_seguridad = self.config["distancia_seguridad"]

        vehiculos_adelante = [
            v for v in self.vehiculos
            if v.id != vehiculo.id
            and v.tiempo_llegada is None
            and v.posicion > vehiculo.posicion
            and v.posicion - vehiculo.posicion < dist_seguridad * 2
        ]

        if not es_mixto:
            # CARRIL EXCLUSIVO
            if vehiculo.tipo == "moto":
                return max(0.9, 1.0 - len(vehiculos_adelante) * 0.02)

            carros_adelante = [v for v in vehiculos_adelante if v.tipo == "carro"]
            if not carros_adelante:
                return 1.0
            return max(0.6, 1.0 - len(carros_adelante) * 0.1)

        # TRAFICO MIXTO
        if not vehiculos_adelante:
            return 1.0

        carros_adelante = sum(1 for v in vehiculos_adelante if v.tipo == "carro")
        motos_adelante = sum(1 for v in vehiculos_adelante if v.tipo == "moto")

        if vehiculo.tipo == "moto":
            factor = 1.0 - (carros_adelante * 0.15) - (motos_adelante * 0.05)
            factor *= (1 - self.config["factor_congestion_mixto"] * 0.3)
            return max(0.35, factor)
        else:
            factor = 1.0 - (carros_adelante * 0.12) - (motos_adelante * 0.03)
            return max(0.45, factor)

    def ejecutar_paso(self, es_mixto: bool) -> None:
        """Ejecuta un paso de tiempo en la simulacion."""
        self.paso_actual += 1

        for vehiculo in self.vehiculos:
            if vehiculo.tiempo_llegada is not None:
                continue

            factor = self.calcular_congestion(vehiculo, es_mixto)
            velocidad_efectiva = vehiculo.velocidad_base * factor
            vehiculo.mover(velocidad_efectiva)

            if vehiculo.ha_llegado(self.config["longitud_via"]):
                vehiculo.tiempo_llegada = self.paso_actual

    def ejecutar_simulacion(self, es_mixto: bool) -> dict:
        """Ejecuta la simulacion completa y retorna metricas."""
        self.inicializar_vehiculos()
        self.paso_actual = 0

        for _ in range(self.config["pasos_simulacion"]):
            self.ejecutar_paso(es_mixto)

        return self.calcular_metricas()

    def calcular_metricas(self) -> dict:
        """Calcula las metricas de rendimiento."""
        tiempos_carros = []
        tiempos_motos = []

        for v in self.vehiculos:
            if v.tiempo_llegada is not None:
                tiempo = v.tiempo_llegada - v.tiempo_inicio
                if v.tipo == "carro":
                    tiempos_carros.append(tiempo)
                else:
                    tiempos_motos.append(tiempo)

        tiempo_carros = sum(tiempos_carros) / len(tiempos_carros) if tiempos_carros else float('inf')
        tiempo_motos = sum(tiempos_motos) / len(tiempos_motos) if tiempos_motos else float('inf')

        total = len(self.vehiculos)
        llegaron = len(tiempos_carros) + len(tiempos_motos)

        return {
            "tiempo_promedio_carros": tiempo_carros,
            "tiempo_promedio_motos": tiempo_motos,
            "carros_llegaron": len(tiempos_carros),
            "motos_llegaron": len(tiempos_motos),
            "eficiencia": (llegaron / total) * 100 if total > 0 else 0,
        }


# ============================================================================
# SIMULACION VISUAL (animacion en tiempo real)
# ============================================================================

class SimulacionVisual:
    """
    Simulacion visual con animacion en tiempo real.
    Muestra dos escenarios lado a lado con metricas de sostenibilidad.
    """

    def __init__(self, config: dict):
        self.config = config
        self.paso_actual = 0
        self.vehiculos_mixto: List[Vehiculo] = []
        self.vehiculos_exclusivo: List[Vehiculo] = []
        self.metricas = MetricasSostenibilidad()
        self.llegados_mixto = {"carros": 0, "motos": 0}
        self.llegados_exclusivo = {"carros": 0, "motos": 0}

    def inicializar_vehiculos(self) -> None:
        """Crea vehiculos para ambos escenarios."""
        random.seed(42)

        self.vehiculos_mixto = []
        self.vehiculos_exclusivo = []

        for i in range(self.config["num_carros"]):
            carril_mixto = random.choice([0, 1])
            carril_exclusivo = random.choice([0, 1])

            v_mixto = crear_vehiculo(i, "carro", self.config, carril_mixto)
            v_excl = crear_vehiculo(i, "carro", self.config, carril_exclusivo)
            v_excl.posicion = v_mixto.posicion

            self.vehiculos_mixto.append(v_mixto)
            self.vehiculos_exclusivo.append(v_excl)

        for i in range(self.config["num_motos"]):
            id_moto = i + self.config["num_carros"]

            v_mixto = crear_vehiculo(id_moto, "moto", self.config, random.choice([0, 1]))
            v_excl = crear_vehiculo(id_moto, "moto", self.config, 2)  # Carril exclusivo
            v_excl.posicion = v_mixto.posicion

            self.vehiculos_mixto.append(v_mixto)
            self.vehiculos_exclusivo.append(v_excl)

    def calcular_congestion(self, vehiculo: Vehiculo, vehiculos: List[Vehiculo], es_exclusivo: bool) -> float:
        """Calcula el factor de congestion."""
        dist_seguridad = self.config["distancia_seguridad"]

        vehiculo_adelante = None
        distancia_minima = float('inf')

        for v in vehiculos:
            if (v.id != vehiculo.id and
                v.carril == vehiculo.carril and
                v.tiempo_llegada is None and
                v.posicion > vehiculo.posicion):

                distancia = v.posicion - vehiculo.posicion
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    vehiculo_adelante = v

        if es_exclusivo and vehiculo.tipo == "moto":
            if vehiculo_adelante is None or distancia_minima > dist_seguridad:
                return 0.95
            return max(0.6, distancia_minima / dist_seguridad)

        if not es_exclusivo and vehiculo.tipo == "moto":
            for v in vehiculos:
                if (v.tipo == "carro" and
                    v.tiempo_llegada is None and
                    v.posicion > vehiculo.posicion and
                    v.posicion - vehiculo.posicion < dist_seguridad * 2):
                    return self.config["factor_congestion_mixto"]

            if vehiculo_adelante and distancia_minima < dist_seguridad * 1.5:
                return self.config["factor_congestion_mixto"] * 1.2

        if vehiculo_adelante is None or distancia_minima > dist_seguridad * 3:
            return 1.0

        if distancia_minima < dist_seguridad:
            return distancia_minima / dist_seguridad * 0.4
        return min(1.0, max(0.15, 0.4 + (distancia_minima - dist_seguridad) / (dist_seguridad * 2) * 0.5))

    def mover_vehiculos(self, vehiculos: List[Vehiculo], es_exclusivo: bool) -> None:
        """Mueve todos los vehiculos un paso."""
        longitud = self.config["longitud_via"]

        for v in vehiculos:
            if v.tiempo_llegada is not None:
                continue

            factor = self.calcular_congestion(v, vehiculos, es_exclusivo)
            v.mover(v.velocidad_base * factor)

            if v.posicion >= longitud:
                v.tiempo_llegada = self.paso_actual
                v.posicion = longitud

    def actualizar_metricas(self) -> None:
        """Actualiza las metricas de sostenibilidad."""
        km_motos = sum(
            v.distancia_recorrida / 1000
            for v in self.vehiculos_exclusivo
            if v.tipo == "moto"
        )

        co2_evitado = km_motos * self.config["emision_moto_gasolina"] / 1000
        self.metricas.co2_ahorrado_kg = co2_evitado
        self.metricas.arboles_equivalentes = co2_evitado / 22 * 365
        self.metricas.km_recorridos_electrico = km_motos

        consumo_elec = km_motos * self.config["consumo_moto_elec_kwh_km"]
        consumo_gas = km_motos * 0.03
        costo_elec = consumo_elec * self.config["costo_electricidad_kwh"]
        costo_gas = consumo_gas * self.config["costo_gasolina_litro"]

        self.metricas.dinero_ahorrado_usd = costo_gas - costo_elec

    def contar_llegados(self) -> None:
        """Cuenta vehiculos que han llegado."""
        self.llegados_mixto = {"carros": 0, "motos": 0}
        self.llegados_exclusivo = {"carros": 0, "motos": 0}

        for v in self.vehiculos_mixto:
            if v.tiempo_llegada is not None:
                key = "carros" if v.tipo == "carro" else "motos"
                self.llegados_mixto[key] += 1

        for v in self.vehiculos_exclusivo:
            if v.tiempo_llegada is not None:
                key = "carros" if v.tipo == "carro" else "motos"
                self.llegados_exclusivo[key] += 1

    def ejecutar_paso(self) -> None:
        """Ejecuta un paso de simulacion."""
        self.paso_actual += 1
        self.mover_vehiculos(self.vehiculos_mixto, es_exclusivo=False)
        self.mover_vehiculos(self.vehiculos_exclusivo, es_exclusivo=True)
        self.contar_llegados()
        self.actualizar_metricas()


# ============================================================================
# VISUALIZADOR
# ============================================================================

class Visualizador:
    """Crea la interfaz visual de la simulacion."""

    def __init__(self, simulacion: SimulacionVisual):
        self.sim = simulacion
        self.fig = None
        self.axes = {}

    def crear_interfaz(self) -> plt.Figure:
        """Crea la estructura visual completa."""
        self.fig = plt.figure(figsize=(20, 12))
        self.fig.patch.set_facecolor('#0a0a1a')

        self.fig.suptitle(
            'SIMULACION DE MOVILIDAD SOSTENIBLE - Carriles Exclusivos para Motos Electricas',
            fontsize=16, fontweight='bold', color='white', y=0.98
        )

        gs = self.fig.add_gridspec(3, 2, height_ratios=[4, 4, 1.5],
                                   hspace=0.15, wspace=0.08,
                                   left=0.02, right=0.98, top=0.94, bottom=0.03)

        self.axes['via_mixto'] = self.fig.add_subplot(gs[0, :])
        self.axes['via_exclusivo'] = self.fig.add_subplot(gs[1, :])
        self.axes['metricas_tiempo'] = self.fig.add_subplot(gs[2, 0])
        self.axes['metricas_sostenibilidad'] = self.fig.add_subplot(gs[2, 1])

        try:
            manager = plt.get_current_fig_manager()
            manager.full_screen_toggle()
        except (AttributeError, NotImplementedError):
            pass

        return self.fig

    def dibujar_via(self, ax, vehiculos: List[Vehiculo], es_exclusivo: bool) -> None:
        """Dibuja la via con carriles y vehiculos."""
        ax.clear()
        ax.set_facecolor('#0d1117')

        longitud = self.sim.config["longitud_via"]
        ax.set_xlim(-20, longitud + 100)
        ax.set_ylim(-10, 32)
        ax.axis('off')

        # Titulo
        if es_exclusivo:
            ax.text(longitud/2, 28, 'CON CARRIL EXCLUSIVO - Motos ELECTRICAS fluyen libres',
                   ha='center', fontsize=14, fontweight='bold', color='#00ff00')
        else:
            ax.text(longitud/2, 28, 'SIN CARRIL EXCLUSIVO - Motos bloqueadas por carros',
                   ha='center', fontsize=14, fontweight='bold', color='#ff4444')

        y_base = 2
        ancho_carril = 7
        ancho_carril_motos = 5

        if es_exclusivo:
            # 3 carriles
            for i in range(2):
                carril = patches.Rectangle(
                    (0, y_base + i * ancho_carril), longitud, ancho_carril,
                    facecolor='#2c3e50', edgecolor='white', linewidth=2
                )
                ax.add_patch(carril)

            carril_motos = patches.Rectangle(
                (0, y_base + 2 * ancho_carril), longitud, ancho_carril_motos,
                facecolor='#0a4d1c', edgecolor='#00FF00', linewidth=4
            )
            ax.add_patch(carril_motos)

            ax.text(longitud/2, y_base + 2 * ancho_carril + ancho_carril_motos/2,
                   'CARRIL EXCLUSIVO MOTOS ELECTRICAS',
                   ha='center', va='center', fontsize=11, color='#00FF00', fontweight='bold')

            altura_total = ancho_carril * 2 + ancho_carril_motos
        else:
            # 2 carriles mixtos
            for i in range(2):
                carril = patches.Rectangle(
                    (0, y_base + i * ancho_carril), longitud, ancho_carril,
                    facecolor='#2c3e50', edgecolor='white', linewidth=2
                )
                ax.add_patch(carril)

            altura_total = ancho_carril * 2

        # Meta
        ax.add_patch(patches.Rectangle(
            (longitud-12, y_base-2), 12, altura_total+4,
            facecolor='#27ae60', alpha=0.9
        ))
        ax.text(longitud-6, y_base + altura_total/2, 'META',
               ha='center', va='center', fontsize=12, color='white', fontweight='bold')

        # Dibujar vehiculos
        for v in vehiculos:
            if v.tiempo_llegada is not None:
                continue

            if es_exclusivo and v.carril == 2:
                y = y_base + ancho_carril * 2 + ancho_carril_motos/2
            else:
                y = y_base + v.carril * ancho_carril + ancho_carril/2

            x = v.posicion

            if v.tipo == "carro":
                ax.add_patch(patches.FancyBboxPatch(
                    (x - 10, y - 2.5), 20, 5,
                    boxstyle="round,pad=0.3",
                    facecolor=v.color, edgecolor='black', linewidth=2
                ))
            else:
                color = '#00FF00' if es_exclusivo else '#FF6B35'
                ax.add_patch(patches.Circle((x, y), 3,
                            facecolor=color, edgecolor='black', linewidth=2))

        # Contador
        llegados = self.sim.llegados_exclusivo if es_exclusivo else self.sim.llegados_mixto
        ax.text(50, -5, f"Carros: {llegados['carros']}/{self.sim.config['num_carros']}",
               fontsize=11, color='#3498db', fontweight='bold')
        ax.text(200, -5, f"Motos: {llegados['motos']}/{self.sim.config['num_motos']}",
               fontsize=11, color='#27ae60' if es_exclusivo else '#FF6B35', fontweight='bold')

    def dibujar_metricas_tiempo(self, ax) -> None:
        """Dibuja las metricas de tiempo."""
        ax.clear()
        ax.set_facecolor('#0d1117')
        ax.axis('off')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)

        ax.text(5, 9, 'TIEMPOS DE VIAJE', ha='center', fontsize=11,
               fontweight='bold', color='white')

        def tiempo_promedio(vehiculos, tipo):
            tiempos = [v.tiempo_llegada for v in vehiculos
                      if v.tiempo_llegada and v.tipo == tipo]
            return sum(tiempos)/len(tiempos) if tiempos else 0

        t_moto_mix = tiempo_promedio(self.sim.vehiculos_mixto, "moto")
        t_moto_exc = tiempo_promedio(self.sim.vehiculos_exclusivo, "moto")

        ax.text(2, 6, f"Motos (Mixto): {t_moto_mix:.0f}", fontsize=10, color='#e74c3c')
        ax.text(2, 4, f"Motos (Exclusivo): {t_moto_exc:.0f}", fontsize=10, color='#27ae60')

        if t_moto_mix > 0 and t_moto_exc > 0:
            mejora = (t_moto_mix - t_moto_exc) / t_moto_mix * 100
            ax.text(5, 2, f"Mejora: {mejora:.1f}%", ha='center',
                   fontsize=12, color='#27ae60', fontweight='bold')

    def dibujar_metricas_sostenibilidad(self, ax) -> None:
        """Dibuja el panel de sostenibilidad."""
        ax.clear()
        ax.set_facecolor('#0d1117')
        ax.axis('off')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)

        ax.text(5, 9, 'IMPACTO AMBIENTAL', ha='center', fontsize=11,
               fontweight='bold', color='#27ae60')

        m = self.sim.metricas
        ax.text(1, 7, f"CO2 Evitado: {m.co2_ahorrado_kg:.2f} kg", fontsize=10, color='#27ae60')
        ax.text(1, 5, f"Arboles equiv.: {m.arboles_equivalentes:.1f}/year", fontsize=10, color='#2ecc71')
        ax.text(1, 3, f"Ahorro: ${m.dinero_ahorrado_usd:.2f}", fontsize=10, color='#f39c12')
        ax.text(1, 1, f"Km electricos: {m.km_recorridos_electrico:.1f}", fontsize=10, color='#3498db')

    def actualizar_frame(self, frame) -> list:
        """Actualiza cada frame de la animacion."""
        self.sim.ejecutar_paso()

        self.dibujar_via(self.axes['via_mixto'], self.sim.vehiculos_mixto, False)
        self.dibujar_via(self.axes['via_exclusivo'], self.sim.vehiculos_exclusivo, True)
        self.dibujar_metricas_tiempo(self.axes['metricas_tiempo'])
        self.dibujar_metricas_sostenibilidad(self.axes['metricas_sostenibilidad'])

        return []

    def ejecutar(self) -> None:
        """Ejecuta la animacion completa."""
        self.crear_interfaz()
        self.sim.inicializar_vehiculos()
        self.actualizar_frame(0)

        anim = animation.FuncAnimation(
            self.fig,
            self.actualizar_frame,
            frames=self.sim.config["pasos_simulacion"],
            interval=self.sim.config["intervalo_animacion_ms"],
            blit=False,
            repeat=False
        )

        plt.show()


# ============================================================================
# FUNCIONES DE EJECUCION
# ============================================================================

def ejecutar_simulaciones_multiples(config: dict) -> Tuple[dict, dict]:
    """Ejecuta multiples simulaciones y promedia resultados."""
    resultados_mixto = {"tiempo_promedio_carros": [], "tiempo_promedio_motos": [], "eficiencia": []}
    resultados_exclusivo = {"tiempo_promedio_carros": [], "tiempo_promedio_motos": [], "eficiencia": []}

    print(f"Ejecutando {config['num_simulaciones']} simulaciones...")

    for i in range(config["num_simulaciones"]):
        sim = SimulacionBasica(config)

        r_mixto = sim.ejecutar_simulacion(es_mixto=True)
        resultados_mixto["tiempo_promedio_carros"].append(r_mixto["tiempo_promedio_carros"])
        resultados_mixto["tiempo_promedio_motos"].append(r_mixto["tiempo_promedio_motos"])
        resultados_mixto["eficiencia"].append(r_mixto["eficiencia"])

        r_excl = sim.ejecutar_simulacion(es_mixto=False)
        resultados_exclusivo["tiempo_promedio_carros"].append(r_excl["tiempo_promedio_carros"])
        resultados_exclusivo["tiempo_promedio_motos"].append(r_excl["tiempo_promedio_motos"])
        resultados_exclusivo["eficiencia"].append(r_excl["eficiencia"])

        print(f"  Simulacion {i+1}/{config['num_simulaciones']} completada")

    def promediar(lista):
        validos = [v for v in lista if v != float('inf')]
        return sum(validos) / len(validos) if validos else 0

    return (
        {k: promediar(v) for k, v in resultados_mixto.items()},
        {k: promediar(v) for k, v in resultados_exclusivo.items()}
    )


def crear_graficas(mixto: dict, exclusivo: dict) -> None:
    """Crea graficas comparativas."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Comparacion: Trafico Mixto vs Carril Exclusivo', fontsize=14, fontweight='bold')

    colores = ['#e74c3c', '#27ae60']
    labels = ['Mixto', 'Exclusivo']

    # Grafica 1: Tiempos
    ax1 = axes[0]
    tiempos = [
        mixto["tiempo_promedio_carros"], exclusivo["tiempo_promedio_carros"],
        mixto["tiempo_promedio_motos"], exclusivo["tiempo_promedio_motos"]
    ]
    ax1.bar([0, 1, 2, 3], tiempos, color=[colores[0], colores[1]]*2)
    ax1.set_xticks([0, 1, 2, 3])
    ax1.set_xticklabels(['Carros\nMixto', 'Carros\nExcl', 'Motos\nMixto', 'Motos\nExcl'])
    ax1.set_ylabel('Tiempo promedio')
    ax1.set_title('Tiempos de Viaje')

    # Grafica 2: Motos
    ax2 = axes[1]
    ax2.bar(labels, [mixto["tiempo_promedio_motos"], exclusivo["tiempo_promedio_motos"]], color=colores)
    ax2.set_ylabel('Tiempo promedio')
    ax2.set_title('Tiempo de Motos')

    if mixto["tiempo_promedio_motos"] > 0:
        mejora = (mixto["tiempo_promedio_motos"] - exclusivo["tiempo_promedio_motos"]) / mixto["tiempo_promedio_motos"] * 100
        ax2.text(0.5, exclusivo["tiempo_promedio_motos"] * 1.1, f'{mejora:.1f}% menos',
                ha='center', color='green', fontweight='bold')

    # Grafica 3: Eficiencia
    ax3 = axes[2]
    ax3.bar(labels, [mixto["eficiencia"], exclusivo["eficiencia"]], color=colores)
    ax3.set_ylabel('Eficiencia (%)')
    ax3.set_title('Eficiencia del Trafico')
    ax3.set_ylim(0, 110)

    plt.tight_layout()
    plt.savefig('resultados_simulacion.png', dpi=150, bbox_inches='tight')
    print("Grafica guardada como 'resultados_simulacion.png'")
    plt.show()


def imprimir_resumen(mixto: dict, exclusivo: dict) -> None:
    """Imprime resumen de resultados."""
    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)

    print("\nTRAFICO MIXTO:")
    print(f"   Tiempo carros: {mixto['tiempo_promedio_carros']:.1f}")
    print(f"   Tiempo motos:  {mixto['tiempo_promedio_motos']:.1f}")
    print(f"   Eficiencia:    {mixto['eficiencia']:.1f}%")

    print("\nCARRIL EXCLUSIVO:")
    print(f"   Tiempo carros: {exclusivo['tiempo_promedio_carros']:.1f}")
    print(f"   Tiempo motos:  {exclusivo['tiempo_promedio_motos']:.1f}")
    print(f"   Eficiencia:    {exclusivo['eficiencia']:.1f}%")

    if mixto['tiempo_promedio_motos'] > 0:
        mejora = (mixto['tiempo_promedio_motos'] - exclusivo['tiempo_promedio_motos']) / mixto['tiempo_promedio_motos'] * 100
        print(f"\nMEJORA PARA MOTOS: {mejora:.1f}% menos tiempo")

    print("="*60)


# ============================================================================
# FUNCION PRINCIPAL
# ============================================================================

def main():
    """Funcion principal."""
    print("="*60)
    print("SIMULACION DE TRAFICO")
    print("Carriles Exclusivos para Motocicletas Electricas")
    print("="*60)

    print(f"\nConfiguracion:")
    print(f"   Carros: {CONFIG['num_carros']}")
    print(f"   Motos:  {CONFIG['num_motos']}")
    print(f"   Via:    {CONFIG['longitud_via']} unidades")

    print("\nOpciones:")
    print("  1. Simulacion basica (graficas)")
    print("  2. Simulacion visual (animacion)")
    print("  3. Ambas")

    opcion = input("\nElige opcion (1/2/3): ").strip()

    if opcion == "1":
        mixto, exclusivo = ejecutar_simulaciones_multiples(CONFIG)
        imprimir_resumen(mixto, exclusivo)
        crear_graficas(mixto, exclusivo)

    elif opcion == "2":
        print("\nIniciando simulacion visual...")
        sim = SimulacionVisual(CONFIG)
        viz = Visualizador(sim)
        viz.ejecutar()

    else:
        mixto, exclusivo = ejecutar_simulaciones_multiples(CONFIG)
        imprimir_resumen(mixto, exclusivo)
        crear_graficas(mixto, exclusivo)

        print("\nIniciando simulacion visual...")
        sim = SimulacionVisual(CONFIG)
        viz = Visualizador(sim)
        viz.ejecutar()

    print("\nSimulacion completada.")


if __name__ == "__main__":
    main()
