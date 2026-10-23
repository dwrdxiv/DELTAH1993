from fpdf import FPDF

def fmt_monto(valor):
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"

pdf = FPDF(orientation='P', unit='mm', format=(216, 279))
pdf.set_margins(0, 0, 0)
pdf.set_auto_page_break(False)
pdf.add_page()

# =========================================================
# DIBUJO DE ESTRUCTURA Y ENCABEZADOS (Hoja en Blanco)
# =========================================================

# --- Encabezado Principal ---
pdf.set_font("Helvetica", "B", 14)

# --- Cuadro de Datos de Factura / Fecha ---
#pdf.rect(140, 15, 60, 25)
pdf.set_font("Helvetica", "B", 10)
pdf.set_xy(140, 19)
pdf.cell(60, 5, text="FECHA DE EMISIÓN", border=0, align="C")

# Sub-tabla para Día / Mes / Año
pdf.set_font("Helvetica", "B", 8)
pdf.set_xy(145, 23)
pdf.cell(15, 5, text="DÍA", border=1, align="C")
pdf.cell(18, 5, text="MES", border=1, align="C")
pdf.cell(17, 5, text="AÑO", border=1, align="C")

pdf.set_font("Helvetica", "", 10)
pdf.set_xy(145, 28)
pdf.cell(15, 5, text="21", border=1, align="C")
pdf.cell(18, 5, text="10", border=1, align="C")
pdf.cell(17, 5, text="2026", border=1, align="C")

# --- Cuadro de Datos del Cliente ---
pdf.rect(14, 35, 186, 23)

pdf.set_font("Helvetica", "B", 9)
pdf.set_xy(16, 36)
pdf.cell(32, 6, text="Nombre / Razón:", border=0)
pdf.set_font("Helvetica", "", 9)
pdf.cell(150, 6, text="DISTRIBUIDORA EJEMPLO C.A.", border="B")

pdf.set_font("Helvetica", "B", 9)
pdf.set_xy(16, 43)
pdf.cell(32, 6, text="Domicilio Fiscal:", border=0)
pdf.set_font("Helvetica", "", 9)
pdf.cell(150, 6, text="AV. PRINCIPAL, EDIF. CENTRO, PISO 2, OFICINA 4", border="B")

pdf.set_font("Helvetica", "B", 9)
pdf.set_xy(16, 50)
pdf.cell(20, 6, text="C.I / RIF:", border=0)
pdf.set_font("Helvetica", "", 9)
pdf.cell(30, 6, text="J-12345678-9", border="B", align="C")

pdf.set_font("Helvetica", "B", 9)
pdf.set_xy(72, 50)
pdf.cell(28, 6, text="N° Orden / Guía:", border=0)
pdf.set_font("Helvetica", "", 9)
pdf.cell(30, 6, text="ORD-2026-0089", border="B", align="C")

pdf.set_font("Helvetica", "B", 9)
pdf.set_xy(137, 50)
pdf.cell(28, 6, text="Metodo de Pago:", border=0)
pdf.set_font("Helvetica", "", 9)
pdf.cell(30, 6, text="Contado", border="B", align="C")

# --- ENCABEZADOS DE LA TABLA DE PRODUCTOS ---
y_tabla_inicio = 60
pdf.set_font("Helvetica", "B", 8)
pdf.set_xy(14, y_tabla_inicio)
pdf.cell(13, 6, text="CANT.", border=1, align="C")
pdf.cell(107, 6, text="DESCRIPCIÓN / CONCEPTO", border=1, align="C")
pdf.cell(24, 6, text="P. UNITARIO", border=1, align="C")
pdf.cell(11, 6, text="ALÍC.", border=1, align="C")
pdf.cell(31, 6, text="SUBTOTAL", border=1, align="C")

alto_cuerpo_tabla = 165 
pdf.rect(14, y_tabla_inicio + 6, 186, alto_cuerpo_tabla) 

# --- ITEMS DE EJEMPLO ---
items = [
    {"cant": 2, "descripcion": "PRODUCTO DE PRUEBA A", "precioBase": 150.00, "tieneIVA": True, "subtotal": 300.00},
    {"cant": 0, "descripcion": "LINEA ADICIONAL DE DESCRIPCION EXTENDIDA PARA DEMOSTRAR EL FORMATO", "precioBase": 0, "tieneIVA": False, "subtotal": 0},
    {"cant": 5, "descripcion": "PRODUCTO EXENTO B", "precioBase": 40.00, "tieneIVA": False, "subtotal": 200.00}
]

pdf.set_font("Helvetica", "", 9)
y_inicial = y_tabla_inicio + 7
alto_fila = 6

for i, item in enumerate(items):
    y = y_inicial + (i * alto_fila)
    cant = float(item.get("cant", 0) or 0)
    descripcion = str(item.get("descripcion", ""))
    precio_base = float(item.get("precioBase", 0) or 0)
    tiene_iva = item.get("tieneIVA", False)
    total_renglon = float(item.get("subtotal", 0) or 0)

    if cant > 0:
        pdf.set_xy(14, y)
        txt_cant = str(int(cant)) if cant.is_integer() else f"{cant:.2f}"
        pdf.cell(13, 5, text=txt_cant, align="C")

    pdf.set_xy(28, y)
    pdf.cell(105, 5, text=descripcion, align="L")

    if precio_base > 0:
        pdf.set_xy(134, y)
        pdf.cell(24, 5, text=fmt_monto(precio_base), align="R")

    if cant > 0 and precio_base > 0:
        pdf.set_xy(158, y)
        alicuota = "16%" if tiene_iva else "E"
        pdf.cell(11, 5, text=alicuota, align="C")

    if total_renglon > 0:
        pdf.set_xy(169, y)
        pdf.cell(31, 5, text=fmt_monto(total_renglon), align="R")

# --- RESUMEN DE TOTALES ---
pdf.set_font("Helvetica", "B", 8)
pdf.set_xy(135, 233)
pdf.cell(32, 5, text="Base Imponible Bs.", border=1, align="L")
pdf.set_font("Helvetica", "", 9)
pdf.cell(33, 5, text=fmt_monto(300.00), border=1, align="R")

pdf.set_font("Helvetica", "B", 8)
pdf.set_xy(135, 238)
pdf.cell(32, 5, text="Exento Bs.", border=1, align="L")
pdf.set_font("Helvetica", "", 9)
pdf.cell(33, 5, text=fmt_monto(200.00), border=1, align="R")

pdf.set_font("Helvetica", "B", 8)
pdf.set_xy(135, 243)
pdf.cell(32, 5, text="I.V.A. (16%)", border=1, align="L")
pdf.set_font("Helvetica", "", 9)
pdf.cell(33, 5, text=fmt_monto(48.00), border=1, align="R")

pdf.set_font("Helvetica", "B", 9)
pdf.set_xy(135, 248)
pdf.cell(32, 7, text="Total Bs.", border=1, align="L")
pdf.cell(33, 7, text=fmt_monto(548.00), border=1, align="R")

pdf.output("vista_previa_factura.pdf")
print("PDF 'vista_previa_factura.pdf' generado con éxito.")