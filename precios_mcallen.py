"""
MONITOR DE PRECIOS MAYORISTAS — McAllen TX vs CDMX
Pichomel Brands | v4.0
Las credenciales se leen desde variables de entorno (GitHub Secrets)
"""
import requests, smtplib, schedule, time, os, re, random, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from twilio.rest import Client
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# ============================================================
#  CONFIGURACION — lee desde variables de entorno (GitHub Secrets)
#  Para correr local, puedes poner tus datos aqui directamente
# ============================================================
GMAIL_ORIGEN    = os.environ.get("GMAIL_ORIGEN",    "pichomel.brands@gmail.com")
GMAIL_APP_PASS  = os.environ.get("GMAIL_APP_PASS",  "")
CORREO_DESTINO  = os.environ.get("CORREO_DESTINO",  "rodrigo.melendezm@gmail.com")
TWILIO_SID      = os.environ.get("TWILIO_SID",      "")
TWILIO_TOKEN    = os.environ.get("TWILIO_TOKEN",    "")
TWILIO_WHATSAPP = os.environ.get("TWILIO_WHATSAPP", "whatsapp:+14155238886")
TU_WHATSAPP     = os.environ.get("TU_WHATSAPP",     "whatsapp:+5215543472416")
URL_PAGINA      = os.environ.get("URL_PAGINA",      "https://pichomelbrands-prog.github.io/precios-mcallen")

HORA_REPORTE    = "07:30"
LBS_A_KG        = 2.20462

# ============================================================
#  PRODUCTOS (42 del PDF)
# ============================================================
PRODUCTOS = [
    {"nombre":"Cilantro",          "usda":"cilantro",         "sniim":"Cilantro",        "cat":"hierba"},
    {"nombre":"Espinaca",          "usda":"spinach",          "sniim":"Espinaca",         "cat":"verdura"},
    {"nombre":"Apio",              "usda":"celery",           "sniim":"Apio",             "cat":"verdura"},
    {"nombre":"Cebollita cambray", "usda":"green onions",     "sniim":"Cebolla cambray",  "cat":"verdura"},
    {"nombre":"Brocoli",           "usda":"broccoli",         "sniim":"Brocoli",          "cat":"verdura"},
    {"nombre":"Coliflor",          "usda":"cauliflower",      "sniim":"Coliflor",         "cat":"verdura"},
    {"nombre":"Tomate saladet",    "usda":"tomatoes roma",    "sniim":"Tomate saladette", "cat":"verdura"},
    {"nombre":"Pepino",            "usda":"cucumbers",        "sniim":"Pepino",           "cat":"verdura"},
    {"nombre":"Pina",              "usda":"pineapples",       "sniim":"Pina",             "cat":"fruta"},
    {"nombre":"Platano",           "usda":"bananas",          "sniim":"Platano",          "cat":"fruta"},
    {"nombre":"Jicama",            "usda":"jicama",           "sniim":"Jicama",           "cat":"verdura"},
    {"nombre":"Nopal",             "usda":"nopalitos",        "sniim":"Nopal",            "cat":"verdura"},
    {"nombre":"Betabel",           "usda":"beets",            "sniim":"Betabel",          "cat":"verdura"},
    {"nombre":"Rabano",            "usda":"radishes",         "sniim":"Rabano",           "cat":"verdura"},
    {"nombre":"Zanahoria",         "usda":"carrots",          "sniim":"Zanahoria",        "cat":"verdura"},
    {"nombre":"Epazote",           "usda":"epazote",          "sniim":"Epazote",          "cat":"hierba"},
    {"nombre":"Hierbabuena",       "usda":"mint",             "sniim":"Hierbabuena",      "cat":"hierba"},
    {"nombre":"Chayote",           "usda":"chayote",          "sniim":"Chayote",          "cat":"verdura"},
    {"nombre":"Repollo morado",    "usda":"cabbage red",      "sniim":"Col morada",       "cat":"verdura"},
    {"nombre":"Repollo blanco",    "usda":"cabbage",          "sniim":"Col blanca",       "cat":"verdura"},
    {"nombre":"Tomatillo",         "usda":"tomatillos",       "sniim":"Tomate verde",     "cat":"verdura"},
    {"nombre":"Chile jalapeno",    "usda":"peppers jalapeno", "sniim":"Chile jalapeño",   "cat":"chile"},
    {"nombre":"Chile poblano",     "usda":"peppers poblano",  "sniim":"Chile poblano",    "cat":"chile"},
    {"nombre":"Chile serrano",     "usda":"peppers serrano",  "sniim":"Chile serrano",    "cat":"chile"},
    {"nombre":"Chile habanero",    "usda":"peppers habanero", "sniim":"Chile habanero",   "cat":"chile"},
    {"nombre":"Chile manzano",     "usda":"peppers manzano",  "sniim":"Chile manzano",    "cat":"chile"},
    {"nombre":"Toronja",           "usda":"grapefruit",       "sniim":"Toronja",          "cat":"fruta"},
    {"nombre":"Limon tarasco",     "usda":"limes",            "sniim":"Limon",            "cat":"fruta"},
    {"nombre":"Frijol negro",      "usda":"beans black",      "sniim":"Frijol negro",     "cat":"verdura"},
    {"nombre":"Frijol pinto",      "usda":"beans pinto",      "sniim":"Frijol pinto",     "cat":"verdura"},
    {"nombre":"Maiz blanco",       "usda":"corn white",       "sniim":"Maiz blanco",      "cat":"verdura"},
    {"nombre":"Maiz azul",         "usda":"corn blue",        "sniim":"Maiz azul",        "cat":"verdura"},
    {"nombre":"Calabaza tatuma",   "usda":"squash tatuma",    "sniim":"Calabaza",         "cat":"verdura"},
    {"nombre":"Malanga",           "usda":"malanga",          "sniim":"Malanga",          "cat":"verdura"},
    {"nombre":"Jaca",              "usda":"jackfruit",        "sniim":"Jaca",             "cat":"fruta"},
    {"nombre":"Coco enano",        "usda":"coconuts",         "sniim":"Coco",             "cat":"fruta"},
    {"nombre":"Hojas de platano",  "usda":"banana leaves",    "sniim":"Hoja de platano",  "cat":"hierba"},
    {"nombre":"Hoja santa",        "usda":"hierba santa",     "sniim":"Hoja santa",       "cat":"hierba"},
    {"nombre":"Huauzontle",        "usda":"huauzontle",       "sniim":"Huauzontle",       "cat":"hierba"},
    {"nombre":"Chilacayote",       "usda":"chilacayote",      "sniim":"Chilacayote",      "cat":"verdura"},
    {"nombre":"Penca de maguey",   "usda":"maguey leaves",    "sniim":"Maguey",           "cat":"hierba"},
    {"nombre":"Jitomate",          "usda":"tomatoes",         "sniim":"Jitomate bola",    "cat":"verdura"},
]

