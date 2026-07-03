"""Formato numérico compartido por los reportes descargables.

Módulo sin dependencias pesadas (solo formatea texto) para que tanto el brief
Markdown (`reporte/generar.py`) como el PDF (`reporte/pdf.py`) usen la misma
lógica de separadores por idioma sin duplicarla.
"""


def numero(valor: float, decimales: int = 1, idioma: str = "es") -> str:
    """Número con separadores según idioma.

    Base (Python): miles con coma y decimal con punto → inglés directo. Para
    español se intercambian a miles con punto y decimal con coma.
    """
    texto = f"{valor:,.{decimales}f}"
    if idioma == "en":
        return texto
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
