import sys
#importamos el modulo cplex
import cplex

TOLERANCE =10e-6

class InstanciaRecorridoMixto:
    def __init__(self):
        self.cantidad_clientes = 0
        self.costo_repartidor = 0
        self.d_max = 0
        self.refrigerados = []
        self.exclusivos = []
        self.distancias = []        
        self.costos = [] 
        self.nombres = []       

    def leer_datos(self,filename):
        # abrimos el archivo de datos
        f = open(filename)

        # Linea 1 --> leemos la cantidad de clientes
        self.cantidad_clientes = int(f.readline())
        # Linea 2 --> leemos el costo por pedido del repartidor
        self.costo_repartidor = int(f.readline())
        # Linea 3 --> leemos la distamcia maxima del repartidor
        self.d_max = int(f.readline())
        
        # inicializamos distancias y costos con un valor muy grande (por si falta algun par en los datos)
        self.distancias = [[1000000 for _ in range(self.cantidad_clientes)] for _ in range(self.cantidad_clientes)]
        self.costos = [[1000000 for _ in range(self.cantidad_clientes)] for _ in range(self.cantidad_clientes)]
        
        # Linea 4 --> leemos la cantidad de refrigerados
        cantidad_refrigerados = int(f.readline())
        # leemos los clientes refrigerados
        for i in range(cantidad_refrigerados):
            self.refrigerados.append(int(f.readline()))
        
        # Linea 4 + exclusivos (5) + 1 --> 10 leemos la cantidad de exclusivos
        cantidad_exclusivos = int(f.readline())
        # leemos los clientes exclusivos
        for i in range(cantidad_exclusivos):
            self.exclusivos.append(int(f.readline()))
        
        # leemos las distancias y costos entre clientes
        lineas = f.readlines()
        for linea in lineas:
            row = list(map(int,linea.split(' ')))
            self.distancias[row[0]-1][row[1]-1] = row[2]
            self.distancias[row[1]-1][row[0]-1] = row[2]
            self.costos[row[0]-1][row[1]-1] = row[3]
            self.costos[row[1]-1][row[0]-1] = row[3]
        
        # cerramos el archivo
        f.close()

def cargar_instancia():
    # El 1er parametro es el nombre del archivo de entrada
    # nombre_archivo = sys.argv[1].strip()
    nombre_archivo = 'instancias/instancia_50_clientes.txt'
    #nombre_archivo = 'instancias/instancia_custom_clientes.txt'
    #nombre_archivo = 'instancias/instancia_def.txt'
    # Crea la instancia vacia
    instancia = InstanciaRecorridoMixto()
    # Llena la instancia con los datos del archivo de entrada 
    instancia.leer_datos(nombre_archivo)
    return instancia

def agregar_variables(prob, instancia):
    # Definir y agregar las variables:
	# metodo 'add' de 'variables', con parametros:
	# obj: costos de la funcion objetivo
	# lb: cotas inferiores
    # ub: cotas superiores
    # types: tipo de las variables
    # names: nombre (como van a aparecer en el archivo .lp)
	
    n = instancia.cantidad_clientes
    cantVar = 2*n*(n-1) + n*2
    # Acá no se porque 2n, asumo que las profes consideraron a zi como una variable,
    
    # Poner nombre a las variables y llenar coef_funcion_objetivo
    coeficientes_funcion_objetivo = []
    tipos = []
    lb = []
    ub = []

    # 1. Agregando las variables xij -->
    # Determina si el camion va del cliente i al j
    c=0
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                c = c+1
                instancia.nombres.append(f'x_{i}_{j}')
                coeficientes_funcion_objetivo.append(instancia.costos[i-1][j-1])
                tipos.append(prob.variables.type.binary)
                lb.append(0)
                ub.append(1)

    print(f'Variables xij {c}')
    # 2. Var. y_ij -->
    # Determina si el repartidor va del cliente i al j
    c = 0
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                c = c+1
                instancia.nombres.append(f'y_{i}_{j}')
                coeficientes_funcion_objetivo.append(instancia.costo_repartidor)
                tipos.append(prob.variables.type.binary)
                lb.append(0)
                ub.append(1)
    print(f'Variables yij {c}')

    # 3. Var. u_i -->
    # Orden de visita del cliente i en el camino del camion.
    c = 0
    for i in range(1, n + 1):
        c = c+1
        instancia.nombres.append(f'u_{i}')
        coeficientes_funcion_objetivo.append(0)
        tipos.append(prob.variables.type.integer)
        lb.append(2 if i != 1 else 1)
        ub.append(n)

    print(f'Variables u_i {c}')

    # 4. Var. z_i -->
    c = 0
    for i in range(1, n + 1):
        c = c+1
        instancia.nombres.append(f'z_{i}')
        coeficientes_funcion_objetivo.append(0)
        tipos.append(prob.variables.type.binary)
        lb.append(0)
        ub.append(1)
    # Indica si el hay repartidor asignado al cliente i para entregar a j


    if len(instancia.nombres) != cantVar:
        print(f'Error en la cantidad de variables, se esperaban {cantVar} y se encontraron {len(instancia.nombres)}')
        return
    
    # Agregar las variables
    prob.variables.add(obj = coeficientes_funcion_objetivo,
                       lb = lb, 
                       ub = ub,
                       types=tipos, 
                       names=instancia.nombres)
    
    return instancia.nombres
    
