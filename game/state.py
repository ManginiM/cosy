class GameState:
    """Estado global del juego: estadísticas que afectan la historia."""
    def __init__(self):
        # Sistema de dualidades - EL JARDÍN DE LOS SUSURROS
        self.dualities = {
            "panic_selfcontrol": 0,        # -100 a +100 (negativo: pánico, positivo: autocontrol)
            "rejection_understanding": 0,  # -100 a +100 (negativo: rechazo, positivo: comprensión)
        }
        self.stats = {
            "intelligence": 0              # 0 a 100
        }
        self.flags = {
            "vio_mariposa": False,
        }
        self.max_stat_value = 100

    def add_duality(self, key, value):
        """Añade valor a una dualidad, respetando los límites"""
        if key in self.dualities:
            self.dualities[key] = max(-100, min(100, self.dualities[key] + value))

    def set_duality(self, key, value):
        """Establece directamente una dualidad"""
        if key in self.dualities:
            self.dualities[key] = max(-100, min(value, 100))

    def add_stat(self, key, value):
        """Añade valor a una estadística simple"""
        if key in self.stats:
            self.stats[key] = max(0, min(self.stats[key] + value, self.max_stat_value))

    def set_stat(self, key, value):
        """Establece directamente una estadística simple"""
        if key in self.stats:
            self.stats[key] = max(0, min(value, self.max_stat_value))

    def get_duality(self, key):
        """Obtiene el valor de una dualidad"""
        return self.dualities.get(key, 0)

    def get_stat(self, key):
        """Obtiene el valor de una estadística simple"""
        return self.stats.get(key, 0)

    def set_flag(self, key, value=True):
        self.flags[key] = value

    def get_primary_tendency(self):
        """Calcula la tendencia principal del personaje para finales"""
        panic_tendency = -self.dualities["panic_selfcontrol"]  # Si es negativo = pánico
        rejection_tendency = -self.dualities["rejection_understanding"]  # Si es negativo = rechazo
        
        tendencies = {
            "panic": max(0, panic_tendency),
            "self_control": max(0, self.dualities["panic_selfcontrol"]),
            "rejection": max(0, rejection_tendency),
            "understanding": max(0, self.dualities["rejection_understanding"]),
        }
        return max(tendencies, key=tendencies.get) if any(tendencies.values()) else "balanced"