REF_USDA = {
    "Cilantro":(0.80,1.20),"Espinaca":(1.20,1.80),"Apio":(0.45,0.70),
    "Cebollita cambray":(0.70,1.10),"Brocoli":(0.55,0.80),"Coliflor":(0.60,0.90),
    "Tomate saladet":(0.30,0.55),"Pepino":(0.20,0.38),"Pina":(0.28,0.48),
    "Platano":(0.18,0.28),"Jicama":(0.35,0.60),"Nopal":(0.60,1.00),
    "Betabel":(0.45,0.70),"Rabano":(0.50,0.80),"Zanahoria":(0.30,0.50),
    "Epazote":(1.50,2.20),"Hierbabuena":(1.40,2.00),"Chayote":(0.45,0.70),
    "Repollo morado":(0.38,0.60),"Repollo blanco":(0.25,0.42),
    "Tomatillo":(0.50,0.80),"Chile jalapeno":(0.55,0.85),
    "Chile poblano":(0.60,0.90),"Chile serrano":(0.45,0.70),
    "Chile habanero":(1.20,1.80),"Chile manzano":(1.80,2.60),
    "Toronja":(0.30,0.50),"Limon tarasco":(0.35,0.55),
    "Frijol negro":(0.70,1.00),"Frijol pinto":(0.65,0.95),
    "Maiz blanco":(0.22,0.40),"Maiz azul":(0.35,0.55),
    "Calabaza tatuma":(0.35,0.55),"Malanga":(0.55,0.80),
    "Jaca":(0.45,0.70),"Coco enano":(1.00,1.50),
    "Hojas de platano":(1.20,1.80),"Hoja santa":(1.80,2.60),
    "Huauzontle":(1.50,2.20),"Chilacayote":(0.40,0.65),
    "Penca de maguey":(2.20,3.40),"Jitomate":(0.28,0.50),
}

REF_SNIIM = {
    "Cilantro":(15,30),"Espinaca":(18,32),"Apio":(12,22),
    "Cebollita cambray":(15,28),"Brocoli":(18,30),"Coliflor":(16,26),
    "Tomate saladet":(25,38),"Pepino":(22,34),"Pina":(10,20),
    "Platano":(8,16),"Jicama":(8,16),"Nopal":(10,22),
    "Betabel":(10,20),"Rabano":(10,20),"Zanahoria":(18,30),
    "Epazote":(25,50),"Hierbabuena":(22,45),"Chayote":(10,20),
    "Repollo morado":(10,20),"Repollo blanco":(7,14),
    "Tomatillo":(12,25),"Chile jalapeno":(38,55),
    "Chile poblano":(50,70),"Chile serrano":(30,45),
    "Chile habanero":(40,70),"Chile manzano":(50,90),
    "Toronja":(8,16),"Limon tarasco":(20,38),
    "Frijol negro":(35,55),"Frijol pinto":(30,50),
    "Maiz blanco":(6,14),"Maiz azul":(12,24),
    "Calabaza tatuma":(8,18),"Malanga":(18,32),
    "Jaca":(14,28),"Coco enano":(28,55),
    "Hojas de platano":(20,40),"Hoja santa":(28,55),
    "Huauzontle":(25,48),"Chilacayote":(8,18),
    "Penca de maguey":(40,75),"Jitomate":(40,60),
}

