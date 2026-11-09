#!/usr/bin/env python3
"""
Arma las hojas de fotos por talla de O'Neill Chiclayo.

Para que el bot, cuando un cliente pida "un polo en talla M", le mande UNA
foto con todo lo disponible en talla M, numerado y con precio. El dueño lo
dijo asi: "nadie entra a los links, el 99% no entran, necesitan fotos para
cerrar la venta".

Cada hoja es una imagen lista para WhatsApp: 12 productos, numerados, con
nombre y precio. Si una talla tiene mas de 12, se parte en varias hojas.

Entrada : datos.json y las fotos de innervision/fotos/
Salida  : innervision/tallas/<categoria>-<talla>-<n>.jpg
          innervision/tallas/indice.json  (lo que lee el bot)
"""

import json
import math
import os
import re
import unicodedata
from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.abspath(__file__))
FOTOS = os.path.join(RAIZ, 'innervision', 'fotos')
SALIDA = os.path.join(RAIZ, 'innervision', 'tallas')
WHATSAPP = '996 113 704'

POR_HOJA = 12
COLS = 3
ANCHO = 840
MARGEN = 18
HUECO = 10
ALTO_CABECERA = 96
ALTO_PIE = 52
ALTO_TEXTO = 62          # para el nombre y el precio debajo de cada foto

NEGRO = (11, 11, 11)
GRIS = (107, 107, 107)
LINEA = (230, 230, 228)
HUMO = (245, 245, 243)
BLANCO = (255, 255, 255)
ROJO = (200, 30, 30)

F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
def fuente(px, negrita=False):
    return ImageFont.truetype(F % ('-Bold' if negrita else ''), px)

TITULO = fuente(30, True)
SUB = fuente(14)
NUM = fuente(17, True)
NOMBRE = fuente(13)
PRECIO = fuente(16, True)
ANTES = fuente(12)
PIE = fuente(13)

NOMBRES = {
    'lentes': 'Lentes', 'polos': 'Polos', 'manga-larga': 'Polos manga larga',
    'camisas': 'Camisas', 'bividis': 'Bividis', 'poleras': 'Poleras',
    'casacas': 'Casacas', 'joggers': 'Joggers', 'shorts': 'Shorts',
    'bano': 'Ropa de bano', 'bikinis': 'Bikinis', 'polos-mujer': 'Polos de mujer',
    'polos-nino': 'Polos de nino', 'sandalias': 'Sandalias',
    'sandalias-mujer': 'Sandalias de mujer', 'sandalias-nino': 'Sandalias de nino',
    'zapatillas': 'Zapatillas', 'aquashoes': 'Aquashoes', 'gorras': 'Gorras',
    'mochilas': 'Mochilas', 'canguros': 'Canguros', 'billeteras': 'Billeteras',
    'acc-otros': 'Accesorios', 'licras': 'Licras', 'bodyboards': 'Bodyboards',
    'wetsuits': 'Wetsuits',
}


# Como estan escritas las marcas en los titulos del catalogo, y como se
# llaman de verdad. Se busca la primera que aparezca en el titulo.
MARCAS = [('OAKLEY', 'Oakley'), ("O'NEILL", "O'Neill"), ('O.NEILL', "O'Neill"),
          ('ONEILL', "O'Neill"), ('DRAGON', 'Dragon'), ('VEECE', 'VEECE'),
          ('REEF', 'Reef'), ('VOLCOM', 'Volcom'), ('RIP CURL', 'Rip Curl'),
          ('BILLABONG', 'Billabong'), ('QUIKSILVER', 'Quiksilver'),
          ('HURLEY', 'Hurley'), ('ARNETTE', 'Arnette'), ('BOLLE', 'Bolle')]


def marca_de(titulo):
    t = titulo.upper()
    for clave, nombre in MARCAS:
        if clave in t:
            return nombre
    return ''


def slug(t):
    t = unicodedata.normalize('NFKD', str(t)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-zA-Z0-9]+', '-', t).strip('-').lower() or 'x'


def recortar(dib, texto, fnt, ancho):
    """Corta el texto con puntos suspensivos para que entre en el ancho."""
    if dib.textlength(texto, font=fnt) <= ancho:
        return texto
    while texto and dib.textlength(texto + '...', font=fnt) > ancho:
        texto = texto[:-1]
    return texto + '...'


