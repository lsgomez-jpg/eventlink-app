

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from models.servicio import Servicio
from models.usuario import Usuario
from sqlalchemy import and_, or_, desc, asc

class BusquedaStrategy(ABC):
    """Estrategia abstracta para búsqueda de servicios"""
    
    @abstractmethod
    def buscar(self, query: Dict[str, Any]) -> List[Servicio]:
        """Método abstracto para realizar búsqueda"""
        pass
    
    @abstractmethod
    def obtener_nombre(self) -> str:
        """Retorna el nombre de la estrategia"""
        pass

class BusquedaPorPrecio(BusquedaStrategy):
    """Estrategia de búsqueda por rango de precios"""
    
    def buscar(self, query: Dict[str, Any]) -> List[Servicio]:
        """Busca servicios por rango de precios"""
        precio_min = query.get('precio_min', 0)
        precio_max = query.get('precio_max', float('inf'))
        categoria = query.get('categoria')
        ciudad = query.get('ciudad')
        
        # Construir consulta base
        consulta = Servicio.query.filter(
            and_(
                Servicio.precio_base >= precio_min,
                Servicio.precio_base <= precio_max,
                Servicio.estado == 'disponible'
            )
        )
        
        # Aplicar filtros adicionales
        if categoria:
            consulta = consulta.filter(Servicio.categoria == categoria)
        
        if ciudad:
            consulta = consulta.filter(Servicio.ciudad.ilike(f'%{ciudad}%'))
        
        # Ordenar por precio ascendente
        return consulta.order_by(asc(Servicio.precio_base)).all()
    
    def obtener_nombre(self) -> str:
        return "Búsqueda por Precio"

class BusquedaPorCalificacion(BusquedaStrategy):
    """Estrategia de búsqueda por calificación promedio"""
    
    def buscar(self, query: Dict[str, Any]) -> List[Servicio]:
        """Busca servicios por calificación mínima"""
        calificacion_min = query.get('calificacion_min', 0)
        categoria = query.get('categoria')
        ciudad = query.get('ciudad')
        
        # Construir consulta base
        consulta = Servicio.query.filter(
            and_(
                Servicio.estado == 'disponible'
            )
        )
        
        # Aplicar filtros adicionales
        if categoria:
            consulta = consulta.filter(Servicio.categoria == categoria)
        
        if ciudad:
            consulta = consulta.filter(Servicio.ciudad.ilike(f'%{ciudad}%'))
        
        # Obtener servicios y filtrar por calificación
        servicios = consulta.all()
        servicios_filtrados = []
        
        for servicio in servicios:
            calificacion_promedio = servicio.obtener_calificacion_promedio()
            if calificacion_promedio >= calificacion_min:
                servicios_filtrados.append(servicio)
        
        # Ordenar por calificación descendente
        servicios_filtrados.sort(
            key=lambda s: s.obtener_calificacion_promedio(), 
            reverse=True
        )
        
        return servicios_filtrados
    
    def obtener_nombre(self) -> str:
        return "Búsqueda por Calificación"

class BusquedaPorUbicacion(BusquedaStrategy):
    """Estrategia de búsqueda por ubicacion cercanas """
    
    def buscar(self, query: Dict[str, Any]) -> List[Servicio]:
        """Busca servicios por proximidad geográfica"""
        ciudad = query.get('ciudad')
        radio_km = query.get('radio_km', 50)
        categoria = query.get('categoria')
        
        # Construir consulta base
        consulta = Servicio.query.filter(
            and_(
                Servicio.estado == 'disponible',
                Servicio.radio_cobertura >= radio_km
            )
        )
        
        # Aplicar filtros adicionales
        if categoria:
            consulta = consulta.filter(Servicio.categoria == categoria)
        
        if ciudad:
            consulta = consulta.filter(Servicio.ciudad.ilike(f'%{ciudad}%'))
        
        # Ordenar por radio de cobertura ascendente (más cercanos primero)
        return consulta.order_by(asc(Servicio.radio_cobertura)).all()
    
    def obtener_nombre(self) -> str:
        return "Búsqueda por Ubicación"

class BusquedaPorDisponibilidad(BusquedaStrategy):
    """Estrategia de búsqueda por disponibilidad de fechas"""
    
    def buscar(self, query: Dict[str, Any]) -> List[Servicio]:
        """Busca servicios disponibles para fechas específicas"""
        fecha_evento = query.get('fecha_evento')
        duracion_horas = query.get('duracion_horas', 1)
        categoria = query.get('categoria')
        ciudad = query.get('ciudad')
        
        # Construir consulta base
        consulta = Servicio.query.filter(
            and_(
                Servicio.estado == 'disponible'
            )
        )
        
        # Aplicar filtros adicionales
        if categoria:
            consulta = consulta.filter(Servicio.categoria == categoria)
        
        if ciudad:
            consulta = consulta.filter(Servicio.ciudad.ilike(f'%{ciudad}%'))
        
        # Filtrar por duración si se especifica
        if duracion_horas:
            consulta = consulta.filter(
                or_(
                    Servicio.duracion_maxima.is_(None),
                    Servicio.duracion_maxima >= duracion_horas
                )
            )
        
        # TODO: faltaria  logica de verificación de disponibilidad real
        # se deria crear una consulta para las contrataciones existentes

        return consulta.all()
    
    def obtener_nombre(self) -> str:
        return "Búsqueda por Disponibilidad"

