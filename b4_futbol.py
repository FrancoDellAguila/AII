#encoding:utf-8

import sqlite3
from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def extraer_jornadas():
    f = urllib.request.urlopen("http://resultados.as.com/resultados/futbol/primera/2023_2024/calendario/")
    s = BeautifulSoup(f,"lxml")
    
    #Lista de todos los divs que tengan las clases dadas en el array
    l = s.find_all("div", class_= ["cont-modulo","resultados"])
    return l

#LISTADO TOTAL DE JORNADAS
def imprimir_lista(cursor):
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    #Lista que se muestra al pulsar "Listar Jornadas"
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    jornada=0
    #Para cada linea de la BD
    for row in cursor:
        #Si no estamos en la jornada 0
        if row[0] != jornada:
            #Se añade salto de linea
            jornada=row[0]
            lb.insert(END,"\n")
            #Se añade el texto "JORNADA 1, JORNADA 2..." y una separación con guiones
            s = 'JORNADA '+ str(jornada)
            lb.insert(END,s)
            lb.insert(END,"-----------------------------------------------------")
        #Se añade La linea
        #consistente en un espacio de identación, nombre del equipo (row1), goles(row3),
        #guión, goles(row4), nombre del otro equipo(row2)
        s = "     " + row[1] +' '+ str(row[3]) +'-'+ str(row[4]) +' '+  row[2]
        lb.insert(END,s)
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)
 