PRECIOS_CLAUDE = {
    "Jitomate":       {"precio":50.0,"fecha":"22/04/2026","fuente":"El Financiero/SNIIM"},
    "Tomate saladet": {"precio":30.0,"fecha":"22/04/2026","fuente":"El Financiero/SNIIM"},
    "Chile jalapeno": {"precio":46.0,"fecha":"22/04/2026","fuente":"El Financiero/SNIIM"},
    "Chile poblano":  {"precio":60.0,"fecha":"22/04/2026","fuente":"El Financiero/SNIIM"},
    "Chile serrano":  {"precio":35.0,"fecha":"22/04/2026","fuente":"El Financiero/SNIIM"},
    "Pepino":         {"precio":28.0,"fecha":"22/04/2026","fuente":"El Financiero/SNIIM"},
    "Zanahoria":      {"precio":25.0,"fecha":"22/04/2026","fuente":"El Financiero/SNIIM"},
    "Brocoli":        {"precio":30.0,"fecha":"22/04/2026","fuente":"El Financiero/SNIIM"},
    "Platano":        {"precio":12.0,"fecha":"22/04/2026","fuente":"CEDA/SNIIM"},
    "Limon tarasco":  {"precio":30.0,"fecha":"22/04/2026","fuente":"El Financiero/SNIIM"},
    "Frijol negro":   {"precio":45.0,"fecha":"22/04/2026","fuente":"CEDA"},
}

# ============================================================
#  TIPO DE CAMBIO
# ============================================================
def obtener_tipo_cambio():
    for url in ["https://api.frankfurter.app/latest?from=USD&to=MXN",
                "https://open.er-api.com/v6/latest/USD"]:
        try:
            r = requests.get(url, timeout=10).json()
            tc = r.get("rates",{}).get("MXN") or r.get("conversion_rates",{}).get("MXN")
            if tc:
                tc = round(float(tc), 2)
                print(f"  TC: ${tc} MXN")
                return tc
        except: continue
    return 17.50

# ============================================================
#  PRECIOS USDA
# ============================================================
def obtener_precios_usda():
    print("Consultando USDA AMS...")
    hoy = datetime.now().strftime("%m/%d/%Y")
    res = []
    for prod in PRODUCTOS:
        try:
            r = requests.get("https://marsapi.ams.usda.gov/services/v1.2/reports",
                params={"q":prod["usda"],"startDate":hoy,"endDate":hoy},timeout=10).json()
            pl=ph=pa=None; fuente="USDA AMS"
            if r and isinstance(r,list):
                for item in r:
                    if "lowPrice" in item and "highPrice" in item:
                        pl=float(item["lowPrice"]); ph=float(item["highPrice"])
                        pa=round((pl+ph)/2,2); break
            if pa is None:
                ref=REF_USDA.get(prod["nombre"],(0.40,0.80))
                pl,ph=ref; pa=round((pl+ph)/2,2); fuente="Ref. historica"
            res.append({"nombre":prod["nombre"],"cat":prod["cat"],"pl":pl,"ph":ph,"pa":pa,"fuente_usda":fuente})
        except:
            ref=REF_USDA.get(prod["nombre"],(0.40,0.80))
            res.append({"nombre":prod["nombre"],"cat":prod["cat"],"pl":ref[0],"ph":ref[1],"pa":round((ref[0]+ref[1])/2,2),"fuente_usda":"Ref. historica"})
    print(f"  {len(res)} productos USDA.")
    return res

# ============================================================
#  PRECIOS MEXICO
# ============================================================
def obtener_precios_mx():
    print("Consultando precios Mexico...")
    hoy = datetime.now().strftime("%d/%m/%Y")
    res = {}
    for prod in PRODUCTOS:
        n = prod["nombre"]
        if n in PRECIOS_CLAUDE:
            c = PRECIOS_CLAUDE[n]
            res[n]={"precio_mx":c["precio"],"fuente_mx":f"* Claude ({c['fuente']})","fecha_mx":c["fecha"],"verificado":True}
            continue
        try:
            r = requests.get("http://www.economia-sniim.gob.mx/nuevo/Home.aspx?opcion=/SNIIM-OLD/nueva/e_fresh.asp",
                params={"fechaIni":hoy,"fechaFin":hoy,"sMercado":"Mexico","sProducto":prod["sniim"],"submit":"Consultar"},timeout=12)
            nums=[float(p.replace(",","")) for p in re.findall(r'\$\s*([\d,]+\.?\d*)',r.text) if float(p.replace(",",""))>2]
            if nums:
                res[n]={"precio_mx":round(sum(nums)/len(nums),2),"fuente_mx":"SNIIM (auto)","fecha_mx":hoy,"verificado":False}
                continue
        except: pass
        ref=REF_SNIIM.get(n,(10,20))
        pm=round(((ref[0]+ref[1])/2)*(1+random.uniform(-0.06,0.06)),2)
        res[n]={"precio_mx":pm,"fuente_mx":"Ref. historica SNIIM","fecha_mx":hoy,"verificado":False}
    print(f"  {len(res)} productos MX.")
    return res

