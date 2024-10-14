#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import datetime
# lineas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context



def cargar():
    #Mensaje de alerta, comprueba si has pulsado si
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operaciÃ³n puede ser lenta")
    if respuesta:
        almacenar_bd()

def almacenar_bd():
    
    #Conexión, borra la tabla por si ya existe y la crea de nuevo
    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS PELICULA")
    conn.execute('''CREATE TABLE PELICULA
       (TITULO            TEXT NOT NULL,
        TITULO_ORIGINAL    TEXT        ,
        PAIS      TEXT,
        FECHA            DATE,          
        DIRECTOR         TEXT,
        GENEROS        TEXT);''')

    #Se obtiene la web desde su URL
    f = urllib.request.urlopen("https://www.elseptimoarte.net/estrenos/")
    s = BeautifulSoup(f, "lxml")
    
    #Dentro de ul de HTML con clase elements, se toma como array todos los li, contienen
    #toda la info de las pelis
    print(s.prettify())
    lista_link_peliculas = s.find("ul", class_="elements").find_all("li")
    
    #Para cada link
    for link_pelicula in lista_link_peliculas:
        #Se obtiene la URL que lleva a esa peli en específico, .a['href'] porque el href
        #dentro del a en HTML es lo que tiene el link como tal
        f = urllib.request.urlopen("https://www.elseptimoarte.net/"+link_pelicula.a['href'])
        s = BeautifulSoup(f, "lxml")
        
        #Busca en el main de HTML con clase "informativo", dentro de este el section con
        #clase "highlight", pasa a un div SIN CLASE y dentro de este
        #un dl SIN CLASE, por eso usa .div y .dl
        datos = s.find("main", class_="informativo").find("section",class_="highlight").div.dl
        
        #Busca en el dt con el texto "Título original" el dd hijo mas cercano, que es el
        #que contiene el nombre como tal .strip() elimina espacios en blanco de antes y despues
        titulo_original = datos.find("dt",string="Título original").find_next_sibling("dd").string.strip()
        
        #si no tiene título traducido se pone el título original
        if (datos.find("dt",string="Título")):
            titulo = datos.find("dt",string="Título").find_next_sibling("dd").string.strip()
        else:
            titulo = titulo_original  
            
        #Obtiene el pais, lo de "" es una trampita para sacarlo mas facilmente
        #Stripped_strings elimina todos los elementos HTML de dentro del dd (en este
        #caso, hay un a con href y title)
        #y se queda con el string, sin espacios    
        pais = "".join(datos.find("dt",string="País").find_next_sibling("dd").stripped_strings)
        
        #Se obtiene la fecha en string, y se formatea con la correspondiente expresión regular
        fecha = datetime.strptime(datos.find("dt",string="Estreno en España").find_next_sibling("dd").string.strip(), '%d/%m/%Y')
        
        #Se obtienen mas datos
        generos_director = s.find("div",id="datos_pelicula")
        generos = "".join(generos_director.find("p",class_="categorias").stripped_strings)
        director = "".join(generos_director.find("p",class_="director").stripped_strings)        

        #Se añaden todos los datos a la BD
        conn.execute("""INSERT INTO PELICULA (TITULO, TITULO_ORIGINAL, PAIS, FECHA, DIRECTOR, GENEROS) VALUES (?,?,?,?,?,?)""",
                     (titulo,titulo_original,pais,fecha,director,generos))
    conn.commit()
    
    #Se realiza un conteo de las películas que hay en la BD, para que se muestre en el
    #mensaje de alerta final
    cursor = conn.execute("SELECT COUNT(*) FROM PELICULA")
    messagebox.showinfo("Base Datos",
                        "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()


def buscar_por_titulo():  
    def listar(event):
            conn = sqlite3.connect('peliculas.db')
            conn.text_factory = str
            #Se usa LIKE % porque como buscamos por título, permite que no haya que escribirlo entero
            cursor = conn.execute("SELECT TITULO, PAIS, DIRECTOR FROM PELICULA WHERE TITULO LIKE '%" + str(entry.get()) + "%'")
            conn.close
            listar_peliculas(cursor)
            
    #Se crea ventana con barra de búsqueda que responde al Intro
    ventana = Toplevel()
    label = Label(ventana, text="Introduzca cadena a buscar ")
    label.pack(side=LEFT)
    entry = Entry(ventana)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)

    

