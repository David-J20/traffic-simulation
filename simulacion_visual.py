"""
================================================================================
SIMULACIÓN VISUAL DE TRÁFICO - CARRILES EXCLUSIVOS PARA MOTOS ELÉCTRICAS
================================================================================

Visualización interactiva que muestra:
- Vista superior de la vía con carriles
- Vehículos en movimiento (carros y motos eléctricas)
- Métricas de sostenibilidad y medio ambiente
- Comparación en tiempo real de ambos escenarios

Enfoque: Sostenibilidad y movilidad eléctrica
================================================================================
"""

import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import numpy as np
from dataclasses import dataclass
from typing import List, Optional

# ============================================================================
# PARÁMETROS DE CONFIGURACIÓN
# ============================================================================

CONFIG = {
    # Vehículos - MÁS para simular tráfico pesado real
    "num_carros": 25,
    "num_motos_electricas": 18,

    # Velocidades (km/h conceptuales, escalados para simulación)
    # Carros más lentos, motos más rápidas = diferencia más notable
    "velocidad_carro_min": 15,
    "velocidad_carro_max": 35,
    "velocidad_moto_min": 50,
    "velocidad_moto_max": 75,

    # Vía
    "longitud_via_metros": 500,      # Vía más larga para ver mejor el efecto
    "ancho_carril_metros": 3.5,      # Ancho estándar de carril

    # Simulación
    "pasos_simulacion": 250,
    "intervalo_animacion_ms": 50,    # Más rápido para ver el efecto

    # Congestión - MUY ALTA para simular tráfico real
    "distancia_seguridad": 35,       # Metros entre vehículos
    "factor_congestion_mixto": 0.25, # MUY alto impacto en tráfico mixto (motos casi bloqueadas)

    # === DATOS DE SOSTENIBILIDAD ===
    # Emisiones promedio (gramos CO2 por km)
    "emision_carro_gasolina": 120,   # Carro promedio
    "emision_moto_gasolina": 72,     # Moto convencional
    "emision_moto_electrica": 0,     # Moto eléctrica (0 directo)

    # Consumo energético
    "consumo_carro_litros_km": 0.08,     # Litros/km
    "consumo_moto_elec_kwh_km": 0.025,   # kWh/km (muy eficiente)

    # Costo aproximado
    "costo_gasolina_litro": 1.2,         # USD/litro
    "costo_electricidad_kwh": 0.15,      # USD/kWh
}


# ============================================================================
# CLASES DE VEHÍCULOS
# ============================================================================

@dataclass
class Vehiculo:
    """Representa un vehículo en la simulación."""
    id: int
    tipo: str                    # 'carro' o 'moto_electrica'
    posicion: float              # Posición en metros
    carril: int                  # 0, 1, 2 (índice del carril)
    velocidad_base: float        # Velocidad sin congestión
    velocidad_actual: float = 0
    color: str = ""
    tiempo_inicio: int = 0
    tiempo_llegada: Optional[int] = None
    distancia_recorrida: float = 0

    def __post_init__(self):
        self.velocidad_actual = self.velocidad_base
        if not self.color:
            if self.tipo == "carro":
                # Colores variados para carros
                self.color = random.choice([
                    '#3498db',  # Azul
                    '#2c3e50',  # Azul oscuro
                    '#7f8c8d',  # Gris
                    '#c0392b',  # Rojo oscuro
                    '#8e44ad',  # Púrpura
                ])
            else:
                # Motos eléctricas en verde (sostenibilidad)
                self.color = '#27ae60'  # Verde


@dataclass
class MetricasSostenibilidad:
    """Métricas ambientales de la simulación."""
    co2_ahorrado_kg: float = 0
    energia_ahorrada_kwh: float = 0
    dinero_ahorrado_usd: float = 0
    arboles_equivalentes: float = 0  # CO2 absorbido por árboles
    km_recorridos_electrico: float = 0
    km_recorridos_gasolina: float = 0


# ============================================================================
# CLASE PRINCIPAL DE SIMULACIÓN VISUAL
# ============================================================================