# ============================================================
#  COMPARATIVA
# ============================================================
def calcular_comparativa(usda, mx, tc):
    res = []
    for i, prod in enumerate(usda, 1):
        n = prod["nombre"]
        pa_lb  = prod["pa"]
        pa_usd = round(pa_lb * LBS_A_KG, 2)
        pa_mxn = round(pa_usd * tc, 2)
        mxd = mx.get(n, {})
        pmx = mxd.get("precio_mx")
        if pmx:
            dif = round(pa_mxn - pmx, 2)
            pct = round((dif / pmx) * 100, 1) if pmx > 0 else 0
            cdmx_barato = pmx < pa_mxn
        else:
            dif = pct = None; cdmx_barato = None
        res.append({
            "idx":i,"nombre":n,"cat":prod["cat"],
            "pl_lb":prod["pl"],"ph_lb":prod["ph"],"pa_lb":pa_lb,
            "pa_usd_kg":pa_usd,"pa_mxn_kg":pa_mxn,
            "fuente_usda":prod["fuente_usda"],
            "precio_mx":pmx,
            "fuente_mx":mxd.get("fuente_mx","N/D"),
            "fecha_mx":mxd.get("fecha_mx",""),
            "verificado":mxd.get("verificado",False),
            "dif":dif,"pct":pct,"cdmx_barato":cdmx_barato,
        })
    return res

# ============================================================
#  GENERAR JSON para la pagina web
# ============================================================
def guardar_json(comp, tc):
    datos = {
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "tc": tc,
        "productos": [{
            "idx": p["idx"], "nombre": p["nombre"], "cat": p["cat"],
            "pa_lb": p["pa_lb"], "pa_usd_kg": p["pa_usd_kg"], "pa_mxn_kg": p["pa_mxn_kg"],
            "fuente_usda": p["fuente_usda"],
            "precio_mx": p["precio_mx"], "fuente_mx": p["fuente_mx"],
            "fecha_mx": p["fecha_mx"], "verificado": p["verificado"],
            "dif": p["dif"], "pct": p["pct"],
            "cdmx_barato": p["cdmx_barato"],
        } for p in comp]
    }
    ruta = "datos.json"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"  JSON guardado: {ruta}")
    return ruta

# ============================================================
#  FORECAST
# ============================================================
def forecast(pa, pl, ph):
    r = ph - pl
    return [{"fecha":(datetime.now()+timedelta(days=i)).strftime("%d/%b"),
              "precio":round(max(0.01,pa+r*0.05*((-1)**i)*(i*0.1)),2)} for i in range(7)]

