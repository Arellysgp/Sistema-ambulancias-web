# Servicio para el cálculo de rutas inteligentes

def calcular_ruta(origen, destino):
    """
    Simula el cálculo de la ruta más eficiente
    entre una ambulancia y una emergencia.
    """

    ruta = {
        "origen": origen,
        "destino": destino,
        "distancia_estimada": "7.5 km",
        "tiempo_estimado": "10 minutos",
        "estado": "Ruta calculada correctamente"
    }

    return ruta


# Ejemplo de prueba del servicio
if __name__ == "__main__":

    resultado = calcular_ruta(
        "Hospital Dos de Mayo",
        "Av. Abancay 1234"
    )

    print(resultado)