def evitar_subtours(prob, instancia, n):

    for i in range(1, n + 1): 
        for j in range(1, n+1):  
            if i != j:
                prob.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(
                        ind=[f'u_{i}', f'u_{j}', f'x_{i}_{j}'],
                        val=[1, -1, n-1]
                    )],
                    senses=['L'],
                    rhs=[n-2],
                    names=[f'MTZ_{i}_{j}']
                )

    prob.linear_constraints.add(
    lin_expr=[cplex.SparsePair(ind=[f'u_1'], val=[1])],
    senses=['E'],
    rhs=[1],
    names=['fix_u1']
    )

def cobertura_total(prob, instancia, n):
    for i in range(1, n + 1):
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(
                ind = [f'x_{j}_{i}' for j in range(1, n + 1) if i != j] +
                        [f'y_{j}_{i}' for j in range(1, n + 1) if i != j],
                val = [1] * (2*(n-1))
            )],
            senses=['E'],
            rhs=[1],
            names=[f'visito_{i}']
        )

def distancia_maxima(prob, instancia, n):
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                prob.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(
                        ind=[f'y_{i}_{j}'],
                        val=[instancia.distancias[i-1][j-1]]
                    )],
                    senses=['L'],
                    rhs=[instancia.d_max],
                    names=[f'distancia_{i}_{j}']
                )

def continuidad_camion(prob, instancia, n):
    for i in range(1, n + 1):
        # Entra a i
        entrada = [f'x_{j}_{i}' for j in range(1, n + 1) if i != j]
        # Sale de i
        salida = [f'x_{i}_{j}' for j in range(1, n + 1) if i != j]

        # Restricción
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(
                ind=entrada + salida,
                val=[1] * len(entrada) + [-1] * len(salida)
            )],
            senses=['E'],
            rhs=[0],
            names=[f'continuidad_{i}']
        )

def restriccion_refrigerados(prob, instancia, n):
    for i in range(1, n + 1):
        refrigerados = [j for j in range(1, n + 1) if j in instancia.refrigerados and i != j]
        if refrigerados:
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(
                    ind=[f'y_{i}_{j}' for j in refrigerados] + [f'z_{i}'],
                    val=[1] * len(refrigerados) + [-1]
                )],
                senses=['L'],
                rhs=[0],
                names=[f'refrigerados_{i}']
            )