class BusquedaCombinada(BusquedaStrategy):
    """Estrategia que combina múltiples criterios de búsqueda"""
    
    def __init__(self):
        self.estrategias = {
            'precio': BusquedaPorPrecio(),
            'calificacion': BusquedaPorCalificacion(),
            'ubicacion': BusquedaPorUbicacion(),
            'disponibilidad': BusquedaPorDisponibilidad()
        }
    
    def buscar(self, query: Dict[str, Any]) -> List[Servicio]:
        """Combina resultados de múltiples estrategias"""
        criterios = query.get('criterios', ['precio'])
        peso_precio = query.get('peso_precio', 0.3)
        peso_calificacion = query.get('peso_calificacion', 0.3)
        peso_ubicacion = query.get('peso_ubicacion', 0.2)
        peso_disponibilidad = query.get('peso_disponibilidad', 0.2)
        
        resultados = {}
        
        # Ejecutar cada estrategia
        for criterio in criterios:
            if criterio in self.estrategias:
                resultados[criterio] = self.estrategias[criterio].buscar(query)
        
        # Combinar y puntuar resultados
        servicios_puntuados = {}
        
        for criterio, servicios in resultados.items():
            peso = {
                'precio': peso_precio,
                'calificacion': peso_calificacion,
                'ubicacion': peso_ubicacion,
                'disponibilidad': peso_disponibilidad
            }.get(criterio, 0.25)
            
            for i, servicio in enumerate(servicios):
                if servicio.id not in servicios_puntuados:
                    servicios_puntuados[servicio.id] = {
                        'servicio': servicio,
                        'puntuacion': 0
                    }
                
                # Puntuación basada en posición (mejor posición = mayor puntuación)
                puntuacion_posicion = (len(servicios) - i) / len(servicios)
                servicios_puntuados[servicio.id]['puntuacion'] += puntuacion_posicion * peso
        
        # Ordenar por puntuación total
        servicios_ordenados = sorted(
            servicios_puntuados.values(),
            key=lambda x: x['puntuacion'],
            reverse=True
        )
        
        return [item['servicio'] for item in servicios_ordenados]
    
    def obtener_nombre(self) -> str:
        return "Búsqueda Combinada"

class BusquedaManager:
    """Manager para gestionar las estrategias de búsqueda"""
    
    def __init__(self):
        self.estrategias = {
            'precio': BusquedaPorPrecio(),
            'calificacion': BusquedaPorCalificacion(),
            'ubicacion': BusquedaPorUbicacion(),
            'disponibilidad': BusquedaPorDisponibilidad(),
            'combinada': BusquedaCombinada()
        }
    
    def buscar_servicios(self, tipo_busqueda: str, query: Dict[str, Any]) -> List[Servicio]:
        """Ejecuta búsqueda usando la estrategia especificada"""
        estrategia = self.estrategias.get(tipo_busqueda)
        
        if not estrategia:
            raise ValueError(f"Estrategia de búsqueda '{tipo_busqueda}' no encontrada")
        
        print(f"🔍 Ejecutando búsqueda: {estrategia.obtener_nombre()}")
        return estrategia.buscar(query)
    
    def obtener_estrategias_disponibles(self) -> List[str]:
        """Retorna las estrategias de búsqueda disponibles"""
        return list(self.estrategias.keys())
    
    def registrar_estrategia(self, nombre: str, estrategia: BusquedaStrategy):
        """Registra una nueva estrategia de búsqueda"""
        self.estrategias[nombre] = estrategia
        print(f"✅ Estrategia '{nombre}' registrada")
    
    def obtener_estadisticas_busqueda(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene estadísticas de búsqueda"""
        estadisticas = {}
        
        for nombre, estrategia in self.estrategias.items():
            try:
                resultados = estrategia.buscar(query)
                estadisticas[nombre] = {
                    'resultados': len(resultados),
                    'estrategia': estrategia.obtener_nombre()
                }
            except Exception as e:
                estadisticas[nombre] = {
                    'error': str(e),
                    'estrategia': estrategia.obtener_nombre()
                }
        
        return estadisticas

# Instancia global del manager de búsqueda
busqueda_manager = BusquedaManager()