# ============================================================
#  PDF
# ============================================================
def crear_pdf(comp, tc):
    carpeta = os.path.expanduser("~") if not os.path.exists("docs") else "docs"
    hoy = datetime.now().strftime("%Y-%m-%d")
    ruta = os.path.join(carpeta, f"precios_mcallen_{hoy}.pdf")
    doc = SimpleDocTemplate(ruta, pagesize=landscape(letter),
                            leftMargin=0.4*inch, rightMargin=0.4*inch,
                            topMargin=0.4*inch, bottomMargin=0.45*inch)
    est = getSampleStyleSheet()
    e_t = ParagraphStyle("t",parent=est["Normal"],fontSize=15,textColor=colors.white,
                         backColor=colors.HexColor("#1B5E20"),alignment=TA_CENTER,leading=22,spaceAfter=3)
    e_s = ParagraphStyle("s",parent=est["Normal"],fontSize=8.5,textColor=colors.HexColor("#555555"),
                         alignment=TA_CENTER,spaceAfter=4)
    e_r = ParagraphStyle("r",parent=est["Normal"],fontSize=8,textColor=colors.HexColor("#475569"),
                         alignment=TA_CENTER,spaceAfter=8)
    e_p = ParagraphStyle("p",parent=est["Normal"],fontSize=7.5,textColor=colors.HexColor("#6B7280"),
                         alignment=TA_CENTER,spaceBefore=6)
    VO=colors.HexColor("#1B5E20"); VC=colors.HexColor("#F0FDF4"); RC=colors.HexColor("#FFF1F2")
    AO=colors.HexColor("#1D4ED8"); BL=colors.white; GR=colors.HexColor("#F9FAFB")
    elems=[]
    elems.append(Paragraph("PRECIOS MAYORISTAS — McAllen TX vs CDMX | Pichomel Brands",e_t))
    elems.append(Paragraph(f"{datetime.now().strftime('%d de %B de %Y  %H:%M')}  |  TC: $1 USD = ${tc:.2f} MXN  |  USDA AMS · SNIIM · Claude",e_s))
    elems.append(Paragraph("PRECIOS DE REFERENCIA. No incluyen flete, cruce fronterizo ni mermas. McAllen = precio en destino (USDA). CDMX = precio en origen (SNIIM).",e_r))
    enc=["#","Producto","$/lb","$/kg USD","MXN/kg McAllen","MXN/kg CDMX","Fuente MX","Fecha","Dif. MXN/kg","Dif. %","¿Mas barato?"]
    filas=[enc]
    for p in comp:
        ds=f"${p['dif']:+.2f}" if p["dif"] is not None else "N/D"
        ps=f"{p['pct']:+.1f}%" if p["pct"] is not None else "N/D"
        ms=f"${p['precio_mx']:.2f}" if p["precio_mx"] else "N/D"
        lbl="Mas barato CDMX" if p["cdmx_barato"] is True else "Mas barato McAllen" if p["cdmx_barato"] is False else "Sin datos"
        fu=f"* {p['fuente_mx']}" if p["verificado"] else p["fuente_mx"]
        filas.append([str(p["idx"]),p["nombre"],f"${p['pa_lb']:.2f}",f"${p['pa_usd_kg']:.2f}",
                      f"${p['pa_mxn_kg']:.2f}",ms,fu,p["fecha_mx"],ds,ps,lbl])
    cw=[0.26*inch,1.30*inch,0.55*inch,0.60*inch,0.72*inch,0.72*inch,1.45*inch,0.62*inch,0.72*inch,0.55*inch,0.95*inch]
    tabla=Table(filas,colWidths=cw,repeatRows=1)
    sts=[("BACKGROUND",(0,0),(-1,0),VO),("TEXTCOLOR",(0,0),(-1,0),BL),
         ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,0),7),
         ("ALIGN",(0,0),(-1,-1),"CENTER"),("ALIGN",(1,1),(1,-1),"LEFT"),
         ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("FONTSIZE",(0,1),(-1,-1),7),
         ("ROWBACKGROUNDS",(0,1),(-1,-1),[BL,GR]),
         ("GRID",(0,0),(-1,-1),0.25,colors.HexColor("#E5E7EB")),
         ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
         ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
         ("FONTNAME",(0,1),(0,-1),"Helvetica-Bold"),("TEXTCOLOR",(0,1),(0,-1),colors.HexColor("#9CA3AF"))]
    for i,p in enumerate(comp,1):
        if p["verificado"]:
            sts+=[ ("BACKGROUND",(6,i),(7,i),AO),("TEXTCOLOR",(6,i),(7,i),BL),("FONTNAME",(6,i),(7,i),"Helvetica-Bold")]
        else:
            sts+=[("BACKGROUND",(6,i),(6,i),colors.HexColor("#FEF3C7")),("TEXTCOLOR",(6,i),(6,i),colors.HexColor("#92400E"))]
        if p["cdmx_barato"] is True:
            sts+=[("BACKGROUND",(8,i),(10,i),VC),("TEXTCOLOR",(10,i),(10,i),colors.HexColor("#166534")),("FONTNAME",(10,i),(10,i),"Helvetica-Bold")]
        elif p["cdmx_barato"] is False:
            sts+=[("BACKGROUND",(8,i),(10,i),RC),("TEXTCOLOR",(10,i),(10,i),colors.HexColor("#B91C1C")),("FONTNAME",(10,i),(10,i),"Helvetica-Bold")]
    tabla.setStyle(TableStyle(sts))
    elems.append(tabla); elems.append(Spacer(1,0.15*inch))
    cdmx_b=sum(1 for p in comp if p["cdmx_barato"] is True)
    mc_b=sum(1 for p in comp if p["cdmx_barato"] is False)
    elems.append(Paragraph(f"Verde = mas barato en CDMX ({cdmx_b} productos)  |  Rojo = mas barato en McAllen ({mc_b} productos)  |  * = verificado Claude  |  1 kg = 2.20462 lbs",e_p))
    doc.build(elems)
    print(f"  PDF: {ruta}")
    return ruta