def miniatura(ruta, lado):
    """Abre la foto y la deja cuadrada y centrada. El fondo va BLANCO: casi
    todas las fotos del catalogo vienen con fondo blanco y cualquier otro
    color deja una franja visible a los costados."""
    lienzo = Image.new('RGB', (lado, lado), BLANCO)
    try:
        im = Image.open(os.path.join(FOTOS, ruta))
    except Exception:
        return lienzo
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        fondo = Image.new('RGB', im.size, BLANCO)
        fondo.paste(im, mask=im.split()[-1])
        im = fondo
    im = im.convert('RGB')
    im.thumbnail((lado, lado), Image.LANCZOS)
    lienzo.paste(im, ((lado - im.width) // 2, (lado - im.height) // 2))
    return lienzo


def armar(productos, categoria, talla, hoja, de_hojas, marca=''):
    cel = (ANCHO - 2 * MARGEN - (COLS - 1) * HUECO) // COLS
    filas = math.ceil(len(productos) / COLS)
    alto = (ALTO_CABECERA + MARGEN + filas * (cel + ALTO_TEXTO)
            + (filas - 1) * HUECO + MARGEN + ALTO_PIE)

    im = Image.new('RGB', (ANCHO, alto), BLANCO)
    d = ImageDraw.Draw(im)

    # Cabecera negra
    d.rectangle([0, 0, ANCHO, ALTO_CABECERA], fill=NEGRO)
    d.text((MARGEN, 20), "O'NEILL CHICLAYO", font=TITULO, fill=BLANCO)
    titulo = NOMBRES.get(categoria, categoria)
    linea2 = f'{titulo} · Talla {talla}' if talla else titulo
    if marca:
        linea2 += f' · {marca}'
    if de_hojas > 1:
        linea2 += f'  ({hoja} de {de_hojas})'
    d.text((MARGEN, 60), linea2.upper(), font=SUB, fill=(163, 163, 163))

    y = ALTO_CABECERA + MARGEN
    for i, p in enumerate(productos):
        titulo_p, precio, antes, foto = p[0], p[1], p[2], p[3]
        cx = MARGEN + (i % COLS) * (cel + HUECO)
        cy = y + (i // COLS) * (cel + ALTO_TEXTO + HUECO)

        im.paste(miniatura(foto, cel), (cx, cy))
        d.rectangle([cx, cy, cx + cel - 1, cy + cel - 1], outline=LINEA)

        # Numero en una esquina negra, para que el cliente diga "quiero el 4"
        d.rectangle([cx, cy, cx + 30, cy + 28], fill=NEGRO)
        n = str((hoja - 1) * POR_HOJA + i + 1)
        d.text((cx + 15 - d.textlength(n, font=NUM) / 2, cy + 5),
               n, font=NUM, fill=BLANCO)

        ty = cy + cel + 6
        d.text((cx, ty), recortar(d, titulo_p, NOMBRE, cel), font=NOMBRE, fill=NEGRO)
        pr = f'S/ {precio:.2f}'.replace('.00', '')
        d.text((cx, ty + 20), pr, font=PRECIO, fill=NEGRO)
        if antes and antes > precio:
            x2 = cx + d.textlength(pr, font=PRECIO) + 8
            an = f'S/ {antes:.2f}'.replace('.00', '')
            d.text((x2, ty + 24), an, font=ANTES, fill=GRIS)
            d.line([x2, ty + 31, x2 + d.textlength(an, font=ANTES), ty + 31], fill=ROJO)

    py = alto - ALTO_PIE
    d.line([0, py, ANCHO, py], fill=LINEA)
    d.text((MARGEN, py + 18), f'Pidelo por WhatsApp {WHATSAPP}  ·  '
           'Av. Santa Victoria 452, Chiclayo', font=PIE, fill=GRIS)
    return im


def main():
    datos = json.load(open(os.path.join(RAIZ, 'datos.json'), encoding='utf-8'))
    os.makedirs(SALIDA, exist_ok=True)
    for f in os.listdir(SALIDA):
        os.remove(os.path.join(SALIDA, f))

    # Agrupar: (categoria, talla) -> productos. Las tallas vienen pegadas
    # con barras, "S/M/L", asi que hay que separarlas.
    grupos = {}
    for cat, prods in datos.items():
        for p in prods:
            tallas = [t.strip() for t in str(p[4]).split('/') if t.strip()]
            for t in (tallas or ['']):
                grupos.setdefault((cat, t), []).append(p)

    indice = {}
    pesos = []

    def hojas_de(prods, cat, talla, marca=''):
        """Guarda las hojas de un grupo y devuelve sus rutas."""
        prods.sort(key=lambda p: -(p[2] or 0) + p[1])   # primero las ofertas
        total = math.ceil(len(prods) / POR_HOJA)
        urls = []
        for h in range(total):
            trozo = prods[h * POR_HOJA:(h + 1) * POR_HOJA]
            partes = [cat, slug(talla) if talla else 'todo']
            if marca:
                partes.append(slug(marca))
            nombre = '-'.join(partes) + f'-{h + 1}.jpg'
            ruta = os.path.join(SALIDA, nombre)
            armar(trozo, cat, talla, h + 1, total, marca).save(
                ruta, 'JPEG', quality=66, optimize=True, progressive=True)
            pesos.append(os.path.getsize(ruta))
            urls.append('tallas/' + nombre)
        return urls

    for (cat, talla), prods in sorted(grupos.items()):
        entrada = {'productos': len(prods), 'hojas': hojas_de(list(prods), cat, talla)}

        # Cuando una talla tiene tantos productos que saldrian 3 hojas o mas,
        # mandarselas todas al cliente no sirve. Ahi el bot pregunta la marca,
        # asi que dejamos tambien las hojas cortadas por marca.
        if len(prods) > 2 * POR_HOJA:
            por_marca = {}
            for p in prods:
                m = marca_de(p[0])
                if m:
                    por_marca.setdefault(m, []).append(p)
            marcas = {}
            for m, lista in sorted(por_marca.items()):
                marcas[m] = {'productos': len(lista),
                             'hojas': hojas_de(list(lista), cat, talla, m)}
            if len(marcas) > 1:
                entrada['marcas'] = marcas

        indice.setdefault(cat, {})[talla or 'todo'] = entrada

    with open(os.path.join(SALIDA, 'indice.json'), 'w', encoding='utf-8') as f:
        json.dump(indice, f, ensure_ascii=False, indent=1)

    print(f'{len(pesos)} hojas · {sum(pesos)/1048576:.1f} MB · '
          f'promedio {sum(pesos)/len(pesos)/1024:.0f} KB · '
          f'la mas pesada {max(pesos)/1024:.0f} KB')


if __name__ == '__main__':
    main()