def almacenar_bd():
    conn = sqlite3.connect('as.db')
    conn.text_factory = str  # para evitar problemas con el conjunto de caracteres que maneja la BD
    conn.execute("DROP TABLE IF EXISTS JORNADAS") 
    conn.execute('''CREATE TABLE JORNADAS
       (JORNADA       INTEGER NOT NULL,
       LOCAL          TEXT    NOT NULL,
       VISITANTE      TEXT    NOT NULL,
       GOLES_L        INTEGER    NOT NULL,
       GOLES_V        INTEGER NOT NULL,
       LINK           TEXT);''')
    l = extraer_jornadas()
    for i in l:
        #Siguiendo la expresión regular "uno o más digitos", busca en los id del HTML y
        #dame el primer resultado
        jornada = int(re.compile('\d+').search(i['id']).group(0))
        #Selecciona todos los tr del HTML que tengan id
        partidos = i.find_all("tr",id=True)
        for p in partidos:
            #Lista de aquellos span del HTML con esa clase (dará 2 resultados), luego se
            #separan los equipos
            equipos= p.find_all("span",class_="nombre-equipo")
            local = equipos[0].string.strip()
            visitante = equipos[1].string.strip()
            #a del HTML con esa clase, CUIDADO ES UN ENLACE
            resultado_enlace = p.find("a",class_="resultado")
            #De haber resultado
            if resultado_enlace != None:
                #Siguiendo la expresión "uno o más dígitos, caracter cualquiera las
                #veces que sea y uno o más digitos", se busca en el link PASADO A STRING
                goles=re.compile('(\d+).*(\d+)').search(resultado_enlace.string.strip())
                #Se separan en los goles del local y del visitante
                #group(0) sacaría "0 - 0", group(1) y group(2) solo busca lo que está en
                #los parentesis de la expresión regular
                goles_l=int(goles.group(1))
                goles_v=int(goles.group(2))
                #Se obtiene el link como tal, buscando que tenga la clase href de HTML
                link = resultado_enlace['href']
                
                conn.execute("""INSERT INTO JORNADAS VALUES (?,?,?,?,?,?)""",(jornada,local,visitante,goles_l,goles_v,link))
    conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM JORNADAS")
    
    messagebox.showinfo( "Base Datos", "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()


def listar_bd():
    conn = sqlite3.connect('as.db')
    conn.text_factory = str  
    cursor = conn.execute("SELECT * FROM JORNADAS ORDER BY JORNADA")
    imprimir_lista(cursor)
    conn.close()
    
#BUSCADOR DE JORNADA
def buscar_jornada():
    #Necesita de un parámetro si la llamada ha sido pulsando tecla (bind), aunque nunca
    #se use. No hay motivo, simplemene así es como funciona
    def listar_busqueda(event):
        conn = sqlite3.connect('as.db')
        conn.text_factory = str
        #Se obtiene el texto que haya en la barra y se pasa a integer
        s =  int(en.get())
        #Se pasa el parametro de la jornada EN FORMA DE TUPLA. No hay motivo, simplemene
        #así es como funciona
        cursor = conn.execute("""SELECT * FROM JORNADAS WHERE JORNADA = ?""",(s,)) 
        imprimir_lista(cursor)       
        conn.close()
    
    conn = sqlite3.connect('as.db')
    conn.text_factory = str
    cursor= conn.execute("""SELECT DISTINCT JORNADA FROM JORNADAS""")
    valores=[i[0] for i in cursor]
    conn.close()
    
    #Crear ventana y darle título
    v = Toplevel()
    # Texto sobre el buscador
    lb = Label(v, text="Seleccione la jornada: ")
    lb.pack(side = LEFT)
    #
    en = Spinbox(v,values=valores,state="readonly")
    en.bind("<Return>", listar_busqueda)
    en.pack(side = LEFT)

#ESTADÍSTICAS
def estadistica_jornada():
    def listar_estadistica(event):
        conn = sqlite3.connect('as.db')
        conn.text_factory = str
        #Se obtiene el texto que haya en la barra y se pasa a integer
        s =  int(en.get())
        #Se pasa el parametro de la jornada EN FORMA DE TUPLA. No hay motivo, simplemene
        #así es como funciona
        cursor = conn.execute("""SELECT SUM(GOLES_L)+SUM(GOLES_V) FROM JORNADAS WHERE JORNADA = ?""",(s,)) 
        #Como lo que se devuelve es un array, se toma el primer valor
        total_goles = cursor.fetchone()[0]
        
        #Se obtienen lineas de goles de cada equipo
        cursor = conn.execute("""SELECT GOLES_L,GOLES_V FROM JORNADAS WHERE JORNADA = ?""",(s,))
        empates=0
        locales=0
        visitantes=0
        #Se decide si ha ganado el equipo en la posicion 0 del array (local), perdido o empate
        for g in cursor:
            if g[0] == g[1]:
                empates +=1 
            elif g[0] > g[1]:
                locales +=1
            else:
                visitantes +=1          
        conn.close()
        
        s = "TOTAL GOLES JORNADA : " + str(total_goles)+ "\n\n" + "EMPATES : " + str(empates) + "\n" + "VICTORIAS LOCALES : " + str(locales) + "\n" + "VICTORIAS VISITANTES : " + str(visitantes)
        v = Toplevel()
        lb = Label(v, text=s) 
        lb.pack()
        
    conn = sqlite3.connect('as.db')
    conn.text_factory = str
    cursor= conn.execute("""SELECT DISTINCT JORNADA FROM JORNADAS""")
    valores=[i[0] for i in cursor]
    conn.close()
    
    v = Toplevel()
    lb = Label(v, text="Seleccione la jornada: ")
    lb.pack(side = LEFT)  
    en = Spinbox(v, values=valores, state="readonly" )
    en.bind("<Return>", listar_estadistica)
    en.pack(side = LEFT)
    


   
def buscar_goles():
    
    def mostrar_equipo_l():
        #actualiza la lista de los equipos que juegan como local en la jornada seleccionada
        conn = sqlite3.connect('as.db')
        conn.text_factory = str
        cursor= conn.execute("""SELECT LOCAL FROM JORNADAS WHERE JORNADA=? """,(int(en_j.get()),))
        en_l.config(values=[i[0] for i in cursor])
        conn.close()
        
    def mostrar_equipo_v():
        #actualiza el equipo que juega como visitante en la jornada y equipo local seleccionados
        conn = sqlite3.connect('as.db')
        conn.text_factory = str
        cursor = conn.execute("""SELECT VISITANTE FROM JORNADAS WHERE JORNADA=? AND LOCAL LIKE ?""",(int(en_j.get()),en_l.get()))
        en_v.config(textvariable=vis.set(cursor.fetchone()[0]))
        conn.close
        
    def cambiar_jornada():
        #se invoca cuando cambia la jornada
        mostrar_equipo_l()
        mostrar_equipo_v()
            
    def listar_busqueda():
        conn = sqlite3.connect('as.db')
        conn.text_factory = str
        cursor = conn.execute("""SELECT LINK,LOCAL,VISITANTE FROM JORNADAS WHERE JORNADA=? AND LOCAL LIKE ? AND VISITANTE LIKE ?""",(int(en_j.get()),en_l.get(),en_v.get()))
        partido = cursor.fetchone()
        enlace = partido[0]
        conn.close()
        f = urllib.request.urlopen(enlace)
        so = BeautifulSoup(f,"lxml")
        #buscamos los goles del equipo local
        l = so.find("header",class_="scr-hdr").find("div", class_="is-local").find("div", class_="scr-hdr__scorers").find_all("span")
        s=""
        for g in l:
            if not g.has_attr("class"): #comprobamos que no sea una tarjeta
                s = s + g.string.strip()
        #buscamos los goles del equipo visitante
        l = so.find("header",class_="scr-hdr").find("div", class_="is-visitor").find("div", class_="scr-hdr__scorers").find_all("span")
        s1=""
        for g in l:
            if not g.has_attr("class"): 
                s1 = s1 + g.string.strip()
        
        goles= partido[1] + " : " + s + "\n" + partido[2] + " : " + s1
                      
        v = Toplevel()
        lb = Label(v, text=goles) 
        lb.pack()
    
    conn = sqlite3.connect('as.db')
    conn.text_factory = str
    #lista de jornadas para la spinbox de seleccion de jornada
    cursor= conn.execute("""SELECT DISTINCT JORNADA FROM JORNADAS""")
    valores_j=[int(i[0]) for i in cursor]
    #lista de los equipos que juegan como local en la jornada seleccionada
    cursor= conn.execute("""SELECT LOCAL FROM JORNADAS WHERE JORNADA=?""",(int(valores_j[0]),))
    valores_l=[i[0] for i in cursor]
    conn.close()
    
    v = Toplevel()
    lb_j = Label(v, text="Seleccione jornada: ")
    lb_j.pack(side = LEFT)
    en_j = Spinbox(v,values=valores_j,command=cambiar_jornada,state="readonly")
    en_j.pack(side = LEFT)
    lb_l = Label(v, text="Seleccione equipo local: ")
    lb_l.pack(side = LEFT)
    en_l = Spinbox(v,values=valores_l,command=mostrar_equipo_v,state="readonly")
    en_l.pack(side = LEFT)
    lb_v = Label(v, text="Equipo visitante: ")
    lb_v.pack(side = LEFT)
    vis=StringVar() #variable para actualizar el equipo visitante 
    en_v = Entry(v,textvariable=vis,state=DISABLED)
    en_v.pack(side = LEFT)
    mostrar_equipo_v() #funcion para mostrar el equipo visitante en funcion de la jornada y el local
    buscar = Button(v, text="Buscar goles", command=listar_busqueda)
    buscar.pack(side=BOTTOM)


    
def ventana_principal():
    top = Tk()
    almacenar = Button(top, text="Almacenar Resultados", command = almacenar_bd)
    almacenar.pack(side = TOP)
    listar = Button(top, text="Listar Jornadas", command = listar_bd)
    listar.pack(side = TOP)
    Buscar = Button(top, text="Buscar Jornada", command = buscar_jornada)
    Buscar.pack(side = TOP)
    Buscar = Button(top, text="EstadÃ­sticas Jornada", command = estadistica_jornada)
    Buscar.pack(side = TOP)
    Buscar = Button(top, text="Buscar Goles", command = buscar_goles)
    Buscar.pack(side = TOP)
    top.mainloop()
    

if __name__ == "__main__":
    ventana_principal()