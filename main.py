"""
================================================================================
SIMULACIÓN DE TRÁFICO: CARRIL EXCLUSIVO PARA MOTOCICLETAS ELÉCTRICAS
================================================================================

Este programa simula y compara dos escenarios de tráfico:
1. Tráfico mixto: carros y motocicletas comparten el mismo carril
2. Carril exclusivo: las motocicletas tienen su propio carril

Autor: [Tu nombre]
Proyecto universitario
================================================================================
"""

import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from dataclasses import dataclass
from typing import List, Tuple

# ============================================================================
# PARÁMETROS DE CONFIGURACIÓN (MODIFICABLES)
# ============================================================================
# Puedes cambiar estos valores para experimentar con diferentes escenarios

PARAMETROS = {
    # Cantidad de vehículos
    "num_carros": 20,              # Número de carros en la simulación
    "num_motos": 15,               # Número de motocicletas eléctricas

    # Velocidades (unidades por paso de tiempo)
    "velocidad_carro_min": 2,      # Velocidad mínima de carros
    "velocidad_carro_max": 4,      # Velocidad máxima de carros
    "velocidad_moto_min": 4,       # Velocidad mínima de motos (más rápidas)
    "velocidad_moto_max": 6,       # Velocidad máxima de motos

    # Características de la vía
    "longitud_via": 300,           # Longitud total de la vía (unidades)
    "pasos_simulacion": 150,       # Número de iteraciones de la simulación

    # Factor de congestión (afecta tráfico mixto)
    "factor_congestion": 0.5,      # Qué tanto se reduce la velocidad en congestión (0-1)

    # Número de simulaciones para promediar resultados
    "num_simulaciones": 10,        # Más simulaciones = resultados más estables
}


# ============================================================================
# CLASES DE VEHÍCULOS
# ============================================================================

@dataclass
class Vehiculo:
    """
    Clase base que representa un vehículo en la simulación.

    Atributos:
        id: Identificador único del vehículo
        tipo: 'carro' o 'moto'
        posicion: Posición actual en la vía (0 a longitud_via)
        velocidad_base: Velocidad sin considerar congestión
        tiempo_inicio: Paso en que el vehículo comenzó
        tiempo_llegada: Paso en que llegó al final (None si no ha llegado)
    """
    id: int
    tipo: str
    posicion: float
    velocidad_base: float
    tiempo_inicio: int = 0
    tiempo_llegada: int = None

    def __post_init__(self):
        """Se ejecuta después de crear el objeto."""
        self.velocidad_actual = self.velocidad_base

    def mover(self, velocidad_efectiva: float) -> None:
        """
        Mueve el vehículo según su velocidad efectiva.

        Args:
            velocidad_efectiva: Velocidad real considerando congestión
        """
        self.posicion += velocidad_efectiva

    def ha_llegado(self, longitud_via: float) -> bool:
        """
        Verifica si el vehículo llegó al final de la vía.

        Args:
            longitud_via: Longitud total de la vía

        Returns:
            True si llegó, False si no
        """
        return self.posicion >= longitud_via


def crear_carro(id: int, params: dict) -> Vehiculo:
    """
    Crea un nuevo carro con velocidad aleatoria dentro del rango.

    Args:
        id: Identificador único
        params: Diccionario de parámetros

    Returns:
        Objeto Vehiculo de tipo 'carro'
    """
    velocidad = random.uniform(
        params["velocidad_carro_min"],
        params["velocidad_carro_max"]
    )
    # Posición inicial aleatoria en el primer 20% de la vía
    posicion_inicial = random.uniform(0, params["longitud_via"] * 0.2)

    return Vehiculo(
        id=id,
        tipo="carro",
        posicion=posicion_inicial,
        velocidad_base=velocidad
    )