class SimulacionVisualTrafico:
    """
    Simulación visual de tráfico con enfoque en sostenibilidad.
    Muestra dos escenarios lado a lado:
    - Izquierda: Tráfico mixto (todos comparten carriles)
    - Derecha: Carril exclusivo para motos eléctricas
    """

    def __init__(self, config: dict):
        self.config = config
        self.paso_actual = 0

        # Vehículos para cada escenario
        self.vehiculos_mixto: List[Vehiculo] = []
        self.vehiculos_exclusivo: List[Vehiculo] = []

        # Métricas
        self.metricas_mixto = MetricasSostenibilidad()
        self.metricas_exclusivo = MetricasSostenibilidad()

        # Contadores de llegada
        self.llegados_mixto = {"carros": 0, "motos": 0}
        self.llegados_exclusivo = {"carros": 0, "motos": 0}

        # Tiempos acumulados
        self.tiempos_mixto = {"carros": [], "motos": []}
        self.tiempos_exclusivo = {"carros": [], "motos": []}

    def inicializar_vehiculos(self):
        """Crea los vehículos con posiciones iniciales."""
        random.seed(42)  # Semilla fija para reproducibilidad

        self.vehiculos_mixto = []
        self.vehiculos_exclusivo = []

        longitud = self.config["longitud_via_metros"]

        # Crear carros
        for i in range(self.config["num_carros"]):
            velocidad = random.uniform(
                self.config["velocidad_carro_min"],
                self.config["velocidad_carro_max"]
            ) / 10  # Escalar para la simulación

            # Posición inicial distribuida
            posicion = random.uniform(0, longitud * 0.3)

            # Para mixto: carriles 0 y 1 (comparten con motos)
            carril_mixto = random.choice([0, 1])

            # Para exclusivo: carriles 0 y 1 (solo carros, el 2 es para motos)
            carril_exclusivo = random.choice([0, 1])

            self.vehiculos_mixto.append(Vehiculo(
                id=i, tipo="carro", posicion=posicion,
                carril=carril_mixto, velocidad_base=velocidad
            ))

            self.vehiculos_exclusivo.append(Vehiculo(
                id=i, tipo="carro", posicion=posicion,
                carril=carril_exclusivo, velocidad_base=velocidad
            ))

        # Crear motos eléctricas
        for i in range(self.config["num_motos_electricas"]):
            velocidad = random.uniform(
                self.config["velocidad_moto_min"],
                self.config["velocidad_moto_max"]
            ) / 10

            posicion = random.uniform(0, longitud * 0.3)

            # Para mixto: comparten carriles 0 y 1 con carros
            carril_mixto = random.choice([0, 1])

            # Para exclusivo: carril 2 (tercer carril, solo motos)
            carril_exclusivo = 2

            id_moto = i + self.config["num_carros"]

            self.vehiculos_mixto.append(Vehiculo(
                id=id_moto, tipo="moto_electrica", posicion=posicion,
                carril=carril_mixto, velocidad_base=velocidad
            ))

            self.vehiculos_exclusivo.append(Vehiculo(
                id=id_moto, tipo="moto_electrica", posicion=posicion,
                carril=carril_exclusivo, velocidad_base=velocidad
            ))

    def calcular_congestion(self, vehiculo: Vehiculo,
                           todos_vehiculos: List[Vehiculo],
                           es_exclusivo: bool) -> float:
        """
        Calcula el factor de congestión basado en vehículos cercanos.

        REALISTA: En tráfico mixto, las motos quedan MUY bloqueadas por carros.
        En carril exclusivo, las motos fluyen casi libremente.
        """
        dist_seguridad = self.config["distancia_seguridad"]

        # Buscar vehículo más cercano adelante en el mismo carril
        vehiculo_adelante = None
        distancia_minima = float('inf')

        for v in todos_vehiculos:
            if (v.id != vehiculo.id and
                v.carril == vehiculo.carril and
                v.tiempo_llegada is None and
                v.posicion > vehiculo.posicion):

                distancia = v.posicion - vehiculo.posicion
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    vehiculo_adelante = v

        # === CARRIL EXCLUSIVO: Motos fluyen libremente ===
        if es_exclusivo and vehiculo.tipo == "moto_electrica":
            # Solo se frenan si hay otra moto MUY cerca
            if vehiculo_adelante is None or distancia_minima > dist_seguridad:
                return 0.95  # Casi velocidad máxima
            else:
                return max(0.6, distancia_minima / dist_seguridad)

        # === TRÁFICO MIXTO: Motos MUY bloqueadas por carros ===
        if not es_exclusivo and vehiculo.tipo == "moto_electrica":
            # Buscar CUALQUIER carro adelante (no solo en mismo carril)
            for v in todos_vehiculos:
                if (v.tipo == "carro" and
                    v.tiempo_llegada is None and
                    v.posicion > vehiculo.posicion and
                    v.posicion - vehiculo.posicion < dist_seguridad * 2):
                    # Moto queda atrapada detrás del carro - MUY lento
                    return self.config["factor_congestion_mixto"]  # ~25% velocidad

            # Si hay vehículo adelante cerca
            if vehiculo_adelante and distancia_minima < dist_seguridad * 1.5:
                return self.config["factor_congestion_mixto"] * 1.2

        # === CARROS: Congestión normal ===
        if vehiculo_adelante is None or distancia_minima > dist_seguridad * 3:
            return 1.0

        # Factor basado en distancia para carros
        if distancia_minima < dist_seguridad:
            factor = distancia_minima / dist_seguridad * 0.4
        else:
            factor = 0.4 + (distancia_minima - dist_seguridad) / (dist_seguridad * 2) * 0.5

        return min(1.0, max(0.15, factor))

    def mover_vehiculos(self, vehiculos: List[Vehiculo], es_exclusivo: bool):
        """Mueve todos los vehículos un paso de tiempo."""
        longitud = self.config["longitud_via_metros"]

        for vehiculo in vehiculos:
            if vehiculo.tiempo_llegada is not None:
                continue

            # Calcular velocidad efectiva
            factor = self.calcular_congestion(vehiculo, vehiculos, es_exclusivo)
            velocidad_efectiva = vehiculo.velocidad_base * factor
            vehiculo.velocidad_actual = velocidad_efectiva

            # Mover
            vehiculo.posicion += velocidad_efectiva
            vehiculo.distancia_recorrida += velocidad_efectiva

            # Verificar llegada
            if vehiculo.posicion >= longitud:
                vehiculo.tiempo_llegada = self.paso_actual
                vehiculo.posicion = longitud

    def actualizar_metricas(self):
        """Actualiza las métricas de sostenibilidad."""
        # Calcular distancias recorridas
        km_motos_mixto = sum(
            v.distancia_recorrida / 1000
            for v in self.vehiculos_mixto
            if v.tipo == "moto_electrica"
        )
        km_motos_exclusivo = sum(
            v.distancia_recorrida / 1000
            for v in self.vehiculos_exclusivo
            if v.tipo == "moto_electrica"
        )
        km_carros_mixto = sum(
            v.distancia_recorrida / 1000
            for v in self.vehiculos_mixto
            if v.tipo == "carro"
        )

        # CO2 ahorrado por usar motos eléctricas vs motos gasolina
        # (comparando con lo que emitirían si fueran motos de gasolina)
        co2_si_fuera_gasolina = km_motos_exclusivo * self.config["emision_moto_gasolina"] / 1000
        self.metricas_exclusivo.co2_ahorrado_kg = co2_si_fuera_gasolina

        # Árboles equivalentes (un árbol absorbe ~22kg CO2/año)
        self.metricas_exclusivo.arboles_equivalentes = co2_si_fuera_gasolina / 22 * 365

        # Energía y dinero
        self.metricas_exclusivo.km_recorridos_electrico = km_motos_exclusivo
        consumo_electrico = km_motos_exclusivo * self.config["consumo_moto_elec_kwh_km"]
        costo_electrico = consumo_electrico * self.config["costo_electricidad_kwh"]

        # Si usaran gasolina
        consumo_gasolina = km_motos_exclusivo * 0.03  # 3L/100km para moto
        costo_gasolina = consumo_gasolina * self.config["costo_gasolina_litro"]

        self.metricas_exclusivo.dinero_ahorrado_usd = costo_gasolina - costo_electrico
        self.metricas_exclusivo.energia_ahorrada_kwh = consumo_gasolina * 9.7 - consumo_electrico

    def contar_llegados(self):
        """Cuenta vehículos que han llegado a la meta."""
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

    def ejecutar_paso(self):
        """Ejecuta un paso de simulación."""
        self.paso_actual += 1
        self.mover_vehiculos(self.vehiculos_mixto, es_exclusivo=False)
        self.mover_vehiculos(self.vehiculos_exclusivo, es_exclusivo=True)
        self.contar_llegados()
        self.actualizar_metricas()