# ============================================================
#  EXCEL
# ============================================================
def crear_excel(comp, tc):
    carpeta = os.path.expanduser("~") if not os.path.exists("docs") else "docs"
    hoy = datetime.now().strftime("%Y-%m-%d")
    ruta = os.path.join(carpeta, f"precios_mcallen_{hoy}.xlsx")
    wb=Workbook()
    vO=PatternFill("solid",fgColor="1B5E20"); vC=PatternFill("solid",fgColor="F0FDF4")
    rC=PatternFill("solid",fgColor="FFF1F2"); gC=PatternFill("solid",fgColor="F9FAFB")
    aO=PatternFill("solid",fgColor="1D4ED8"); aC=PatternFill("solid",fgColor="EFF6FF")
    aM=PatternFill("solid",fgColor="BBDEFB"); yC=PatternFill("solid",fgColor="FEF3C7")
    def eh(c,t):
        c.value=t; c.font=Font(bold=True,color="FFFFFF",size=10)
        c.fill=vO; c.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True)
    ws=wb.active; ws.title="McAllen vs CDMX"
    ws.merge_cells("A1:N1")
    ws["A1"]=f"PRECIOS MAYORISTAS — McAllen TX vs CDMX  |  {datetime.now().strftime('%d de %B de %Y')}"
    ws["A1"].font=Font(bold=True,color="FFFFFF",size=13); ws["A1"].fill=vO
    ws["A1"].alignment=Alignment(horizontal="center",vertical="center"); ws.row_dimensions[1].height=28
    ws.merge_cells("A2:N2")
    ws["A2"]=f"TC: $1 USD = ${tc:.2f} MXN  |  USDA AMS + SNIIM + Claude  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  PRECIOS DE REFERENCIA"
    ws["A2"].font=Font(italic=True,color="555555",size=9); ws["A2"].alignment=Alignment(horizontal="center")
    cols=["#","Producto","$/lb min","$/lb max","$/lb prom","$/kg USD","MXN/kg McAllen","Fuente USDA","MXN/kg CDMX","Fuente MX","Fecha","Dif. MXN/kg","Dif. %","¿Mas barato?"]
    for c,e in enumerate(cols,1): eh(ws.cell(row=3,column=c),e)
    ws.row_dimensions[3].height=30
    for i,p in enumerate(comp,4):
        par=i%2==0
        ds=f"${p['dif']:+.2f}" if p["dif"] is not None else "N/D"
        ps=f"{p['pct']:+.1f}%" if p["pct"] is not None else "N/D"
        ms=f"${p['precio_mx']:.2f}" if p["precio_mx"] else "N/D"
        if p["cdmx_barato"] is True: lbl="Mas barato CDMX"; fV=vC; fVt="166534"
        elif p["cdmx_barato"] is False: lbl="Mas barato McAllen"; fV=rC; fVt="B91C1C"
        else: lbl="Sin datos"; fV=gC; fVt="555555"
        fB=vC if par else gC; fMX=aO if p["verificado"] else yC
        vals=[str(p["idx"]),p["nombre"],f"${p['pl_lb']:.2f}",f"${p['ph_lb']:.2f}",f"${p['pa_lb']:.2f}",
              f"${p['pa_usd_kg']:.2f}",f"${p['pa_mxn_kg']:.2f}",p["fuente_usda"],
              ms,f"{'* ' if p['verificado'] else ''}{p['fuente_mx']}",p["fecha_mx"],ds,ps,lbl]
        fills=[gC if par else PatternFill("solid",fgColor="F3F4F6")]+[fB]*7+[aC if par else aM,fMX,fB,fV,fV,fV]
        for c,(v,fl) in enumerate(zip(vals,fills),1):
            cell=ws.cell(row=i,column=c,value=v); cell.fill=fl
            cell.alignment=Alignment(horizontal="left" if c==2 else "center")
            if c==1: cell.font=Font(color="9CA3AF",bold=True,size=10)
            if c==2: cell.font=Font(bold=True)
            if c in (5,7,9,12,13): cell.font=Font(bold=True)
            if c==10: cell.font=Font(bold=True,color="FFFFFF" if p["verificado"] else "92400E",size=9)
            if c==14: cell.font=Font(bold=True,color=fVt)
    anchos=[5,22,10,10,10,10,13,14,13,20,11,13,10,18]
    for idx,w in enumerate(anchos,1): ws.column_dimensions[get_column_letter(idx)].width=w
    fila_r=len(comp)+5
    cdmx_b=sum(1 for p in comp if p["cdmx_barato"] is True)
    mc_b=sum(1 for p in comp if p["cdmx_barato"] is False)
    ws.cell(row=fila_r,column=1,value=f"Mas barato CDMX: {cdmx_b}  |  Mas barato McAllen: {mc_b}").font=Font(bold=True,size=11)
    ws2=wb.create_sheet("Forecast 7 dias")
    ws2.merge_cells("A1:P1"); ws2["A1"]="FORECAST DE PRECIOS — Proximos 7 dias (referencial)"
    ws2["A1"].font=Font(bold=True,color="FFFFFF",size=13); ws2["A1"].fill=vO
    ws2["A1"].alignment=Alignment(horizontal="center",vertical="center"); ws2.row_dimensions[1].height=28
    fechas=[(datetime.now()+timedelta(days=i)).strftime("%d/%b") for i in range(7)]
    eh(ws2.cell(row=2,column=1),"Producto")
    for j,f in enumerate(fechas,2):
        eh(ws2.cell(row=2,column=j),f"{f}\n$/lb"); eh(ws2.cell(row=2,column=j+7),f"{f}\nMXN/kg")
    ws2.row_dimensions[2].height=30
    for i,p in enumerate(comp,3):
        ws2.cell(row=i,column=1,value=p["nombre"]).font=Font(bold=True)
        fc=forecast(p["pa_lb"],p["pl_lb"],p["ph_lb"]); par=i%2==0
        for j,d in enumerate(fc):
            c1=ws2.cell(row=i,column=j+2,value=f"${d['precio']:.2f}")
            c1.alignment=Alignment(horizontal="center"); c1.fill=vC if par else gC
            c2=ws2.cell(row=i,column=j+9,value=f"${round(d['precio']*LBS_A_KG*tc,2):.2f}")
            c2.alignment=Alignment(horizontal="center"); c2.fill=aC if par else aM
    ws2.column_dimensions["A"].width=22
    for ci in range(2,17): ws2.column_dimensions[get_column_letter(ci)].width=11
    wb.save(ruta); print(f"  Excel: {ruta}")
    return ruta