def crear_moto(id: int, params: dict) -> Vehiculo:
    """
    Crea una nueva motocicleta eléctrica con velocidad aleatoria.

    Args:
        id: Identificador único
        params: Diccionario de parámetros

    Returns:
        Objeto Vehiculo de tipo 'moto'
    """
    velocidad = random.uniform(
        params["velocidad_moto_min"],
        params["velocidad_moto_max"]
    )
    # Posición inicial aleatoria en el primer 20% de la vía
    posicion_inicial = random.uniform(0, params["longitud_via"] * 0.2)

    return Vehiculo(
        id=id,
        tipo="moto",
        posicion=posicion_inicial,
        velocidad_base=velocidad
    )


# ============================================================================
# CLASE DE SIMULACIÓN
# ============================================================================

class SimulacionTrafico:
    """
    Clase principal que ejecuta la simulación de tráfico.

    Puede simular dos escenarios:
    - Tráfico mixto: todos los vehículos comparten carril
    - Carril exclusivo: las motos tienen su propio carril
    """

    def __init__(self, params: dict):
        """
        Inicializa la simulación con los parámetros dados.

        Args:
            params: Diccionario con parámetros de configuración
        """
        self.params = params
        self.vehiculos: List[Vehiculo] = []
        self.paso_actual = 0
        self.historial_posiciones = []  # Para la animación

    def inicializar_vehiculos(self) -> None:
        """Crea todos los vehículos al inicio de la simulación."""
        self.vehiculos = []

        # Crear carros
        for i in range(self.params["num_carros"]):
            carro = crear_carro(i, self.params)
            self.vehiculos.append(carro)

        # Crear motocicletas
        for i in range(self.params["num_motos"]):
            moto = crear_moto(i + self.params["num_carros"], self.params)
            self.vehiculos.append(moto)

    def calcular_congestion(self, vehiculo: Vehiculo, es_mixto: bool) -> float:
        """
        Calcula el factor de congestión para un vehículo.

        En tráfico mixto, los vehículos más lentos (carros) bloquean
        a los más rápidos (motos), creando congestión.

        Args:
            vehiculo: El vehículo a evaluar
            es_mixto: True si es escenario de tráfico mixto

        Returns:
            Factor entre 0 y 1 (1 = sin congestión, 0 = parado)
        """
        # Contar vehículos que están ADELANTE y cerca (bloquean el paso)
        vehiculos_adelante = [
            v for v in self.vehiculos
            if v.id != vehiculo.id
            and v.tiempo_llegada is None
            and v.posicion > vehiculo.posicion  # Está adelante
            and v.posicion - vehiculo.posicion < 25  # Está cerca
        ]

        if not es_mixto:
            # CARRIL EXCLUSIVO
            if vehiculo.tipo == "moto":
                # Las motos tienen su propio carril, fluyen libremente
                # Solo pequeña reducción por densidad general
                return max(0.9, 1.0 - len(vehiculos_adelante) * 0.02)

            # Los carros compiten solo entre ellos
            carros_adelante = [v for v in vehiculos_adelante if v.tipo == "carro"]
            if not carros_adelante:
                return 1.0
            # Reducción moderada por carros cercanos
            return max(0.6, 1.0 - len(carros_adelante) * 0.1)

        # TRÁFICO MIXTO: todos comparten carril, más congestión
        if not vehiculos_adelante:
            return 1.0

        # Contar por tipo
        carros_adelante = sum(1 for v in vehiculos_adelante if v.tipo == "carro")
        motos_adelante = sum(1 for v in vehiculos_adelante if v.tipo == "moto")

        if vehiculo.tipo == "moto":
            # Las motos sufren más congestión porque no pueden adelantar carros
            # Los carros las bloquean significativamente
            factor = 1.0 - (carros_adelante * 0.15) - (motos_adelante * 0.05)
            factor *= (1 - self.params["factor_congestion"] * 0.3)
            return max(0.35, factor)
        else:
            # Los carros tienen congestión normal
            factor = 1.0 - (carros_adelante * 0.12) - (motos_adelante * 0.03)
            return max(0.45, factor)

    def ejecutar_paso(self, es_mixto: bool) -> None:
        """
        Ejecuta un paso de tiempo en la simulación.

        Args:
            es_mixto: True para simular tráfico mixto
        """
        self.paso_actual += 1
        posiciones_paso = {"carros": [], "motos": []}

        for vehiculo in self.vehiculos:
            # Solo mover vehículos que no han llegado
            if vehiculo.tiempo_llegada is not None:
                continue

            # Calcular velocidad efectiva
            factor_congestion = self.calcular_congestion(vehiculo, es_mixto)
            velocidad_efectiva = vehiculo.velocidad_base * factor_congestion

            # Mover el vehículo
            vehiculo.mover(velocidad_efectiva)

            # Verificar si llegó
            if vehiculo.ha_llegado(self.params["longitud_via"]):
                vehiculo.tiempo_llegada = self.paso_actual

            # Guardar posición para historial
            if vehiculo.tipo == "carro":
                posiciones_paso["carros"].append(vehiculo.posicion)
            else:
                posiciones_paso["motos"].append(vehiculo.posicion)

        self.historial_posiciones.append(posiciones_paso)

    def ejecutar_simulacion(self, es_mixto: bool) -> dict:
        """
        Ejecuta la simulación completa y retorna los resultados.

        Args:
            es_mixto: True para tráfico mixto, False para carril exclusivo

        Returns:
            Diccionario con métricas de la simulación
        """
        self.inicializar_vehiculos()
        self.paso_actual = 0
        self.historial_posiciones = []

        # Ejecutar todos los pasos
        for _ in range(self.params["pasos_simulacion"]):
            self.ejecutar_paso(es_mixto)

        # Calcular métricas
        return self.calcular_metricas()

    def calcular_metricas(self) -> dict:
        """
        Calcula las métricas de rendimiento de la simulación.

        Returns:
            Diccionario con:
            - tiempo_promedio_carros: Tiempo promedio de viaje de carros
            - tiempo_promedio_motos: Tiempo promedio de viaje de motos
            - vehiculos_llegaron: Cantidad que completaron el recorrido
            - eficiencia: Porcentaje de vehículos que llegaron
        """
        tiempos_carros = []
        tiempos_motos = []

        for vehiculo in self.vehiculos:
            if vehiculo.tiempo_llegada is not None:
                tiempo_viaje = vehiculo.tiempo_llegada - vehiculo.tiempo_inicio
                if vehiculo.tipo == "carro":
                    tiempos_carros.append(tiempo_viaje)
                else:
                    tiempos_motos.append(tiempo_viaje)

        # Calcular promedios (evitar división por cero)
        tiempo_prom_carros = sum(tiempos_carros) / len(tiempos_carros) if tiempos_carros else float('inf')
        tiempo_prom_motos = sum(tiempos_motos) / len(tiempos_motos) if tiempos_motos else float('inf')

        total_vehiculos = len(self.vehiculos)
        vehiculos_llegaron = len(tiempos_carros) + len(tiempos_motos)

        return {
            "tiempo_promedio_carros": tiempo_prom_carros,
            "tiempo_promedio_motos": tiempo_prom_motos,
            "tiempo_promedio_total": (tiempo_prom_carros + tiempo_prom_motos) / 2,
            "carros_llegaron": len(tiempos_carros),
            "motos_llegaron": len(tiempos_motos),
            "vehiculos_llegaron": vehiculos_llegaron,
            "eficiencia": (vehiculos_llegaron / total_vehiculos) * 100,
        }


