
"""
# -- --------------------------------------------------------------------------------------------------- -- #
# -- project: A SHORT DESCRIPTION OF THE PROJECT                                                         -- #
# -- script: data.py : python script for data collection                                                 -- #
# -- author: YOUR GITHUB USER NAME                                                                       -- #
# -- license: GPL-3.0 License                                                                            -- #
# -- repository: YOUR REPOSITORY URL                                                                     -- #
# -- --------------------------------------------------------------------------------------------------- -- #
"""
import os
import numpy as np
import pandas as pd
import time
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# 1.1 Obtener la lista de los archivos a leer data.py
#%%
path = '/Users/Catalina/Documents/ITESO/MST/myst_if708925_lab1/files/NAFTRAC_holdings'
abspath = os.path.abspath(path)
archivos = [f[:-4] for f in os.listdir(abspath) if os.path.isfile(os.path.join(abspath, f))]


# 1.2 leer todos los archivos y guardarlos en un diccionario functions.py
data_archivos = {}
for i in archivos:
    # i = achivos[0]
    # leer archivos despues de los primeros 2 renglones
    data = pd.read_csv('files/NAFTRAC_holdings/' + i + '.csv', skiprows=2, header=None)
    # renombrar columnas
    data.columns = list(data.iloc[0, :])
    data = data.loc[:, pd.notnull(data.columns)]
    data = data.iloc[1:-1].reset_index(drop=True, inplace=False)
    # quitar comas
    data['Precio'] = [i.replace(',','') for i in data['Precio']]
    # quitar asteriscos
    data['Ticker'] = [i.replace('*','') for i in data['Ticker']]
    convert_dict = {'Ticker': str, 'Nombre': str, 'Peso (%)': float, 'Precio': float}
    data = data.astype(convert_dict)
    # convertir a decimal la columna de peso
    data['Peso (%)'] = data['Peso (%)']/100
    # guardar en diccionario
    data_archivos[i] = data

# 1.3 Construir el vector de fechas a partir del vector de nombres de archivos functions.py
# sirve como etiqueta en dataframe y para yfinance
t_fechas = [i.strftime('%d-%m-%Y') for i in sorted([pd.to_datetime(i[8:]).date() for i in archivos])]
#lista con fechas ordenadas para usarse como indexadores de archivos
i_fechas = [j.strftime('%Y-%m-%d') for j in sorted([pd.to_datetime(i[8:]).date() for i in archivos])]
# 1.4 Construir el vector de tickers utilizables en yahoo finance functions.py
# -- descargar y acomodar los datos
ticker = []
for i in archivos:
    # i = archivos[1]
    l_tickers = list(data_archivos[i]['Ticker'])
    print(l_tickers)
    [ticker.append(i + '.MX') for i in l_tickers]
#lista global (todos los datos que vamos a necesitar para descargar)
global_tickers = np.unique(ticker).tolist()

# 1.5 Obtener posiciones historicas main.py
global_tickers = [i.replace('GFREGIOO.MX', 'RA.MX') for i in global_tickers]
global_tickers = [i.replace('MEXCHEM.MX', 'ORBIA.MX') for i in global_tickers]
global_tickers = [i.replace('LIVEPOLC.1.MX', 'LIVEPOLC-1.MX') for i in global_tickers]

# ELIMINAR MXN, USD, KOFL y usar como cash
#cuando se utiliza KOF, ese % o ponderacion se tiene que pasar a CASH
[global_tickers.remove(i) for i in ['MXN.MX', 'USD.MX', 'KOFL.MX', 'KOFUBL.MX', 'BSMXB.MX']]
# contar el tiempo que tarda
inicio = time.time()
# descarga de yahoofinance
data = yf.download(global_tickers, start="2018-01-31", end="2020-08-25", actions=False,
                   group_by="close", interval='1d', auto_adjust=False, prepost=False, threads=True)

print('se tardo', round(time.time() - inicio, 2), 'segundos')
#convertir columna de fechas de cierre en un dataframe
data_close = pd.DataFrame({i: data[i]['Close'] for i in global_tickers})

# tomar solo las fechas de interes y ponerlas en una lista
ic_fechas = sorted(list(set(data_close.index.astype(str).tolist()) & set(i_fechas)))

#localizar todos los precios (encontrar todos los precios de cada mes)
precios = data_close.iloc[[int(np.where(data_close.index.astype(str) == i)[0]) for i in ic_fechas]]

# ordenar columnas lexicograficamente
precios = precios.reindex(sorted(precios.columns), axis=1)

# tomar solo las columnas de interes
# transponer matriz para tener x: fechas, y: precios
# multiplicar matriz de precios por matriz de pesos
# hacer suma de cada columna para obtener valor de mercado

# 1.6 posicion inicial main.py
#capital inicial
k = 1000000
#comision
c = 0.00125
#vector de comisiones historicas
comisiones = []