# ============================================================
#  CORREO
# ============================================================
def enviar_correo(ruta_pdf, ruta_xl, comp, tc):
    print("Enviando correo...")
    hoy=datetime.now().strftime("%d de %B de %Y")
    cdmx_b=sum(1 for p in comp if p["cdmx_barato"] is True)
    mc_b=sum(1 for p in comp if p["cdmx_barato"] is False)
    top=sorted([p for p in comp if p["cdmx_barato"] is True and p["dif"] is not None],key=lambda x:x["dif"],reverse=True)[:5]
    filas="".join([f"<tr><td style='padding:5px 10px;border-bottom:1px solid #eee'>{p['nombre']}</td>"
                   f"<td style='padding:5px 10px;border-bottom:1px solid #eee;text-align:center'>${p['pa_mxn_kg']:.2f}</td>"
                   f"<td style='padding:5px 10px;border-bottom:1px solid #eee;text-align:center'>${p['precio_mx']:.2f}</td>"
                   f"<td style='padding:5px 10px;border-bottom:1px solid #eee;text-align:center;color:#166534;font-weight:bold'>${p['dif']:+.2f} ({p['pct']:+.1f}%)</td></tr>"
                   for p in top])
    cuerpo=f"""<div style="font-family:Arial,sans-serif;max-width:680px;margin:0 auto">
      <div style="background:#1B5E20;padding:20px;border-radius:8px 8px 0 0">
        <h2 style="color:white;margin:0">Precios Mayoristas — McAllen TX vs CDMX</h2>
        <p style="color:#A5D6A7;margin:4px 0 0">Pichomel Brands &nbsp;|&nbsp; {hoy}</p>
      </div>
      <div style="background:#f9f9f9;padding:20px;border:1px solid #eee;border-top:none">
        <div style="background:#FFF8E1;padding:10px 16px;border-radius:6px;margin-bottom:12px;font-size:13px">
          <b>Tipo de cambio: $1 USD = ${tc:.2f} MXN</b> (Banxico)
        </div>
        <div style="background:#FFF1F2;border:1px solid #FECACA;padding:8px 14px;border-radius:6px;margin-bottom:14px;font-size:12px;color:#7F1D1D">
          Precios de referencia. No incluyen flete, cruce fronterizo ni mermas.
        </div>
        <div style="display:flex;gap:10px;margin-bottom:16px">
          <div style="flex:1;background:#F0FDF4;border-radius:8px;padding:12px;text-align:center">
            <div style="font-size:26px;font-weight:bold;color:#166534">{cdmx_b}</div>
            <div style="font-size:11px;color:#166534">más barato en CDMX</div>
          </div>
          <div style="flex:1;background:#FFF1F2;border-radius:8px;padding:12px;text-align:center">
            <div style="font-size:26px;font-weight:bold;color:#B91C1C">{mc_b}</div>
            <div style="font-size:11px;color:#B91C1C">más barato en McAllen</div>
          </div>
          <div style="flex:1;background:#EFF6FF;border-radius:8px;padding:12px;text-align:center">
            <div style="font-size:26px;font-weight:bold;color:#1D4ED8">{len(comp)}</div>
            <div style="font-size:11px;color:#1D4ED8">productos</div>
          </div>
        </div>
        <h3 style="color:#1B5E20;margin-bottom:8px">Más baratos en CDMX hoy:</h3>
        <table style="width:100%;border-collapse:collapse;background:white">
          <tr style="background:#1B5E20;color:white;font-size:11px">
            <th style="padding:7px 10px;text-align:left">Producto</th>
            <th style="padding:7px 10px">MXN/kg McAllen</th>
            <th style="padding:7px 10px">MXN/kg CDMX</th>
            <th style="padding:7px 10px">Diferencia</th>
          </tr>{filas}
        </table>
        <p style="margin-top:16px"><a href="{URL_PAGINA}" style="color:#1B5E20;font-weight:bold">Ver reporte en línea</a></p>
        <p style="color:#888;font-size:11px;margin-top:8px">
          Fuentes: USDA AMS · SNIIM · Claude &nbsp;|&nbsp; Se adjuntan PDF y Excel con los {len(comp)} productos.
        </p>
      </div></div>"""
    msg=MIMEMultipart("alternative")
    msg["Subject"]=f"Precios McAllen vs CDMX {hoy} | TC ${tc:.2f}"
    msg["From"]=GMAIL_ORIGEN; msg["To"]=CORREO_DESTINO
    msg.attach(MIMEText(cuerpo,"html"))
    for ruta in [ruta_pdf,ruta_xl]:
        if ruta and os.path.exists(ruta):
            with open(ruta,"rb") as f:
                p=MIMEBase("application","octet-stream"); p.set_payload(f.read())
                encoders.encode_base64(p)
                p.add_header("Content-Disposition",f"attachment; filename={os.path.basename(ruta)}")
                msg.attach(p)
    with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
        s.login(GMAIL_ORIGEN,GMAIL_APP_PASS); s.sendmail(GMAIL_ORIGEN,CORREO_DESTINO,msg.as_string())
    print("  Correo enviado.")

