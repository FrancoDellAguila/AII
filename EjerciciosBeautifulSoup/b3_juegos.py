#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import re

PAGINAS = 2  #nÃºmero de pÃ¡ginas

# lineas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def extraer_juegos():
    lista=[]
    
    for p in range(1,PAGINAS+1):
        url="https://zacatrus.es/juegos-de-mesa.html?p="+str(p)
        f = urllib.request.urlopen(url)
        s = BeautifulSoup(f,"lxml")      
        
        l = s.ol.find_all("div", class_= "product-item-details")

        for i in l:
            titulo = i.a.string.strip()
            votos = i.find("div",class_="rating-result")
            if votos:
                votos = int(re.compile('\d+').search(votos['title']).group())
            else:
                votos = -1
            precio = re.compile('\d+,\d+').search(i.find("span", class_="price").string.strip()).group()
            precio = float(precio.replace(',','.'))
            
            f1 = urllib.request.urlopen(i.a['href'])
            j = BeautifulSoup(f1,"lxml")
          
            t = j.find("div", class_="data table additional-attributes")       
            if t :#tienen alguna/s de las caracterÃ­sticas adicionales
                tematica = t.find("div",attrs={"data-th":"Temática"})
                if tematica:
                    tematica = tematica.string.strip()
                else:
                    tematica = "Desconocida"
                complejidad = t.find("div",attrs={"data-th":"Complejidad"})
                if complejidad:
                    complejidad = complejidad.string.strip()
                else:
                    complejidad = "Desconocida"
            else: #no tienen caracterÃ­sticas adicionales
                tematica = "Desconocida"
                complejidad = "Desconocida"
                    
            lista.append((titulo,votos,precio,tematica,complejidad))
        
    return lista


def imprimir_lista(cursor):
    v = Toplevel()
    v.title("JUEGOS DE MESA DE ZACATRUS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row[0])
        lb.insert(END,"    Votos positivos: "+ str(row[1] if row[1]>=0 else "sin votos"))
        lb.insert(END,"    Precio: "+ str(row[2]) + " $")
        lb.insert(END,"    Temáticas: "+ row[3])
        lb.insert(END,"    Complejidad: "+ row[4])
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)

def imprimir_lista_1(cursor,tematicacomplejidad):
    v = Toplevel()
    v.title("JUEGOS DE " + tematicacomplejidad)
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row[0])
        lb.insert(END,"    Temáticas: "+ row[1])
        lb.insert(END,"    Complejidad: "+ row[2])
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)
 
def almacenar_bd():
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str  # para evitar problemas con el conjunto de caracteres que maneja la BD
    conn.execute("DROP TABLE IF EXISTS JUEGOS") 
    conn.execute('''CREATE TABLE JUEGOS
       (TITULO        TEXT    NOT NULL,
       VOTOS          INT    ,
       PRECIO         FLOAT    ,
       TEMATICAS        TEXT    ,
       COMPLEJIDAD      TEXT);''')

    for i in extraer_juegos():              
        conn.execute("""INSERT INTO JUEGOS VALUES (?,?,?,?,?)""",i)
    conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM JUEGOS")
    messagebox.showinfo( "Base Datos", "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()


def listar_juegos():
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str  
    cursor = conn.execute("SELECT * FROM JUEGOS")
    imprimir_lista(cursor)
    conn.close()
    
def listar_mejores_juegos():
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str  
    cursor = conn.execute("SELECT * FROM JUEGOS WHERE VOTOS > 90 ORDER BY VOTOS DESC")
    imprimir_lista(cursor)
    conn.close()
 
def buscar_por_tematicas():
    def listar(event):
            conn = sqlite3.connect('juegos.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT TITULO, TEMATICAS, COMPLEJIDAD FROM JUEGOS where TEMATICAS LIKE '%" + str(tematica.get()) + "%'")
            conn.close
            imprimir_lista_1(cursor,"TEMATICA "+ tematica.get().upper())
    
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT TEMATICAS FROM JUEGOS")
    
    tematicas=set()
    for i in cursor:
        varios = i[0].split(",")
        for t in varios:
            tematicas.add(t.strip())

    v = Toplevel()
    label = Label(v,text="Seleccione la temática: ")
    label.pack(side=LEFT)
    tematica = Spinbox(v, width= 30, values=list(tematicas))
    tematica.bind("<Return>", listar)
    tematica.pack(side=LEFT)
    
    conn.close()

def buscar_por_complejidad():
    def listar(event):
            conn = sqlite3.connect('juegos.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT TITULO, TEMATICAS, COMPLEJIDAD FROM JUEGOS where COMPLEJIDAD LIKE '%" + str(complejidad.get()) + "%'")
            conn.close
            imprimir_lista_1(cursor,"COMPLEJIDAD "+ complejidad.get().upper())
    
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT COMPLEJIDAD FROM JUEGOS")
    
    complejidades = [i[0] for i in cursor]

    v = Toplevel()
    label = Label(v,text="Seleccione la complejidad: ")
    label.pack(side=LEFT)
    complejidad = Spinbox(v, width= 30, values=complejidades)
    complejidad.bind("<Return>", listar)
    complejidad.pack(side=LEFT)
    
    conn.close()   
  
def ventana_principal():       
    root = Tk()
    root.geometry("150x100")

    menubar = Menu(root)
    
    datosmenu = Menu(menubar, tearoff=0)
    datosmenu.add_command(label="Cargar", command=almacenar_bd)
    datosmenu.add_separator()   
    datosmenu.add_command(label="Salir", command=root.quit)
    
    menubar.add_cascade(label="Datos", menu=datosmenu)
    
    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Juegos", command=listar_juegos)
    buscarmenu.add_command(label="Mejores juegos", command=listar_mejores_juegos)
    
    menubar.add_cascade(label="Listar", menu=buscarmenu)
    
    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Juegos por temática", command=buscar_por_tematicas)
    buscarmenu.add_command(label="Juegos por complejidad", command=buscar_por_complejidad)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()

    

if __name__ == "__main__":
    ventana_principal()