# obtener posicion inicial, los % para KOFL, KOFUBL, BSMXB, USD asignarlos a cash
#quitar tickers cuando aparezcan. la suma de lo que te gastaste en hace las posiciones de el resto
#entonces la diferencia es el CASH
c_activos = ['KOFL', 'KOFUBL', 'BSMXB', 'MXN', 'USD']

#diccionario para resultado final
inv_pasiva = {'timestamp': t_fechas, 'capital': [k]}

# ------------------------------------------------------------------------------------------------------------------
# 1.7 Evolucion de la postura (Inversion pasiva) visualization.py

pos_datos = data_archivos[archivos[0]].copy().sort_values('Ticker')[['Ticker', 'Nombre', 'Peso (%)']]
# extraer la lista de activos a eliminar
i_activos = list(pos_datos[list(pos_datos['Ticker'].isin(c_activos))].index)
# eliminar los activos del dataframe
pos_datos.drop(i_activos, inplace=True)
# resetear el index
pos_datos.reset_index(inplace=True, drop=True)
# agregar .MX para empatar precios
pos_datos['Ticker'] = pos_datos['Ticker'] + '.MX'
#corregir tickers en datos
pos_datos['Ticker'] = pos_datos['Ticker'].replace('LIVEPOLC.1.MX', 'LIVEPOLC-1.MX')
pos_datos['Ticker'] = pos_datos['Ticker'].replace('MEXCHEM.MX', 'ORBIA.MX')
pos_datos['Ticker'] = pos_datos['Ticker'].replace('GFREGIOO.MX', 'RA.MX')
# fecha para la que se busca hacer el match de precios
match = 0
# precios necesarios para la posicion
pos_datos['Precio'] = [precios.iloc[match, precios.columns.to_list().index(i)] for i in pos_datos['Ticker']]
pos_datos['Capital'] = pos_datos['Peso (%)'] * k - pos_datos['Peso (%)'] * k * c

# cantidad de titulos por accion (solo se hace una vez)
pos_datos['Titulos'] = pos_datos['Capital'] // pos_datos['Precio']
# valor de la postura por accion (solo se hace una vez)
pos_datos['Postura'] = pos_datos['Titulos'] * pos_datos['Precio']
# comision pagada (solo se hace una vez)
pos_datos['Comision'] = pos_datos['Postura'] * c

pos_comision = pos_datos['Comision'].sum()
pos_cash = k - pos_datos['Postura'].sum() - pos_comision
#suma de todas las posiciones
pos_value = pos_datos['Postura'].sum()
capital = pos_value + pos_cash

for i in archivos:
    i = archivos.index(i)
    match = i
    precios.index.to_list()[match]
    # precios necesarios para la posicion
    m2 = [precios.iloc[match, precios.columns.to_list().index(i)] for i in pos_datos['Ticker']]
    pos_datos['Precio'] = m2
    #Postura, precio por cantidad de titulos
    pos_datos['Postura'] = pos_datos['Titulos'] * pos_datos['Precio']
    #suma de todas las posiciones
    pos_value = pos_datos['Postura'].sum()
    inv_pasiva['capital'].append(pos_value + pos_cash)

df_pasiva = pd.DataFrame.from_dict(inv_pasiva, orient='index').transpose()
df_pasiva.set_index('timestamp', inplace=True)
df_pasiva['rend'] = df_pasiva.pct_change()
df_pasiva['rend_acum'] = np.cumsum(df_pasiva['rend'])
df_pasiva = df_pasiva.reset_index()

# ----------------------------------------------------------------------------------------------------------------------
#Inversion Activa
#Tomar el activo con mayor ponderacion el primer mes, y reducir su posicion a la mitad (truncar(division sin decimales)
#esa es la postura individual de cada activo.
# comprola mitad y la otra mitad se suma a cash (sumas lo que tienes en cash con la mitad del activo de la mayor ponderacion)
# para el rebalanceo solo se toma un activo, este al que se le hizo lo de la mitad y este es el que se va a estar rebalanceando
# logica de inversion pasiva: al mes tienes que estar determinando con cuantos activos te quedaste
#cuando tu tienes ese activo, si estas calculando diario tienes que esar poniendo cuanto ha ido evolucoinanado cada
#postura individual, agarrar dataframe

#en lugar de hacerlo por mes se hace por dia con la misma posicion inicial
#excepto que ahora vas a tener la mitad de acciones de los titulos del activo con mayor ponderacion
#la otra mitad se suma a cash, y con esa vas a ir sumandole dia a dia si se cumple la regla SOLO SE MUEVE AMX
#Usar su precio diario y solo comprar
#REGLAS:
    #SI EL DIA ANTERIOR EL PRECIO DE APERTURA ES MAYOR AL DE CIERRE EN 1%
    #CUANTOS?
    #posicion inicial50%de amx , Incrementar un  K=10% de lo que hay disponible de cash DE AMX,
    # hasta llegar al 100% del capital disponible
    #cash +50% rstante de posicion inicial de AMX