# ============================================================================
# VISUALIZACIÓN
# ============================================================================

class VisualizadorTrafico:
    """Crea la interfaz visual de la simulación."""

    def __init__(self, simulacion: SimulacionVisualTrafico):
        self.sim = simulacion
        self.fig = None
        self.axes = {}

    def crear_interfaz(self):
        """Crea la estructura visual completa."""
        # Figura MUY grande - pantalla completa
        self.fig = plt.figure(figsize=(24, 14))
        self.fig.patch.set_facecolor('#0a0a1a')  # Fondo oscuro elegante

        # Título principal
        self.fig.suptitle(
            '🔋 SIMULACIÓN DE MOVILIDAD SOSTENIBLE - Carriles Exclusivos para Motos Eléctricas',
            fontsize=18, fontweight='bold', color='white', y=0.98
        )

        # Grid layout - VÍAS DOMINAN (70% del espacio)
        gs = self.fig.add_gridspec(3, 2, height_ratios=[4, 4, 1.5],
                                   hspace=0.15, wspace=0.08,
                                   left=0.02, right=0.98, top=0.94, bottom=0.03)

        # Vías de tráfico GRANDES (arriba - ocupan más espacio)
        self.axes['via_mixto'] = self.fig.add_subplot(gs[0, :])  # Fila completa
        self.axes['via_exclusivo'] = self.fig.add_subplot(gs[1, :])  # Fila completa

        # Métricas compactas (abajo)
        self.axes['metricas_tiempo'] = self.fig.add_subplot(gs[2, 0])
        self.axes['metricas_sostenibilidad'] = self.fig.add_subplot(gs[2, 1])

        # Configurar cada panel
        self._configurar_vias()
        self._configurar_metricas()

        # Maximizar ventana
        try:
            manager = plt.get_current_fig_manager()
            manager.full_screen_toggle()
        except (AttributeError, NotImplementedError):
            # Algunos backends de matplotlib no soportan full_screen_toggle
            pass

        return self.fig

    def _configurar_vias(self):
        """Configura los paneles de las vías - GRANDES Y VISIBLES."""
        longitud = self.sim.config["longitud_via_metros"]

        for nombre, titulo in [
            ('via_mixto', '❌ SIN CARRIL EXCLUSIVO - Motos GASOLINA 🛵💨 bloqueadas por carros'),
            ('via_exclusivo', '✅ CON CARRIL EXCLUSIVO - Motos ELÉCTRICAS ⚡ fluyen libres en 3er carril')
        ]:
            ax = self.axes[nombre]
            ax.set_facecolor('#0d1117')
            ax.set_xlim(-20, longitud + 100)
            ax.set_ylim(-10, 32)
            ax.axis('off')

            # Título del panel - grande y claro
            color_titulo = '#ff4444' if 'mixto' in nombre else '#00ff00'
            ax.text(longitud/2, 28, titulo, ha='center', va='center',
                   fontsize=15, fontweight='bold', color=color_titulo)

    def _configurar_metricas(self):
        """Configura los paneles de métricas - compactos."""
        for nombre in ['metricas_tiempo', 'metricas_sostenibilidad']:
            ax = self.axes[nombre]
            ax.set_facecolor('#0d1117')
            ax.axis('off')

    def dibujar_via(self, ax, vehiculos: List[Vehiculo], es_exclusivo: bool):
        """Dibuja la vía con carriles y vehículos - GRANDE Y VISIBLE."""
        ax.clear()
        ax.set_facecolor('#0d1117')

        longitud = self.sim.config["longitud_via_metros"]
        ax.set_xlim(-20, longitud + 100)
        ax.set_ylim(-10, 32)
        ax.axis('off')

        # Título grande y claro
        if es_exclusivo:
            ax.text(longitud/2, 28, '✅ CON CARRIL EXCLUSIVO - Motos ELÉCTRICAS ⚡ fluyen libres en 3er carril',
                   ha='center', fontsize=15, fontweight='bold', color='#00ff00')
        else:
            ax.text(longitud/2, 28, '❌ SIN CARRIL EXCLUSIVO - Motos GASOLINA 🛵💨 bloqueadas por carros',
                   ha='center', fontsize=15, fontweight='bold', color='#ff4444')

        # === DIBUJAR CARRILES ===
        y_base = 2
        ancho_carril = 7  # Carriles para carros
        ancho_carril_motos = 5  # Carril más delgado para motos

        if es_exclusivo:
            # ========== ESCENARIO EXCLUSIVO: 3 CARRILES ==========
            # Carril 0 (carros - abajo)
            carril0 = patches.Rectangle(
                (0, y_base), longitud, ancho_carril,
                facecolor='#2c3e50', edgecolor='white', linewidth=2
            )
            ax.add_patch(carril0)

            # Carril 1 (carros - medio)
            carril1 = patches.Rectangle(
                (0, y_base + ancho_carril), longitud, ancho_carril,
                facecolor='#2c3e50', edgecolor='white', linewidth=2
            )
            ax.add_patch(carril1)

            # Carril 2 (MOTOS ELÉCTRICAS - arriba, más delgado y verde)
            carril2 = patches.Rectangle(
                (0, y_base + ancho_carril * 2), longitud, ancho_carril_motos,
                facecolor='#0a4d1c', edgecolor='#00FF00', linewidth=5
            )
            ax.add_patch(carril2)

            # Texto en carril de motos
            ax.text(longitud/2, y_base + ancho_carril * 2 + ancho_carril_motos/2,
                   '⚡ CARRIL EXCLUSIVO MOTOS ELÉCTRICAS ⚡',
                   ha='center', va='center', fontsize=12, color='#00FF00',
                   fontweight='bold', alpha=0.8)

            # Línea entre carriles de carros (blanca punteada)
            ax.plot([0, longitud], [y_base + ancho_carril, y_base + ancho_carril],
                   color='white', linewidth=3, linestyle='--', dashes=(15, 8))

            # Línea doble amarilla entre carros y motos (separación fuerte)
            linea_sep = y_base + ancho_carril * 2
            ax.plot([0, longitud], [linea_sep - 0.4, linea_sep - 0.4],
                   color='#FFD700', linewidth=6, linestyle='-')
            ax.plot([0, longitud], [linea_sep + 0.4, linea_sep + 0.4],
                   color='#FFD700', linewidth=6, linestyle='-')

            # Etiquetas laterales
            ax.text(longitud + 15, y_base + ancho_carril * 2 + ancho_carril_motos/2,
                   '⚡ MOTOS\nELÉCTRICAS',
                   fontsize=12, color='#00FF00', va='center', fontweight='bold')
            ax.text(longitud + 15, y_base + ancho_carril,
                   '🚗 CARROS\n(2 carriles)',
                   fontsize=12, color='#3498db', va='center', fontweight='bold')

            # Altura total para meta/inicio
            altura_total = ancho_carril * 2 + ancho_carril_motos

        else:
            # ========== ESCENARIO MIXTO: 2 CARRILES ==========
            # Carril 0 (mixto - abajo)
            carril0 = patches.Rectangle(
                (0, y_base), longitud, ancho_carril,
                facecolor='#2c3e50', edgecolor='white', linewidth=2
            )
            ax.add_patch(carril0)

            # Carril 1 (mixto - arriba)
            carril1 = patches.Rectangle(
                (0, y_base + ancho_carril), longitud, ancho_carril,
                facecolor='#2c3e50', edgecolor='white', linewidth=2
            )
            ax.add_patch(carril1)

            # Línea entre carriles (blanca punteada)
            ax.plot([0, longitud], [y_base + ancho_carril, y_base + ancho_carril],
                   color='white', linewidth=3, linestyle='--', dashes=(15, 8))

            # Etiqueta lateral
            ax.text(longitud + 15, y_base + ancho_carril,
                   '🚗🛵 MIXTO\nCarros + Motos\nGasolina',
                   fontsize=11, color='#ff6666', va='center', fontweight='bold')

            # Altura total para meta/inicio
            altura_total = ancho_carril * 2

        # Líneas de borde superior e inferior
        for xi in range(0, int(longitud), 40):
            ax.plot([xi, xi+20], [y_base, y_base], color='white',
                   linewidth=2, alpha=0.6)
            ax.plot([xi, xi+20], [y_base + altura_total, y_base + altura_total],
                   color='white', linewidth=2, alpha=0.6)

        # META
        ax.add_patch(patches.Rectangle(
            (longitud-12, y_base-2), 12, altura_total+4,
            facecolor='#27ae60', alpha=0.9
        ))
        ax.text(longitud-6, y_base + altura_total/2, '🏁\nMETA',
               ha='center', va='center', fontsize=14, color='white',
               fontweight='bold')

        # INICIO
        ax.add_patch(patches.Rectangle(
            (0, y_base-2), 8, altura_total+4,
            facecolor='#3498db', alpha=0.9
        ))
        ax.text(4, y_base + altura_total/2, '🚦\nINICIO',
               ha='center', va='center', fontsize=12, color='white',
               fontweight='bold')

        # === DIBUJAR VEHÍCULOS (MÁS GRANDES) ===
        for v in vehiculos:
            if v.tiempo_llegada is not None:
                continue  # Ya llegó

            # Posición Y según carril (centrado en el carril)
            if es_exclusivo and v.carril == 2:
                # Carril de motos (más delgado, arriba)
                y = y_base + ancho_carril * 2 + ancho_carril_motos/2
            else:
                # Carriles de carros (o mixto)
                y = y_base + v.carril * ancho_carril + ancho_carril/2
            x = v.posicion

            if v.tipo == "carro":
                # ========== CARRO: Rectángulo GRANDE con detalles ==========
                ancho_carro = 22
                alto_carro = 5.5

                # Sombra del carro
                ax.add_patch(patches.FancyBboxPatch(
                    (x - ancho_carro/2 + 1.5, y - alto_carro/2 - 0.8),
                    ancho_carro, alto_carro,
                    boxstyle="round,pad=0.4",
                    facecolor='black', alpha=0.4
                ))

                # Cuerpo principal del carro
                ax.add_patch(patches.FancyBboxPatch(
                    (x - ancho_carro/2, y - alto_carro/2),
                    ancho_carro, alto_carro,
                    boxstyle="round,pad=0.4",
                    facecolor=v.color, edgecolor='#000000', linewidth=3
                ))

                # Ventanas grandes
                ax.add_patch(patches.FancyBboxPatch(
                    (x - 5, y - 1.5), 10, 3,
                    boxstyle="round,pad=0.15",
                    facecolor='#87CEEB', edgecolor='#1a1a1a', linewidth=2
                ))

                # Ruedas (círculos negros más grandes)
                ax.add_patch(patches.Circle((x - 7, y - alto_carro/2), 2,
                            facecolor='#1a1a1a', edgecolor='#444', linewidth=2))
                ax.add_patch(patches.Circle((x + 7, y - alto_carro/2), 2,
                            facecolor='#1a1a1a', edgecolor='#444', linewidth=2))

                # Luces delanteras
                ax.add_patch(patches.Circle((x + ancho_carro/2 - 2, y + 1.5), 1.2,
                            facecolor='#FFD700', edgecolor='#FFA500', linewidth=2))
                ax.add_patch(patches.Circle((x + ancho_carro/2 - 2, y - 1.5), 1.2,
                            facecolor='#FFD700', edgecolor='#FFA500', linewidth=2))

            else:
                # ========== MOTOS ==========
                if es_exclusivo:
                    # MOTO ELÉCTRICA: Verde con rayo ⚡ (carril exclusivo)
                    moto_ancho = 8
                    moto_alto = 1.8
                    circulo_radio = 1.5
                    font_size = 12
                    color_moto = '#00FF00'
                    color_borde = '#004400'
                    color_centro = '#FFFF00'
                    simbolo = '⚡'
                else:
                    # MOTO GASOLINA: Naranja/Rojo con humo 💨 (tráfico mixto)
                    moto_ancho = 10
                    moto_alto = 2.5
                    circulo_radio = 2
                    font_size = 14
                    color_moto = '#FF6B35'  # Naranja
                    color_borde = '#8B0000'  # Rojo oscuro
                    color_centro = '#FFD700'
                    simbolo = '🛵'

                # Cuerpo de la moto (diamante/rombo)
                moto_points = [
                    [x - moto_ancho, y],
                    [x, y + moto_alto],
                    [x + moto_ancho, y],
                    [x, y - moto_alto],
                ]
                moto = patches.Polygon(moto_points, closed=True,
                            facecolor=color_moto, edgecolor=color_borde, linewidth=3)
                ax.add_patch(moto)

                # Círculo interior
                ax.add_patch(patches.Circle((x, y), circulo_radio,
                            facecolor=color_centro, edgecolor=color_borde, linewidth=2))

                # Símbolo
                ax.text(x, y, simbolo, ha='center', va='center', fontsize=font_size,
                       color=color_borde, fontweight='bold')

                # Humo para motos gasolina (indicador de contaminación)
                if not es_exclusivo:
                    ax.text(x - moto_ancho - 2, y, '💨', ha='center', va='center',
                           fontsize=8, alpha=0.7)

        # Contador de llegados - MÁS VISIBLE
        carros_total = self.sim.config["num_carros"]
        motos_total = self.sim.config["num_motos_electricas"]

        llegados = self.sim.llegados_exclusivo if es_exclusivo else self.sim.llegados_mixto

        # Fondo para el contador
        ax.add_patch(patches.FancyBboxPatch(
            (5, -8), 280, 5,
            boxstyle="round,pad=0.3",
            facecolor='#1a1a2e', edgecolor='white', linewidth=2, alpha=0.9
        ))

        if es_exclusivo:
            texto_motos = f"⚡ Motos ELÉCTRICAS llegadas: {llegados['motos']}/{motos_total}"
            color_motos = '#00FF00'
        else:
            texto_motos = f"🛵 Motos GASOLINA llegadas: {llegados['motos']}/{motos_total}"
            color_motos = '#FF6B35'

        ax.text(50, -5.5,
               f"🚗 Carros: {llegados['carros']}/{carros_total}",
               fontsize=13, color='#3498db', fontweight='bold')
        ax.text(180, -5.5, texto_motos,
               fontsize=13, color=color_motos, fontweight='bold')

    def dibujar_metricas_tiempo(self, ax):
        """Dibuja las métricas de tiempo comparativas - COMPACTO."""
        ax.clear()
        ax.set_facecolor('#0d1117')

        # Calcular tiempos promedio actuales
        def calcular_tiempo_promedio(vehiculos, tipo):
            tiempos = [v.tiempo_llegada for v in vehiculos
                      if v.tiempo_llegada and
                      (v.tipo == tipo if tipo else True)]
            return sum(tiempos)/len(tiempos) if tiempos else 0

        tiempo_moto_mixto = calcular_tiempo_promedio(self.sim.vehiculos_mixto, "moto_electrica")
        tiempo_moto_excl = calcular_tiempo_promedio(self.sim.vehiculos_exclusivo, "moto_electrica")
        tiempo_carro_mixto = calcular_tiempo_promedio(self.sim.vehiculos_mixto, "carro")
        tiempo_carro_excl = calcular_tiempo_promedio(self.sim.vehiculos_exclusivo, "carro")

        # Crear gráfico de barras
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')

        ax.text(5, 9.5, '⏱️ TIEMPOS DE VIAJE', ha='center', fontsize=12,
               fontweight='bold', color='white')

        # Barras comparativas
        max_tiempo = max(tiempo_moto_mixto, tiempo_moto_excl,
                        tiempo_carro_mixto, tiempo_carro_excl, 1) * 1.2

        bar_width = 1.5
        bar_spacing = 2.5

        datos = [
            ('🔋 Motos\n(Mixto)', tiempo_moto_mixto, '#e74c3c', 1),
            ('🔋 Motos\n(Exclusivo)', tiempo_moto_excl, '#27ae60', 1 + bar_spacing),
            ('🚗 Carros\n(Mixto)', tiempo_carro_mixto, '#e67e22', 1 + 2*bar_spacing),
            ('🚗 Carros\n(Exclusivo)', tiempo_carro_excl, '#3498db', 1 + 3*bar_spacing),
        ]

        for label, valor, color, x in datos:
            if max_tiempo > 0:
                altura = (valor / max_tiempo) * 5
            else:
                altura = 0

            ax.add_patch(patches.Rectangle(
                (x, 2), bar_width, altura,
                facecolor=color, edgecolor='white', linewidth=1
            ))
            ax.text(x + bar_width/2, 1.5, label, ha='center', va='top',
                   fontsize=7, color='white')
            if valor > 0:
                ax.text(x + bar_width/2, 2 + altura + 0.2, f'{valor:.0f}',
                       ha='center', fontsize=9, color=color, fontweight='bold')

        # Mejora porcentual
        if tiempo_moto_mixto > 0 and tiempo_moto_excl > 0:
            mejora = (tiempo_moto_mixto - tiempo_moto_excl) / tiempo_moto_mixto * 100
            color_mejora = '#27ae60' if mejora > 0 else '#e74c3c'
            ax.text(5, 8, f'📈 Mejora motos: {mejora:.1f}%', ha='center',
                   fontsize=11, color=color_mejora, fontweight='bold')

    def dibujar_metricas_sostenibilidad(self, ax):
        """Dibuja el panel de sostenibilidad - COMPACTO."""
        ax.clear()
        ax.set_facecolor('#0d1117')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')

        ax.text(5, 9.5, '🌱 IMPACTO AMBIENTAL', ha='center', fontsize=12,
               fontweight='bold', color='#27ae60')

        m = self.sim.metricas_exclusivo

        # Métricas en formato de tarjetas
        metricas = [
            ('🌿', 'CO₂ Evitado', f'{m.co2_ahorrado_kg:.2f} kg', '#27ae60'),
            ('🌳', 'Equivalente a', f'{m.arboles_equivalentes:.1f} árboles/año', '#2ecc71'),
            ('💰', 'Ahorro', f'${m.dinero_ahorrado_usd:.2f} USD', '#f39c12'),
            ('🔋', 'Km Eléctricos', f'{m.km_recorridos_electrico:.1f} km', '#3498db'),
        ]

        y_pos = 7.5
        for emoji, titulo, valor, color in metricas:
            # Tarjeta
            ax.add_patch(patches.FancyBboxPatch(
                (0.5, y_pos - 0.8), 9, 1.6,
                boxstyle="round,pad=0.1",
                facecolor='#1a1a2e', edgecolor=color, linewidth=2
            ))
            ax.text(1.2, y_pos, emoji, fontsize=14, va='center')
            ax.text(2.5, y_pos + 0.3, titulo, fontsize=9, color='#bdc3c7', va='center')
            ax.text(2.5, y_pos - 0.3, valor, fontsize=11, color=color,
                   va='center', fontweight='bold')
            y_pos -= 2

        # Mensaje motivacional
        ax.text(5, 0.5, '💚 Cada moto eléctrica = menos emisiones',
               ha='center', fontsize=9, color='#bdc3c7', style='italic')

    def dibujar_resumen(self, ax):
        """Dibuja el panel de resumen inferior."""
        ax.clear()
        ax.set_facecolor('#0f0f23')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 2)
        ax.axis('off')

        paso = self.sim.paso_actual
        total = self.sim.config["pasos_simulacion"]

        # Barra de progreso
        progreso = paso / total
        ax.add_patch(patches.Rectangle((0.5, 0.8), 9, 0.4,
                    facecolor='#2c3e50', edgecolor='white'))
        ax.add_patch(patches.Rectangle((0.5, 0.8), 9 * progreso, 0.4,
                    facecolor='#27ae60'))

        ax.text(5, 1.6, f'Simulación: Paso {paso}/{total}', ha='center',
               fontsize=11, color='white', fontweight='bold')

        # Leyenda
        ax.text(1, 0.3, '🔴 Mixto: Congestión alta', fontsize=9, color='#e74c3c')
        ax.text(5, 0.3, '🟢 Exclusivo: Flujo optimizado', fontsize=9, color='#27ae60')
        ax.text(8.5, 0.3, f'⚡ {self.sim.config["num_motos_electricas"]} motos eléctricas',
               fontsize=9, color='#3498db')

    def actualizar_frame(self, frame):
        """Actualiza cada frame de la animación."""
        # Ejecutar paso de simulación
        self.sim.ejecutar_paso()

        # Actualizar visualizaciones (sin panel de resumen)
        self.dibujar_via(self.axes['via_mixto'],
                        self.sim.vehiculos_mixto, es_exclusivo=False)
        self.dibujar_via(self.axes['via_exclusivo'],
                        self.sim.vehiculos_exclusivo, es_exclusivo=True)
        self.dibujar_metricas_tiempo(self.axes['metricas_tiempo'])
        self.dibujar_metricas_sostenibilidad(self.axes['metricas_sostenibilidad'])

        return []

    def ejecutar_animacion(self):
        """Ejecuta la animación completa."""
        self.crear_interfaz()
        self.sim.inicializar_vehiculos()

        # Dibujo inicial
        self.actualizar_frame(0)

        # Crear animación
        anim = animation.FuncAnimation(
            self.fig,
            self.actualizar_frame,
            frames=self.sim.config["pasos_simulacion"],
            interval=self.sim.config["intervalo_animacion_ms"],
            blit=False,
            repeat=False
        )

        plt.show()
        return anim


