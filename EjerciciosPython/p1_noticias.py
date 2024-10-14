#encoding:utf-8

import re
import urllib.request
import os.path

def extraer_lista(file):
    f = open (file, "r",encoding='utf-8')
    s = f.read()
    l1 = re.findall(r'<title>(.*)</title>\s*<link>(.*)</link>', s)
    l2 = re.findall(r'<pubDate>(.*)</pubDate>', s)
    l = [list(e1) for e1 in l1[1:]]
    for e1,e2 in zip(l,l2):
        e1.append(e2)
    f.close()
    return l

def imprimir_lista(l):
    for t in l:
        print ("Título:", t[0])
        print ("Link:", t[1])
        f=formatear_fecha(t[2])
        print ("Fecha: {0:2s}/{1:2s}/{2:4s}\n".format(f[0],f[1],f[2]))
 

def abrir_url(url,file):
    try:
        if os.path.exists(file):
            recarga = input("La página ya ha sido cargada. Desea recargarla (s/n)?")
            if recarga == "s":
                urllib.request.urlretrieve(url,file)
        else:
            urllib.request.urlretrieve(url,file)
        return file
    except:
        print  ("Error al conectarse a la página")
        return None

def buscar_fecha(l):
    mes = input("Introduzca el mes (mm):")
    dia = input("Introduzca el dia (dd):")
    enc=False
    for t in l:
        f =formatear_fecha(t[2])
        if mes == f[1] and dia == f[0]:
            print ("Título:", t[0])
            print ("Link:", t[1])
            print ("Fecha: %2s/%2s/%4s\n"%(f[0],f[1],f[2]))
            enc = True
    if not enc:
        print ("No hay noticias para ese mes")
        
def formatear_fecha(s):
    meses={'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
    fecha = re.match(r'.*(\b2_cine\b2_cine)\s*(.{3})\s*(\b2_cine{4}).*', s)
    l = list(fecha.groups())
    l[1] = meses[l[1]]
    return tuple(l)

if __name__ == "__main__":
    fichero="noticias"
    if abrir_url("https://www.abc.es/rss/2.0/espana/andalucia/",fichero):
        l=extraer_lista(fichero)
    if l:
        imprimir_lista(l)
        buscar_fecha(l)