def buscar_por_fecha():
    #Si lo quieres dejar dentro por no pasar parámetros (?), la función debe recibir uno
    #de todos modos aunque no lo uses, si no peta
    def listar(event):
            conn = sqlite3.connect('peliculas.db')
            conn.text_factory = str
            #Se formatea la fecha y se usa como parámetro, pasándolo como tupla, es así como funciona
            try:
                fecha = datetime.strptime(str(entry.get()),"%d-%m-%Y")
                cursor = conn.execute("SELECT TITULO, FECHA FROM PELICULA WHERE FECHA > ?", (fecha,))
                conn.close
                listar_peliculas_1(cursor)
            except:
                conn.close
                messagebox.showerror(title="Error",message="Error en la fecha\nFormato dd-mm-aaaa")  
    
    #Se crea una ventana que tiene un input de estos de flechita arriba y abajo. El
    #input responde al Intro
    v = Toplevel()
    label = Label(v, text="Introduzca la fecha (dd-mm-aaaa) ")
    label.pack(side=LEFT)
    entry = Entry(v)
    #Se le pasa como parámetro el texto introducido en la barra de búsqueda
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)



def buscar_por_genero():
    def listar(Event):
            conn = sqlite3.connect('peliculas.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT TITULO, FECHA FROM PELICULA where GENEROS LIKE '%" + str(entry.get())+"%'")
            conn.close
            listar_peliculas_1(cursor)
    
    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT GENEROS FROM PELICULA")
    
    generos=set()
    for i in cursor:
        generos_pelicula = i[0].split(",")
        for genero in generos_pelicula:
            generos.add(genero.strip())

    v = Toplevel()
    label = Label(v, text="Seleccione un gÃ©nero ")
    label.pack(side=LEFT)
    entry = Spinbox(v, values=list(generos), state='readonly')
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)
    
    conn.close()



def listar_peliculas_1(cursor):
    #Se crea ventana nueva, con scroll vertical y listado que responde al scroll
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    #Para cada resultado de pelicula
    for row in cursor:
        s = 'TÃTULO: ' + row[0]
        lb.insert(END, s)
        lb.insert(END, "-----------------------------------------------------")
        #SQLite almacena las fechas como str, así que hay que parsearlo
        fecha = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        s = "     FECHA DE ESTRENO: " + datetime.strftime(fecha,"%d/%m/%Y")
        lb.insert(END, s)
        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)

    
    
def listar_peliculas(cursor):  
    #Se crea ventana nueva, con scroll vertical y listado que responde al scroll    
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    #Para cada resultado de pelicula
    for row in cursor:
        #Se crea título y se añade al listado
        s = 'TÃTULO: ' + row[0]
        lb.insert(END, s)
        lb.insert(END, "------------------------------------------------------------------------")
        #Se crea el pais + director y se añade, luego se mete salto de línea
        s = "     PAÃS: " + str(row[1]) + ' | DIRECTOR: ' + row[2]
        lb.insert(END, s)
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)



def ventana_principal():
    def listar():
            conn = sqlite3.connect('peliculas.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT TITULO, PAIS, DIRECTOR FROM PELICULA")
            conn.close
            listar_peliculas(cursor)
    
    #Se crea ventana principal y barra de menú
    raiz = Tk()
    menu = Menu(raiz)

    #DATOS
    #Se crean las opciones del desplegable Datos, y se añaden todas
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Listar", command=listar)
    #.quit cierra la ventana más grande
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)

    #BUSCAR
    #Se crean las opciones del desplegable Buscar, y se añaden todas
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="TÃ­tulo", command=buscar_por_titulo)
    menubuscar.add_command(label="Fecha", command=buscar_por_fecha)
    menubuscar.add_command(label="GÃ©neros", command=buscar_por_genero)
    menu.add_cascade(label="Buscar", menu=menubuscar)

    #Añadir este config para que la barra de menú sea visible
    raiz.config(menu=menu)
    raiz.mainloop()



if __name__ == "__main__":
    ventana_principal()