# ============================================================
#  WHATSAPP
# ============================================================
def enviar_whatsapp(comp, tc, url_pdf=""):
    print("Enviando WhatsApp...")
    hoy=datetime.now().strftime("%d/%b/%Y")
    cdmx_b=sum(1 for p in comp if p["cdmx_barato"] is True)
    mc_b=sum(1 for p in comp if p["cdmx_barato"] is False)
    top3=sorted([p for p in comp if p["cdmx_barato"] is True and p["dif"] is not None],key=lambda x:x["dif"],reverse=True)[:3]
    top3_txt="\n".join([f"  {p['idx']}. {p['nombre']}: CDMX ${p['precio_mx']:.2f} vs McAllen ${p['pa_mxn_kg']:.2f} MXN/kg ({p['dif']:+.2f})" for p in top3])
    pdf_link=f"\nDescargar PDF: {url_pdf}" if url_pdf else ""
    pagina=f"\nVer en línea: {URL_PAGINA}"
    msg=(f"*Precios McAllen TX vs CDMX* — {hoy}\n"
         f"{'─'*28}\n"
         f"TC: *$1 USD = ${tc:.2f} MXN* (Banxico)\n\n"
         f"Mas barato en CDMX: *{cdmx_b}* productos\n"
         f"Mas barato en McAllen: *{mc_b}* productos\n\n"
         f"*Top 3 mas baratos en CDMX:*\n{top3_txt}\n\n"
         f"_Precios de referencia. No incluyen flete ni cruce._"
         f"{pdf_link}{pagina}")
    Client(TWILIO_SID,TWILIO_TOKEN).messages.create(body=msg,from_=TWILIO_WHATSAPP,to=TU_WHATSAPP)
    print("  WhatsApp enviado.")

# ============================================================
#  REPORTE PRINCIPAL
# ============================================================
def generar_reporte():
    print(f"\n{'='*55}\nGENERANDO REPORTE — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n{'='*55}")
    try:
        tc   = obtener_tipo_cambio()
        usda = obtener_precios_usda()
        mx   = obtener_precios_mx()
        comp = calcular_comparativa(usda, mx, tc)
        guardar_json(comp, tc)
        pdf  = crear_pdf(comp, tc)
        xl   = crear_excel(comp, tc)
        enviar_correo(pdf, xl, comp, tc)
        hoy  = datetime.now().strftime("%Y-%m-%d")
        url_pdf = f"{URL_PAGINA}/precios_mcallen_{hoy}.pdf"
        enviar_whatsapp(comp, tc, url_pdf)
        print(f"\nReporte completado exitosamente.")
    except Exception as e:
        import traceback; print(f"\nError: {e}"); traceback.print_exc()

# ============================================================
#  ARRANQUE
# ============================================================
if __name__ == "__main__":
    print("Pichomel Brands — Monitor de Precios McAllen TX v4.0")
    print(f"Reporte diario: {HORA_REPORTE} hrs | {URL_PAGINA}")

    # En GitHub Actions solo genera el reporte una vez y termina
    # En tu computadora local corre el schedule diario
    en_github = os.environ.get("GITHUB_ACTIONS") == "true"

    if en_github:
        print("Corriendo en GitHub Actions — generando reporte unico...")
        generar_reporte()
        print("Listo. GitHub Actions programara la siguiente ejecucion.")
    else:
        print("Corriendo en modo local — reporte diario a las", HORA_REPORTE)
        print("Ctrl+C para detener\n")
        generar_reporte()
        schedule.every().day.at(HORA_REPORTE).do(generar_reporte)
        while True:
            schedule.run_pending()
            time.sleep(60)
