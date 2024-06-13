# Librerias
import os
import sys
import random
import arcpy
import pandas as pd
import statistics
import unicodedata

# ----------------------------------------------- 1) Obteniendo las variables ----------------------------------------------- #

capa_optimizar = arcpy.GetParameterAsText(0)  # Nombre de la capa a optimizar
aspecto_a_optimizar = arcpy.GetParameterAsText(1) # Aspecto a optimizar, puede ser tiempos o visitas
columna_rutas = arcpy.GetParameterAsText(2) # Nombre de la columna de rutas
columna_frecuencia =  arcpy.GetParameterAsText(3) # Frecuencia de visita semanal
columna_tiempos = arcpy.GetParameterAsText(4) # Columna de tiempos
lista_dias =arcpy.GetParameterAsText(5).replace(";","") # Esto es una cadena de texto
lista_dias = list(lista_dias) # Convierto la cadena de texto en una lista
sujeto_cambios = arcpy.GetParameterAsText(6)  # Columna de suejeto a cambios
num_escenarios = arcpy.GetParameterAsText(7) # Columnan sujerto a cambios
num_escenarios =  int(num_escenarios)
archivo_ruta = rf"{arcpy.GetParameterAsText(8)}" # Ruta a exportar

# --------------------------------------------- 2) Procesamiento de los datos --------------------------------------------- #

# 2.1) Extraccionn de la tabla de atributos de la capa selecionada
data = [row for row in arcpy.da.SearchCursor(capa_optimizar, "*")]
df = pd.DataFrame(data, columns=[f.name for f in arcpy.ListFields(capa_optimizar)])

#  2.2) Tratammiento de na values, si hay na values los pondra por defaul como si sujetos a cambios
df[f"{sujeto_cambios}"].fillna(value="si")

# Declaracion de la funcion que quita acentos
def quitar_acentos(texto):
    texto_sin_acentos = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto_sin_acentos

for i in range (0, len(df)):
    df[sujeto_cambios][i] = df[sujeto_cambios][i].replace(" ", "") # Eliminacion de espacios
    df[sujeto_cambios][i] = df[sujeto_cambios][i].lower() # Todo a minusculas
    df[sujeto_cambios][i] = quitar_acentos(df[sujeto_cambios][i]) # quitamos acenntos

# 2.3)  Extraccion de los clintes sujetos a cambios y clientes no sujtos a cambios
clientes_sujetos = df[df[sujeto_cambios] == "si"]
clientes_sujetos.reset_index(drop=True , inplace=True)
clientes_no_sujetos  = df[df[sujeto_cambios] == "no"]
clientes_no_sujetos.reset_index(drop=True, inplace=True)

# 2.4) Generacion de posibilidades
combinaciones_dias = {
    1: [
        ("L"),
        ("M"),
        ("R"),
        ("J"),
        ("V"),
        ("S")
    ],
    2: [
        ('L', 'J'),
        ('M', 'V'),
        ('R', 'S')
    ],
    3: [
        ('L', 'R', "V"),
        ('M', 'J', 'S')
    ],
    4: [("L", "R", "J", "S"),
        ("M", "R", "V", "S"),
        ("R", "J","V", "S")],
    5: [("L", "M", "R", "J", "V")],
    6:[("L", "M", "R", "J", "V", "S")]
}

# Crear una lista de todas las posibles combinaciones de días para cada cliente
clientes_sujetos['posibilidades'] = clientes_sujetos[f'{columna_frecuencia}'].apply(lambda x: combinaciones_dias[x])

# 2.5) Definicio de funciones
def random_combinacion(argumento):
    aleatorio = random.choice(argumento)

    return aleatorio

def lunes (argumento):
    if "L" in argumento:
        resultado = 1
    else:
        resultado = 0
    return resultado

def martes (argumento):
    if "M" in argumento:
        resultado = 1
    else:
        resultado = 0
    return resultado

def miercoles (argumento):
    if "R" in argumento:
        resultado = 1
    else:
        resultado = 0
    return resultado

def jueves (argumento):
    if "J" in argumento:
        resultado = 1
    else:
        resultado = 0
    return  resultado

def viernes (argumento):
    if "V" in argumento:
        resultado = 1
    else:
        resultado = 0
    return resultado

def sabado (argumento):
    if "S" in argumento:
        resultado = 1
    else:
        resultado = 0
    return resultado

# 2.6) Genenracion de escennrios aleatorios de itinerario

escenarios_global = pd.DataFrame(columns= clientes_sujetos.columns)
escenarios_global["escenario"] = []

# ---------------------------------------- 3) Generacion de escenarios aleatorios ---------------------------------------- #

# Valor inicial
escenarios = 1

while escenarios < num_escenarios:
    clientes_sujetos["itinerario"] = clientes_sujetos["posibilidades"].apply(random_combinacion)
    # Aplicamos las funciones
    clientes_sujetos["L"] = clientes_sujetos["itinerario"].apply(lunes)
    clientes_sujetos["M"] = clientes_sujetos["itinerario"].apply(martes)
    clientes_sujetos["R"] = clientes_sujetos["itinerario"].apply(miercoles)
    clientes_sujetos["J"] = clientes_sujetos["itinerario"].apply(jueves)
    clientes_sujetos["V"] = clientes_sujetos["itinerario"].apply(viernes)
    clientes_sujetos["S"] = clientes_sujetos["itinerario"].apply(sabado)
    clientes_sujetos["escenario"] = escenarios
    # NOTA: En este punto ya se agregaron yu se modificaron las columnas de dias en funcion a los itinerarios aleatrios
    # Ya se tienen la binarizacion de los dias en funcion al escenario aleatorio que salio
    escenarios_global = pd.concat(objs=[escenarios_global, clientes_sujetos], axis=0)
    escenarios = escenarios + 1