#cada mes (igual que en pasiva) en un dataframe que registre los datos de la evolucion de la posicion, actualizar solamente
#los nuevos titulos que se tienen de AMX

#cuando hagas una compra tienes que registrar los titulos que tenias, los que compraste y la comision que pagaste
#la comision se descuenta del cash (cuantos titulos me alcanza para comprar con 1,000 CON TODO Y LA COMISION

# posicion inicial
#capital inicial
k = 1000000
#comision
c = 0.00125
#vector de comisiones historicas
comisiones = []

# obtener posicion inicial, los % para KOFL, KOFUBL, BSMXB, USD asignarlos a cash
#quitar tickers cuando aparezcan. la suma de lo que te gastaste en hace las posiciones de el resto
#entonces la diferencia es el CASH
c_activos = ['KOFL', 'KOFUBL', 'BSMXB', 'MXN', 'USD']

#diccionario para resultado final
inv_pasiva = {'timestamp': t_fechas, 'capital': [k]}

# ------------------------------------------------------------------------------------------------------------------
# -- Evolucion de la postura (Inversion pasiva)

datos_posicion = {}
pos_comision = {}
pos_cash = {}
pos_value = {}
for i in archivos:
    i = archivos.index(i)
    pos_datos = data_archivos[archivos[i]].copy().sort_values('Ticker')[['Ticker', 'Nombre', 'Peso (%)']]
    # extraer la lista de activos a eliminar
    i_activos = list(pos_datos[list(pos_datos['Ticker'].isin(c_activos))].index)
    # eliminar los activos del dataframe
    pos_datos.drop(i_activos, inplace=True)
    # resetear el index
    pos_datos.reset_index(inplace=True, drop=True)
    # agregar .MX para empatar precios
    pos_datos['Ticker'] = pos_datos['Ticker'] + '.MX'
    #corregir tickers en datos
    pos_datos['Ticker'] = pos_datos['Ticker'].replace('LIVEPOLC.1.MX', 'LIVEPOLC-1.MX')
    pos_datos['Ticker'] = pos_datos['Ticker'].replace('MEXCHEM.MX', 'ORBIA.MX')
    pos_datos['Ticker'] = pos_datos['Ticker'].replace('GFREGIOO.MX', 'RA.MX')
    # fecha para la que se busca hacer el match de precios
    match = i
    # precios necesarios para la posicion
    #m1 = np.array(precios.iloc[match, [i in pos_datos['Ticker'].to_list() for i in precios.columns.to_list()]])
    m2 = [precios.iloc[match, precios.columns.to_list().index(i)] for i in pos_datos['Ticker']]
    pos_datos['Precio'] = m2
    # Part\e REAL
    pos_datos['Capital'] = pos_datos['Peso (%)'] * k - pos_datos['Peso (%)'] * k * c
    # cantidad de titulos por accion (solo se hace una vez)
    pos_datos['Titulos'] = pos_datos['Capital'] // pos_datos['Precio']
    # valor de la postura por accion (solo se hace una vez)
    pos_datos['Postura'] = pos_datos['Titulos'] * pos_datos['Precio']
    # comision pagada (solo se hace una vez)
    pos_datos['Comision'] = pos_datos['Postura'] * c
    datos_posicion[i] = pos_datos
    #comision total mensual
    pos_comision[i] = pos_datos['Comision'].sum()

pos_cash[0] = k - datos_posicion[0]['Postura'].sum() - pos_comision[0]
pos_value[0] = datos_posicion[0]['Postura'].sum()
inv_pasiva['capital'].append(pos_value[0] + pos_cash[0])
for i in datos_posicion:
    i = i+1
    # efectivo libre en la postura
    pos_cash[i] = (pos_cash[i-1] + pos_value[i-1]) - pos_datos['Postura'].sum() - pos_comision[i]
    # valor de la posicion
    pos_value[i] = pos_datos['Postura'].sum()
    # actualizar lista de valores de cada llave en el diccionario
    #inv_pasiva['timestamp'].append(t_fechas[0])
    inv_pasiva['capital'].append(pos_value[i] + pos_cash[i])

df_pasiva = pd.DataFrame.from_dict(inv_pasiva, orient='index').transpose()
df_pasiva.set_index('timestamp', inplace=True)
df_pasiva['rend'] = df_pasiva.pct_change()
df_pasiva['rend_acum'] = np.cumsum(df_pasiva['rend'])
df_pasiva = df_pasiva.reset_index()

# ----------------------------------------------------------------------------------------------------------------------
# 5. Medidas de atribucion al desempeno (rendimiento mensual promedio, rendimiento mensual acumulado, sharpe)
rend_pm = df_pasiva['rend'].mean()
rendacumm = df_pasiva['rend'].sum()
sharper = rend_pm/df_pasiva['rend'].std()
medidas = [['Rendimiento mensual promedio', rend_pm], ['Rendimiento mensual acumulado', rendacumm], ['Sharpe ratio', sharper]]
df_medidas = pd.DataFrame(medidas, columns=['descripcion', 'inv_pasiva'])