def activacion_z(prob, instancia, n):
    # Primer constraint:  Si todos los y_ij son 0, entonces z_i = 0
    for i in range(1, n + 1):
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(
                ind=[f'y_{i}_{j}' for j in range(1, n + 1) if i != j] + [f'z_{i}'],
                val=[1] * (n - 1) + [-1]
            )],
            senses=['G'],  
            rhs=[0],       
            names=[f'anti_activacion_z_{i}']
        )
    
    # Segundo constraint:  y_i_j <= z_i para todos los 
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                prob.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(
                        ind=[f'y_{i}_{j}', f'z_{i}'],
                        val=[1] + [-1]
                    )],
                    senses=['L'],  # y_i_j - z_i <= 0
                    rhs=[1],
                    names=[f'activacion_z_{i}_{j}']  
                )

def no_repartidor_en_deposito(prob, instancia, n):
    '''
    y_1_j y y_i_1 deberían ser siempre 0
    '''
    for j in range(1, n + 1):
        # Restricción para y_1_j = 0
        if j != 1:
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(
                    ind=[f'y_{1}_{j}'],
                    val=[1]
                )],
                senses=['E'], 
                rhs=[0],
                names=[f'no_repartidor_en_deposito_{1}_{j}'] 
            )

            # Restricción para y_j_0 = 0    
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(
                    ind=[f'y_{j}_{1}'],
                    val=[1]
                )],
                senses=['E'],
                rhs=[0],
                names=[f'no_repartidor_en_deposito_{j}_{1}'] 
            )

def activacion_z_x(prob, instancia, n):
    for i in range(1, n + 1):
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(
                ind=[f'z_{i}'] + [f'x_{j}_{i}' for j in range(1, n + 1) if i != j],
                val=[-1] + [1] * (n - 1)
        )],
        senses=['G'],
        rhs=[0],
        names=[f'activacion_z_x_{i}']
        )

def minimo_bicicletas(prob, instancia, n, minimo):
    '''
    Para todas las combinaciones de i j al menos tiene que haber minimo bicicletas
    '''
    prob.linear_constraints.add(
        lin_expr=[cplex.SparsePair(
            ind=[f'y_{i}_{j}' for i in range(n) for j in range(n) if i != j],
            val=[1] * (n * (n - 1))
        )],
        senses=['G'],
        rhs=[minimo],
        names=[f'minimo_bicicletas']
    )

def agregar_restricciones(prob, instancia):
    # Agregar las restricciones ax <= (>= ==) b:
	# funcion 'add' de 'linear_constraints' con parametros:
	# lin_expr: lista de listas de [ind,val] de a
    # sense: lista de 'L', 'G' o 'E'
    # rhs: lista de los b
    # names: nombre (como van a aparecer en el archivo .lp)

    # Notar que cplex espera "una matriz de restricciones", es decir, una
    # lista de restricciones del tipo ax <= b, [ax <= b]. Por lo tanto, aun cuando
    # agreguemos una unica restriccion, tenemos que hacerlo como una lista de un unico
    # elemento.

    n = instancia.cantidad_clientes
    
    # 1. Evitar subtours con la formulación de Miller-Tucker-Zemlin
    # u_i - u_j + n*x_ij <= n-1 para i,j != 0
    evitar_subtours(prob, instancia, n)

    # 2. Visitar a todos los clientes
    cobertura_total(prob, instancia, n)

    # 3. Continuidad del camión
    continuidad_camion(prob, instancia, n)

    # 4. Distancia máxima
    distancia_maxima(prob, instancia, n)

    # 5. Productos refrigerados (ri)
    restriccion_refrigerados(prob, instancia, n)
    
    # 6. Activación de Zi
    activacion_z(prob, instancia, n)

    # 7. No repartidor en deposito
    no_repartidor_en_deposito(prob, instancia, n)

    # 8. Activación de Zi con Xij
    activacion_z_x(prob, instancia, n)





    # 4. Restricciones con zi
    # 4.a. zi = 1 si el cliente i tiene repartidor asignado

    # 5. Productos refrigerados (ri) 



def armar_lp(prob, instancia):

    # Agregar las variables
    nombres = agregar_variables(prob, instancia)
   
    # Agregar las restricciones 
    agregar_restricciones(prob, instancia)

    # Setear el sentido del problema
    prob.objective.set_sense(prob.objective.sense.minimize)

    # Escribir el lp a archivo
    prob.write('recorridoMixto.lp')

    return nombres