# ------------------------------------------- 4) Evaluacion de los escenarios ------------------------------------------- #

# Definimos las funciones globales que se utilizaran en cualquiera de los 2 casos
# Tiempos dias
def tiempos_dias (argumento, tiempo):
    if argumento == 1:
        resultado= tiempo
    else:
        resultado= 0
    return resultado

# Generación de la desviacion estandar por semana
def desviacion_estandar(lunes,martes,miercoles,jueves,viernes,sabado):
    data= [lunes,martes,miercoles,jueves,viernes,sabado]
    desviacion = statistics.stdev(data)
    return desviacion

if aspecto_a_optimizar == "Tiempos":
    # Aplicamos la funcion
    escenarios_global["Tiempos lunes"] = escenarios_global.apply(
        lambda row: tiempos_dias(row["L"], row[f"{columna_tiempos}"]), axis=1)
    escenarios_global["Tiempos martes"] = escenarios_global.apply(
        lambda row: tiempos_dias(row["M"], row[f"{columna_tiempos}"]), axis=1)
    escenarios_global["Tiempos miercoles"] = escenarios_global.apply(
        lambda row: tiempos_dias(row["R"], row[f"{columna_tiempos}"]), axis=1)
    escenarios_global["Tiempos jueves"] = escenarios_global.apply(
        lambda row: tiempos_dias(row["J"], row[f"{columna_tiempos}"]), axis=1)
    escenarios_global["Tiempos viernes"] = escenarios_global.apply(
        lambda row: tiempos_dias(row["V"], row[f"{columna_tiempos}"]), axis=1)
    escenarios_global["Tiempos sabado"] = escenarios_global.apply(
        lambda row: tiempos_dias(row["S"], row[f"{columna_tiempos}"]), axis=1)
    # Agrupamiento y generacion de la desviacion estandar por escenario
    tiempos_vendedor = escenarios_global.groupby(by=[f"{columna_rutas}", "escenario"])[
        "Tiempos lunes", "Tiempos martes", "Tiempos miercoles", "Tiempos jueves", "Tiempos viernes", "Tiempos sabado"].sum().reset_index()
    # Aplicamos la funcion de desviacion
    tiempos_vendedor["Desviacion por escenario"] = tiempos_vendedor.apply(
        lambda row: desviacion_estandar(row["Tiempos lunes"], row["Tiempos martes"], row["Tiempos miercoles"],
                                        row["Tiempos jueves"], row["Tiempos viernes"], row["Tiempos sabado"]), axis=1)
    # Selecionamos el escenario optimo por vendedor
    tiempos_vendedor.sort_values(by=[f"{columna_rutas}", "Desviacion por escenario"], ascending=True, inplace=True)
    tiempos_vendedor.drop_duplicates(subset=[f"{columna_rutas}"], keep="first", inplace=True)
    tiempos_vendedor.reset_index(drop=True, inplace=True)
    # Lo mnergeamos y nos quedamos con esa configuacion optima, junto con el DF original
    tiempos_vendedor = tiempos_vendedor[[f"{columna_rutas}", "escenario"]]
    itinerario_optimo = pd.merge(left=escenarios_global, right=tiempos_vendedor,
                                 on=[f"{columna_rutas}", "escenario"], how="right")
    # Eliminamos las varia(bles de no interes
    itinerario_optimo.drop(columns=["posibilidades", "escenario", "itinerario", "Tiempos lunes",
                                    "Tiempos martes", "Tiempos miercoles", "Tiempos jueves",
                                    "Tiempos viernes", "Tiempos sabado"], inplace=True)
    # Merge final con los clientes sujetos y no sujetos a cambios
    itinerario_optimo = pd.concat(objs=[itinerario_optimo, clientes_no_sujetos], axis=0)
    # Exportacion
    itinerario_optimo.to_excel(archivo_ruta, index=False)

elif aspecto_a_optimizar == "Visitas":
    agenda_vendedor = escenarios_global.groupby(by=[f"{columna_rutas}", "escenario"])["L", "M", "R", "J",
                                                                                        "V", "S"].sum().reset_index()
    # Aplicamos la funcion de desviacion
    agenda_vendedor["Desviacion por escenario"] = agenda_vendedor.apply(
        lambda row: desviacion_estandar(row["L"], row["M"], row["R"], row["J"], row["V"], row["S"]), axis=1)
    # Selecionamos el escenario optimo por vendedor
    agenda_vendedor.sort_values(by=[f"{columna_rutas}", "Desviacion por escenario"], ascending=True, inplace=True)
    agenda_vendedor.drop_duplicates(subset=[f"{columna_rutas}"], keep="first", inplace=True)
    agenda_vendedor.reset_index(drop=True, inplace=True)
    # Lo mnergeamos y nos quedamos con esa configuacion optima, junto con el DF original
    agenda_vendedor = agenda_vendedor[[f"{columna_rutas}", "escenario"]]
    itinerario_optimo = pd.merge(left=escenarios_global, right=agenda_vendedor,
                                 on=[f"{columna_rutas}", "escenario"], how="right")
    itinerario_optimo.drop(columns=["posibilidades", "escenario", "itinerario"], inplace=True)
    # Merge final con los clientes sujetos y no sujetos a cambios
    itinerario_optimo = pd.concat(objs=[itinerario_optimo, clientes_no_sujetos], axis=0)
    # Exportacion
    itinerario_optimo.to_excel(archivo_ruta, index=False)
