import random

def generar_archivo_datos(filename):
    # Seed
    random.seed(1234)

    # Cantidad de clientes
    cantidad_clientes = 50
    costo_repartidor = 3
    d_max = 5
    cantidad_refrigerados = 3
    cantidad_exclusivos = 3

    # Generamos los clientes refrigerados con reemplazo
    refrigerados = random.choices(range(1, cantidad_clientes + 1), k=cantidad_refrigerados)

    # Generamos los clientes exclusivos sin reemplazo
    exclusivos = random.sample(range(1, cantidad_clientes + 1), cantidad_exclusivos)

    # Abrimos el archivo para escribir los datos
    with open(filename, 'w') as f:
        # Línea 1: cantidad de clientes
        f.write(f"{cantidad_clientes}\n")
        
        # Línea 2: costo del repartidor
        f.write(f"{costo_repartidor}\n")
        
        # Línea 3: distancia máxima
        f.write(f"{d_max}\n")
        
        # Línea 4: cantidad de refrigerados
        f.write(f"{cantidad_refrigerados}\n")
        
        # Lista de refrigerados
        for r in refrigerados:
            f.write(f"{r}\n")
        
        # Línea 4 + exclusivos (5) + 1 --> cantidad de exclusivos
        f.write(f"{cantidad_exclusivos}\n")
        
        # Lista de exclusivos
        for e in exclusivos:
            f.write(f"{e}\n")
        
        # Generamos distancias y costos entre clientes (solo i < j)
        for i in range(1, cantidad_clientes + 1):
            for j in range(i + 1, cantidad_clientes + 1):
                distancia = random.randint(1, 10)
                costo = distancia
                f.write(f"{i} {j} {distancia} {costo}\n")

# Llamamos a la función para generar el archivo
generar_archivo_datos('instancias/instancia_50_clientes.txt')