def resolver_lp(prob):
    
    # Definir los parametros del solver
    prob.parameters.mip.tolerances.mipgap.set(1e-10)
       
    # Resolver el lp
    prob.solve()

def mostrar_solucion(prob,instancia, nombres):
    n = instancia.cantidad_clientes

    # Obtener informacion de la solucion a traves de 'solution'
    
    # Tomar el estado de la resolucion
    status = prob.solution.get_status_string(status_code = prob.solution.get_status())
    
    # Tomar el valor del funcional
    try:
        valor_obj = prob.solution.get_objective_value()
    except:
        print(cplex.FeasoptInterface.get_feasibilities(prob.solution))
    valor_obj = prob.solution.get_objective_value()
    
    print('Funcion objetivo: ',valor_obj,'(' + str(status) + ')')
    
    # Tomar los valores de las variables
    solution_values = prob.solution.get_values()
    x_values = {}
    y_values = {}
    u_values = {}

    # Extracción x
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                var_name = f'x_{i}_{j}'
                x_values[(i, j)] = solution_values[nombres.index(var_name)]

    # Extracción y
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                var_name = f'y_{i}_{j}'
                y_values[(i, j)] = solution_values[nombres.index(var_name)]

    # Extracción u
    for i in range(1, n + 1):
        var_name = f'u_{i}'
        u_values[i] = solution_values[nombres.index(var_name)]
    
    # Extracción z
    z_values = {}
    for i in range(1, n + 1):
        var_name = f'z_{i}'
        z_values[i] = solution_values[nombres.index(var_name)]

    # Mostrar las variables con valor positivo (mayor que una tolerancia)
    print('Variables con valor positivo:')
    vars_x_con_valor_positivo = {}
    vars_y_con_valor_positivo = {}
    vars_u_con_valor_positivo = {}
    vars_z_con_valor_positivo = {}
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j and x_values[(i, j)] > TOLERANCE:
                vars_x_con_valor_positivo[(i, j)] = x_values[(i, j)]
        for j in range(1, n + 1):
            if i != j and y_values[(i, j)] > TOLERANCE:
                vars_y_con_valor_positivo[(i, j)] = y_values[(i, j)]
        if u_values[i] > TOLERANCE:
            vars_u_con_valor_positivo[i] = u_values[i]
        if z_values[i] > TOLERANCE:
            vars_z_con_valor_positivo[i] = z_values[i]

    # Ordenar las variables de x
    ruta_ordenada = []
    nodo_inicial = 0

    while len(ruta_ordenada) < len(vars_x_con_valor_positivo):
        for (i,j), value in vars_x_con_valor_positivo.items():
            if i == nodo_inicial:
                ruta_ordenada.append((i,j))
                nodo_inicial = j
                break
    
    # Filtrando para mostrar solo las variables u que corresponden
    # A los clientes visitados por camión
    clientes_ruta = set([x for x, _ in ruta_ordenada])
    u_filtrados_ordenados = dict()
    for i, j in vars_u_con_valor_positivo.items():
        if i in clientes_ruta:
            u_filtrados_ordenados[i] = j
            u_filtrados_ordenados = dict(sorted(u_filtrados_ordenados.items(), key=lambda item: item[1]))
            
    print('---------------------------------')
    print('x:')
    print(ruta_ordenada)
    print('---------------------------------')
    print('y:')
    print(vars_y_con_valor_positivo)
    print('---------------------------------')
    print('u:')
    print(u_filtrados_ordenados)
    print('---------------------------------')
    print('z:')
    print(vars_z_con_valor_positivo)
    print('---------------------------------')


def main():
    
    # Lectura de datos desde el archivo de entrada
    instancia = cargar_instancia()
    
    # # Definicion del problema de Cplex
    prob = cplex.Cplex()
    
    # # Definicion del modelo
    nombres = armar_lp(prob,instancia)

    # # Resolucion del modelo
    resolver_lp(prob)
    print()

    # # Obtencion de la solucion
    mostrar_solucion(prob,instancia, nombres)

if __name__ == '__main__':
    main()