# ============================================================================
# GENERADOR DE REPORTE ESTÁTICO
# ============================================================================

def generar_reporte_estatico(config: dict = CONFIG):
    """
    Genera un reporte visual estático con los resultados de la simulación.
    Útil para incluir en presentaciones.
    """
    print("\nGenerando reporte estático...")

    # Ejecutar simulación completa
    sim = SimulacionVisualTrafico(config)
    sim.inicializar_vehiculos()

    # Guardar datos de progreso
    historial = {
        "pasos": [],
        "motos_llegadas_mixto": [],
        "motos_llegadas_exclusivo": [],
        "carros_llegados_mixto": [],
        "carros_llegados_exclusivo": [],
    }

    for i in range(config["pasos_simulacion"]):
        sim.ejecutar_paso()
        if i % 5 == 0:  # Guardar cada 5 pasos
            historial["pasos"].append(i)
            historial["motos_llegadas_mixto"].append(sim.llegados_mixto["motos"])
            historial["motos_llegadas_exclusivo"].append(sim.llegados_exclusivo["motos"])
            historial["carros_llegados_mixto"].append(sim.llegados_mixto["carros"])
            historial["carros_llegados_exclusivo"].append(sim.llegados_exclusivo["carros"])

    # Crear figura del reporte
    fig = plt.figure(figsize=(14, 10))
    fig.patch.set_facecolor('#1a1a2e')
    fig.suptitle(
        'REPORTE: IMPACTO DE CARRILES EXCLUSIVOS PARA MOTOS ELECTRICAS\n'
        'Simulacion de Movilidad Sostenible',
        fontsize=14, fontweight='bold', color='white', y=0.98
    )

    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.25,
                         left=0.08, right=0.92, top=0.88, bottom=0.08)

    # === GRÁFICA 1: Llegadas en el tiempo ===
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#16213e')
    ax1.plot(historial["pasos"], historial["motos_llegadas_mixto"],
            'r-', linewidth=2, label='Motos (Mixto)', marker='o', markersize=3)
    ax1.plot(historial["pasos"], historial["motos_llegadas_exclusivo"],
            'g-', linewidth=2, label='Motos (Exclusivo)', marker='s', markersize=3)
    ax1.set_xlabel('Tiempo (pasos)', color='white')
    ax1.set_ylabel('Motos que llegaron', color='white')
    ax1.set_title('Motos Electricas: Llegadas en el Tiempo', color='white', fontweight='bold')
    ax1.legend(facecolor='#16213e', labelcolor='white')
    ax1.tick_params(colors='white')
    ax1.grid(True, alpha=0.3)
    for spine in ax1.spines.values():
        spine.set_color('white')

    # === GRÁFICA 2: Comparación final de tiempos ===
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#16213e')

    # Calcular tiempos promedio
    def tiempo_promedio(vehiculos, tipo):
        tiempos = [v.tiempo_llegada for v in vehiculos
                  if v.tiempo_llegada and v.tipo == tipo]
        return sum(tiempos)/len(tiempos) if tiempos else 0

    t_moto_mix = tiempo_promedio(sim.vehiculos_mixto, "moto_electrica")
    t_moto_exc = tiempo_promedio(sim.vehiculos_exclusivo, "moto_electrica")
    t_carro_mix = tiempo_promedio(sim.vehiculos_mixto, "carro")
    t_carro_exc = tiempo_promedio(sim.vehiculos_exclusivo, "carro")

    categorias = ['Motos\nMixto', 'Motos\nExclusivo', 'Carros\nMixto', 'Carros\nExclusivo']
    valores = [t_moto_mix, t_moto_exc, t_carro_mix, t_carro_exc]
    colores = ['#e74c3c', '#27ae60', '#e67e22', '#3498db']

    bars = ax2.bar(categorias, valores, color=colores, edgecolor='white', linewidth=1.5)
    ax2.set_ylabel('Tiempo promedio (pasos)', color='white')
    ax2.set_title('Comparacion de Tiempos de Viaje', color='white', fontweight='bold')
    ax2.tick_params(colors='white')
    for spine in ax2.spines.values():
        spine.set_color('white')

    # Añadir valores encima de barras
    for bar, val in zip(bars, valores):
        if val > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                    f'{val:.0f}', ha='center', color='white', fontweight='bold')

    # Flecha de mejora
    if t_moto_mix > 0 and t_moto_exc > 0:
        mejora = (t_moto_mix - t_moto_exc) / t_moto_mix * 100
        ax2.annotate(f'{mejora:.0f}% menos\ntiempo',
                    xy=(1, t_moto_exc), xytext=(1.5, t_moto_mix),
                    color='#27ae60', fontsize=10, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='#27ae60', lw=2))

    # === GRÁFICA 3: Eficiencia (% llegados) ===
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor('#16213e')

    total_motos = config["num_motos_electricas"]
    total_carros = config["num_carros"]

    efic_motos_mix = (sim.llegados_mixto["motos"] / total_motos) * 100
    efic_motos_exc = (sim.llegados_exclusivo["motos"] / total_motos) * 100
    efic_carros_mix = (sim.llegados_mixto["carros"] / total_carros) * 100
    efic_carros_exc = (sim.llegados_exclusivo["carros"] / total_carros) * 100

    x = np.arange(2)
    width = 0.35

    bars1 = ax3.bar(x - width/2, [efic_motos_mix, efic_carros_mix], width,
                   label='Trafico Mixto', color='#e74c3c', edgecolor='white')
    bars2 = ax3.bar(x + width/2, [efic_motos_exc, efic_carros_exc], width,
                   label='Carril Exclusivo', color='#27ae60', edgecolor='white')

    ax3.set_ylabel('Eficiencia (%)', color='white')
    ax3.set_title('Eficiencia: Vehiculos que Completaron el Recorrido', color='white', fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(['Motos Electricas', 'Carros'], color='white')
    ax3.legend(facecolor='#16213e', labelcolor='white')
    ax3.tick_params(colors='white')
    ax3.set_ylim(0, 110)
    ax3.axhline(y=100, color='white', linestyle='--', alpha=0.3)
    for spine in ax3.spines.values():
        spine.set_color('white')

    # === PANEL 4: Métricas de sostenibilidad ===
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor('#16213e')
    ax4.axis('off')

    m = sim.metricas_exclusivo

    # Título
    ax4.text(0.5, 0.95, 'IMPACTO AMBIENTAL', ha='center', va='top',
            fontsize=14, fontweight='bold', color='#27ae60',
            transform=ax4.transAxes)

    # Métricas
    metricas_texto = [
        f"CO2 Evitado: {m.co2_ahorrado_kg:.2f} kg",
        f"Equivalente a {m.arboles_equivalentes:.1f} arboles plantados/año",
        f"Kilometros recorridos en electrico: {m.km_recorridos_electrico:.1f} km",
        f"Ahorro estimado: ${m.dinero_ahorrado_usd:.2f} USD",
        "",
        f"Motos electricas en simulacion: {config['num_motos_electricas']}",
        f"Emision moto electrica: 0 g CO2/km (cero emisiones directas)",
        f"Emision moto gasolina: {config['emision_moto_gasolina']} g CO2/km",
    ]

    y_pos = 0.80
    for texto in metricas_texto:
        color = '#27ae60' if 'CO2' in texto or 'Ahorro' in texto or 'Equivalente' in texto else '#bdc3c7'
        ax4.text(0.1, y_pos, texto, ha='left', va='top',
                fontsize=11, color=color, transform=ax4.transAxes)
        y_pos -= 0.10

    # Mensaje final
    ax4.text(0.5, 0.05,
            'Las motos electricas + carril exclusivo = movilidad mas eficiente y sostenible',
            ha='center', va='bottom', fontsize=10, color='#f39c12',
            style='italic', transform=ax4.transAxes,
            bbox=dict(boxstyle='round', facecolor='#1a1a2e', edgecolor='#f39c12'))

    # Guardar
    plt.savefig('reporte_sostenibilidad.png', dpi=150, facecolor=fig.get_facecolor(),
               bbox_inches='tight')
    print("Reporte guardado como 'reporte_sostenibilidad.png'")
    plt.show()


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Ejecuta la simulación visual."""
    print("=" * 60)
    print("  SIMULACION DE MOVILIDAD SOSTENIBLE")
    print("  Carriles Exclusivos para Motos Electricas")
    print("=" * 60)

    print("\nConfiguracion:")
    print(f"   Carros: {CONFIG['num_carros']}")
    print(f"   Motos electricas: {CONFIG['num_motos_electricas']}")
    print(f"   Longitud de via: {CONFIG['longitud_via_metros']} metros")

    print("\nDatos de sostenibilidad:")
    print(f"   Emision carro gasolina: {CONFIG['emision_carro_gasolina']} g CO2/km")
    print(f"   Emision moto electrica: {CONFIG['emision_moto_electrica']} g CO2/km (cero!)")

    print("\nOpciones:")
    print("  1. Ver animacion en tiempo real")
    print("  2. Generar reporte estatico (graficas)")
    print("  3. Ambos")

    opcion = input("\nElige una opcion (1/2/3): ").strip()

    if opcion == "2":
        generar_reporte_estatico()
    elif opcion == "3":
        generar_reporte_estatico()
        print("\nIniciando animacion...")
        simulacion = SimulacionVisualTrafico(CONFIG)
        visualizador = VisualizadorTrafico(simulacion)
        visualizador.ejecutar_animacion()
    else:
        print("\nIniciando simulacion visual...")
        print("(Cierra la ventana para terminar)\n")
        simulacion = SimulacionVisualTrafico(CONFIG)
        visualizador = VisualizadorTrafico(simulacion)
        visualizador.ejecutar_animacion()

    print("\nSimulacion completada.")


if __name__ == "__main__":
    main()
