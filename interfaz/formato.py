"""Formato de números y unidades para la interfaz bilingüe."""

UNIDADES_LEGIBLES = {
    "COP/carga_125kg": "COP/carga",
    "USc/lb": "US¢/lb",
    "miles_sacos_60kg": "miles de sacos de 60 kg",
}


def unidad_legible(unidad: str) -> str:
    """Traduce una unidad técnica del contrato a una etiqueta visible."""
    return UNIDADES_LEGIBLES.get(unidad, unidad)


def numero(valor: float, decimales: int, idioma: str = "es") -> str:
    """Formatea un número con los separadores del idioma seleccionado."""
    texto = f"{valor:,.{decimales}f}"
    if idioma == "en":
        return texto
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