# ============================================================================
# FUNCIONES DE VISUALIZACIÓN
# ============================================================================

def ejecutar_multiples_simulaciones(params: dict) -> Tuple[dict, dict]:
    """
    Ejecuta múltiples simulaciones y promedia los resultados.

    Esto da resultados más estables y confiables.

    Args:
        params: Parámetros de configuración

    Returns:
        Tupla con (resultados_mixto, resultados_exclusivo)
    """
    resultados_mixto = {
        "tiempo_promedio_carros": [],
        "tiempo_promedio_motos": [],
        "eficiencia": []
    }
    resultados_exclusivo = {
        "tiempo_promedio_carros": [],
        "tiempo_promedio_motos": [],
        "eficiencia": []
    }

    print(f"Ejecutando {params['num_simulaciones']} simulaciones...")

    for i in range(params["num_simulaciones"]):
        sim = SimulacionTrafico(params)

        # Simulación mixta
        resultado = sim.ejecutar_simulacion(es_mixto=True)
        resultados_mixto["tiempo_promedio_carros"].append(resultado["tiempo_promedio_carros"])
        resultados_mixto["tiempo_promedio_motos"].append(resultado["tiempo_promedio_motos"])
        resultados_mixto["eficiencia"].append(resultado["eficiencia"])

        # Simulación con carril exclusivo
        resultado = sim.ejecutar_simulacion(es_mixto=False)
        resultados_exclusivo["tiempo_promedio_carros"].append(resultado["tiempo_promedio_carros"])
        resultados_exclusivo["tiempo_promedio_motos"].append(resultado["tiempo_promedio_motos"])
        resultados_exclusivo["eficiencia"].append(resultado["eficiencia"])

        print(f"  Simulación {i+1}/{params['num_simulaciones']} completada")

    # Promediar resultados
    def promediar(lista):
        valores_validos = [v for v in lista if v != float('inf')]
        return sum(valores_validos) / len(valores_validos) if valores_validos else 0

    promedio_mixto = {
        "tiempo_promedio_carros": promediar(resultados_mixto["tiempo_promedio_carros"]),
        "tiempo_promedio_motos": promediar(resultados_mixto["tiempo_promedio_motos"]),
        "eficiencia": promediar(resultados_mixto["eficiencia"])
    }

    promedio_exclusivo = {
        "tiempo_promedio_carros": promediar(resultados_exclusivo["tiempo_promedio_carros"]),
        "tiempo_promedio_motos": promediar(resultados_exclusivo["tiempo_promedio_motos"]),
        "eficiencia": promediar(resultados_exclusivo["eficiencia"])
    }

    return promedio_mixto, promedio_exclusivo


def crear_graficas_comparativas(mixto: dict, exclusivo: dict, params: dict) -> None:
    """
    Crea gráficas comparando los dos escenarios.

    Args:
        mixto: Resultados del escenario de tráfico mixto
        exclusivo: Resultados del escenario con carril exclusivo
        params: Parámetros de la simulación
    """
    # Configurar estilo de las gráficas
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Comparación: Tráfico Mixto vs Carril Exclusivo para Motos',
                 fontsize=14, fontweight='bold')

    # Colores consistentes
    colores = ['#e74c3c', '#27ae60']  # Rojo para mixto, verde para exclusivo
    labels = ['Tráfico Mixto', 'Carril Exclusivo']

    # -------------------------------------------------------------------------
    # GRÁFICA 1: Tiempo promedio de viaje por tipo de vehículo
    # -------------------------------------------------------------------------
    ax1 = axes[0]

    x = [0, 1, 2, 3]
    tiempos = [
        mixto["tiempo_promedio_carros"],
        exclusivo["tiempo_promedio_carros"],
        mixto["tiempo_promedio_motos"],
        exclusivo["tiempo_promedio_motos"]
    ]
    colores_barras = [colores[0], colores[1], colores[0], colores[1]]

    barras = ax1.bar(x, tiempos, color=colores_barras, edgecolor='black', linewidth=1.2)

    ax1.set_xticks(x)
    ax1.set_xticklabels(['Carros\n(Mixto)', 'Carros\n(Exclusivo)',
                         'Motos\n(Mixto)', 'Motos\n(Exclusivo)'])
    ax1.set_ylabel('Tiempo Promedio (pasos)', fontsize=11)
    ax1.set_title('Tiempo de Viaje por Tipo', fontsize=12, fontweight='bold')

    # Añadir valores encima de las barras
    for barra, tiempo in zip(barras, tiempos):
        ax1.annotate(f'{tiempo:.1f}',
                    xy=(barra.get_x() + barra.get_width() / 2, barra.get_height()),
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    # -------------------------------------------------------------------------
    # GRÁFICA 2: Comparación de tiempos de motocicletas (principal interés)
    # -------------------------------------------------------------------------
    ax2 = axes[1]

    tiempos_motos = [mixto["tiempo_promedio_motos"], exclusivo["tiempo_promedio_motos"]]
    barras2 = ax2.bar(labels, tiempos_motos, color=colores, edgecolor='black', linewidth=1.2)

    ax2.set_ylabel('Tiempo Promedio (pasos)', fontsize=11)
    ax2.set_title('Tiempo de Viaje de Motocicletas', fontsize=12, fontweight='bold')

    # Calcular y mostrar la mejora porcentual
    if mixto["tiempo_promedio_motos"] > 0:
        mejora = ((mixto["tiempo_promedio_motos"] - exclusivo["tiempo_promedio_motos"])
                  / mixto["tiempo_promedio_motos"] * 100)
        ax2.annotate(f'↓ {mejora:.1f}% menos tiempo',
                    xy=(1, exclusivo["tiempo_promedio_motos"]),
                    xytext=(1, exclusivo["tiempo_promedio_motos"] * 1.2),
                    ha='center', fontsize=11, color='green', fontweight='bold')

    for barra, tiempo in zip(barras2, tiempos_motos):
        ax2.annotate(f'{tiempo:.1f}',
                    xy=(barra.get_x() + barra.get_width() / 2, barra.get_height()),
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    # -------------------------------------------------------------------------
    # GRÁFICA 3: Eficiencia del tráfico
    # -------------------------------------------------------------------------
    ax3 = axes[2]

    eficiencias = [mixto["eficiencia"], exclusivo["eficiencia"]]
    barras3 = ax3.bar(labels, eficiencias, color=colores, edgecolor='black', linewidth=1.2)

    ax3.set_ylabel('Eficiencia (%)', fontsize=11)
    ax3.set_title('Eficiencia del Tráfico', fontsize=12, fontweight='bold')
    ax3.set_ylim(0, 110)  # Para que se vea el 100%

    # Línea de referencia al 100%
    ax3.axhline(y=100, color='gray', linestyle='--', alpha=0.5)

    for barra, efic in zip(barras3, eficiencias):
        ax3.annotate(f'{efic:.1f}%',
                    xy=(barra.get_x() + barra.get_width() / 2, barra.get_height()),
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Ajustar espaciado
    plt.tight_layout()

    # Guardar la figura
    plt.savefig('resultados_simulacion.png', dpi=150, bbox_inches='tight')
    print("\n✓ Gráfica guardada como 'resultados_simulacion.png'")

    # Mostrar
    plt.show()


def crear_animacion(params: dict, duracion_segundos: int = 10) -> None:
    """
    Crea una animación mostrando el movimiento de vehículos en tiempo real.

    Esta es una visualización opcional pero muy útil para presentaciones.

    Args:
        params: Parámetros de configuración
        duracion_segundos: Duración aproximada de la animación
    """
    print("\nGenerando animación comparativa...")

    # Crear dos simulaciones
    sim_mixto = SimulacionTrafico(params)
    sim_exclusivo = SimulacionTrafico(params)

    # Inicializar con la misma semilla para comparar
    random.seed(42)
    sim_mixto.inicializar_vehiculos()
    random.seed(42)
    sim_exclusivo.inicializar_vehiculos()

    # Configurar figura con dos subgráficas
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle('Simulación en Tiempo Real', fontsize=14, fontweight='bold')

    # Configurar ejes
    for ax, titulo in [(ax1, 'TRÁFICO MIXTO (carros y motos comparten carril)'),
                       (ax2, 'CARRIL EXCLUSIVO (motos en su propio carril)')]:
        ax.set_xlim(0, params["longitud_via"])
        ax.set_ylim(-1, 2)
        ax.set_title(titulo, fontsize=11)
        ax.set_xlabel('Posición en la vía')
        ax.set_yticks([0, 1])
        ax.set_yticklabels(['Carril 1', 'Carril 2'])
        ax.axvline(x=params["longitud_via"], color='green', linewidth=3, label='META')

    # Elementos a animar
    scatter_mixto_carros = ax1.scatter([], [], c='blue', s=100, marker='s', label='Carros')
    scatter_mixto_motos = ax1.scatter([], [], c='red', s=80, marker='^', label='Motos')

    scatter_excl_carros = ax2.scatter([], [], c='blue', s=100, marker='s', label='Carros')
    scatter_excl_motos = ax2.scatter([], [], c='red', s=80, marker='^', label='Motos')

    # Leyendas
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper left')

    # Texto para mostrar estadísticas
    texto_mixto = ax1.text(10, 1.7, '', fontsize=10)
    texto_exclusivo = ax2.text(10, 1.7, '', fontsize=10)

    def init():
        """Inicializa la animación."""
        scatter_mixto_carros.set_offsets([])
        scatter_mixto_motos.set_offsets([])
        scatter_excl_carros.set_offsets([])
        scatter_excl_motos.set_offsets([])
        return (scatter_mixto_carros, scatter_mixto_motos,
                scatter_excl_carros, scatter_excl_motos)

    def actualizar(frame):
        """Actualiza cada frame de la animación."""
        # Ejecutar un paso en cada simulación
        sim_mixto.ejecutar_paso(es_mixto=True)
        sim_exclusivo.ejecutar_paso(es_mixto=False)

        # Obtener posiciones actuales
        pos_mixto_carros = [(v.posicion, 0.5) for v in sim_mixto.vehiculos
                           if v.tipo == "carro" and v.tiempo_llegada is None]
        pos_mixto_motos = [(v.posicion, 0.5) for v in sim_mixto.vehiculos
                          if v.tipo == "moto" and v.tiempo_llegada is None]

        # En carril exclusivo, motos van en carril separado (y=1)
        pos_excl_carros = [(v.posicion, 0) for v in sim_exclusivo.vehiculos
                          if v.tipo == "carro" and v.tiempo_llegada is None]
        pos_excl_motos = [(v.posicion, 1) for v in sim_exclusivo.vehiculos
                         if v.tipo == "moto" and v.tiempo_llegada is None]

        # Actualizar posiciones
        if pos_mixto_carros:
            scatter_mixto_carros.set_offsets(pos_mixto_carros)
        if pos_mixto_motos:
            scatter_mixto_motos.set_offsets(pos_mixto_motos)
        if pos_excl_carros:
            scatter_excl_carros.set_offsets(pos_excl_carros)
        if pos_excl_motos:
            scatter_excl_motos.set_offsets(pos_excl_motos)

        # Contar llegados
        llegados_mixto = sum(1 for v in sim_mixto.vehiculos if v.tiempo_llegada is not None)
        llegados_excl = sum(1 for v in sim_exclusivo.vehiculos if v.tiempo_llegada is not None)

        texto_mixto.set_text(f'Paso: {frame+1} | Llegaron: {llegados_mixto}')
        texto_exclusivo.set_text(f'Paso: {frame+1} | Llegaron: {llegados_excl}')

        return (scatter_mixto_carros, scatter_mixto_motos,
                scatter_excl_carros, scatter_excl_motos,
                texto_mixto, texto_exclusivo)

    # Crear animación
    frames = min(params["pasos_simulacion"], 150)  # Limitar frames
    intervalo = (duracion_segundos * 1000) // frames  # ms entre frames

    anim = animation.FuncAnimation(
        fig, actualizar, init_func=init,
        frames=frames, interval=intervalo, blit=False
    )

    # Guardar como GIF (opcional, requiere pillow)
    try:
        anim.save('simulacion_animada.gif', writer='pillow', fps=15)
        print("✓ Animación guardada como 'simulacion_animada.gif'")
    except Exception as e:
        print(f"Nota: No se pudo guardar el GIF ({e})")
        print("  La animación se mostrará en pantalla.")

    plt.tight_layout()
    plt.show()


def imprimir_resumen(mixto: dict, exclusivo: dict) -> None:
    """
    Imprime un resumen de los resultados en la consola.

    Args:
        mixto: Resultados del escenario mixto
        exclusivo: Resultados del escenario con carril exclusivo
    """
    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)

    print("\n📊 TRÁFICO MIXTO (todos comparten carril):")
    print(f"   • Tiempo promedio carros: {mixto['tiempo_promedio_carros']:.1f} pasos")
    print(f"   • Tiempo promedio motos:  {mixto['tiempo_promedio_motos']:.1f} pasos")
    print(f"   • Eficiencia total:       {mixto['eficiencia']:.1f}%")

    print("\n🛣️  CARRIL EXCLUSIVO (motos en carril separado):")
    print(f"   • Tiempo promedio carros: {exclusivo['tiempo_promedio_carros']:.1f} pasos")
    print(f"   • Tiempo promedio motos:  {exclusivo['tiempo_promedio_motos']:.1f} pasos")
    print(f"   • Eficiencia total:       {exclusivo['eficiencia']:.1f}%")

    # Calcular mejoras
    if mixto['tiempo_promedio_motos'] > 0:
        mejora_tiempo = ((mixto['tiempo_promedio_motos'] - exclusivo['tiempo_promedio_motos'])
                        / mixto['tiempo_promedio_motos'] * 100)
        print(f"\n✅ MEJORA PARA MOTOCICLETAS: {mejora_tiempo:.1f}% menos tiempo de viaje")

    mejora_eficiencia = exclusivo['eficiencia'] - mixto['eficiencia']
    print(f"✅ MEJORA EN EFICIENCIA: +{mejora_eficiencia:.1f} puntos porcentuales")

    print("\n" + "="*60)


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """
    Función principal que ejecuta todo el programa.
    """
    print("="*60)
    print("SIMULACIÓN DE TRÁFICO")
    print("Impacto de Carriles Exclusivos para Motocicletas Eléctricas")
    print("="*60)

    # Mostrar parámetros actuales
    print("\n📋 Parámetros de simulación:")
    print(f"   • Número de carros: {PARAMETROS['num_carros']}")
    print(f"   • Número de motos: {PARAMETROS['num_motos']}")
    print(f"   • Longitud de vía: {PARAMETROS['longitud_via']} unidades")
    print(f"   • Pasos de simulación: {PARAMETROS['pasos_simulacion']}")

    # Ejecutar simulaciones
    print("\n" + "-"*60)
    resultados_mixto, resultados_exclusivo = ejecutar_multiples_simulaciones(PARAMETROS)

    # Mostrar resumen
    imprimir_resumen(resultados_mixto, resultados_exclusivo)

    # Crear gráficas
    print("\nGenerando gráficas comparativas...")
    crear_graficas_comparativas(resultados_mixto, resultados_exclusivo, PARAMETROS)

    # Preguntar si quiere ver la animación
    print("\n¿Deseas ver la animación de la simulación? (puede tardar unos segundos)")
    respuesta = input("Escribe 's' para sí, cualquier otra tecla para no: ").strip().lower()

    if respuesta == 's':
        crear_animacion(PARAMETROS)

    print("\n✓ Simulación completada exitosamente.")
    print("  Revisa los archivos generados:")
    print("  - resultados_simulacion.png (gráficas)")
    print("  - simulacion_animada.gif (animación, si se generó)")


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    main()