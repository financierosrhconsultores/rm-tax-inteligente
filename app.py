import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP


# AUTENTICACION RM TAX INTELIGENTE
from supabase import create_client

try:
    supabase = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
except Exception:
    st.error("No se pudo configurar Supabase.")
    st.stop()

if "rm_session" not in st.session_state:
    st.session_state.rm_session = None

if st.session_state.rm_session is not None:
    try:
        sesion = st.session_state.rm_session
        actualizada = supabase.auth.set_session(
            sesion["access_token"],
            sesion["refresh_token"]
        )
        st.session_state.rm_session = {
            "access_token": actualizada.session.access_token,
            "refresh_token": actualizada.session.refresh_token
        }
        usuario = actualizada.user
    except Exception:
        st.session_state.rm_session = None
        usuario = None
else:
    usuario = None

if usuario is None:
    st.title("RM Tax Inteligente")
    st.subheader("Acceso seguro")
    st.caption("RM Consultores Financieros")

    with st.form("formulario_acceso"):
        correo = st.text_input("Correo electronico")
        clave = st.text_input(
            "Contrasena",
            type="password"
        )
        ingresar = st.form_submit_button(
            "Iniciar sesion"
        )

    if ingresar:
        try:
            respuesta = supabase.auth.sign_in_with_password({
                "email": correo.strip(),
                "password": clave
            })
            if respuesta.session:
                st.session_state.rm_session = {
                    "access_token": respuesta.session.access_token,
                    "refresh_token": respuesta.session.refresh_token
                }
                st.rerun()
            else:
                st.error("No se pudo iniciar sesion.")
        except Exception:
            st.error("Credenciales incorrectas o acceso no disponible.")

    st.stop()

with st.sidebar:
    st.caption("Sesion iniciada")
    st.write(usuario.email)
    if st.button("Cerrar sesion"):
        try:
            supabase.auth.sign_out()
        finally:
            st.session_state.rm_session = None
            st.rerun()

# CONSULTAR EMPRESAS AUTORIZADAS
try:
    resultado_empresas = (
        supabase.table("usuarios_empresas")
        .select("empresa_id, rol")
        .eq("usuario_id", usuario.id)
        .execute()
    )

    st.sidebar.divider()
    st.sidebar.subheader("Empresas autorizadas")
    st.sidebar.metric(
        "Empresas asignadas",
        len(st.session_state.rm_empresas)
    )


except Exception as error:
    st.session_state.rm_empresas = []
    st.warning(
        "No se pudieron consultar los permisos de empresas."
    )
    st.error(
        f"Tipo de error: {type(error).__name__}"
    )
    st.code(str(error)[:500])


st.markdown('''<style> [data-testid="stAppViewContainer"]{background:#f5f7fb} [data-testid="stSidebar"]{background:#122741} [data-testid="stSidebar"] *{color:white!important} .block-container{max-width:1200px;padding-top:2rem} h1,h2,h3{color:#142942!important} [data-testid="stMetric"]{background:white;border:1px solid #e2e8f0;border-radius:14px;padding:18px} .hero{background:linear-gradient(115deg,#122741,#24537a);border-radius:18px;padding:30px;color:white;margin-bottom:20px}.hero h1{color:white!important;margin:0}.hero p{color:#d5e1ef} </style>''',unsafe_allow_html=True)
with st.sidebar:
    st.markdown('## ◈ RM TAX')
    st.caption('INTELIGENTE · EL SALVADOR')
    st.divider()
    menu=st.radio('Menú',['🏠 Inicio','🧮 Simulador IVA','🏢 Empresas','📅 Obligaciones','📁 Importar CSV','ℹ️ Información'],label_visibility='collapsed')
    st.divider()
    st.caption('VERSIÓN 1.1 · DEMOSTRACIÓN')
st.markdown('<div class="hero"><h1>RM Tax Inteligente</h1><p>RM Consultores Financieros · Plataforma tributaria para El Salvador</p></div>',unsafe_allow_html=True)
st.warning('Versión demostrativa. Utiliza únicamente datos ficticios. No presenta declaraciones oficiales ni guarda registros.')
def money(x):return Decimal(str(x)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
if menu=='🏠 Inicio':
    st.subheader('Panel de control')
    a,b,c=st.columns(3)
    a.metric('Empresas demo','2');b.metric('Obligaciones demo','3');c.metric('Alertas demo','1')
    st.info('Explora los módulos desde el menú lateral. Los indicadores son ilustrativos.')
elif menu=='🧮 Simulador IVA':
    st.subheader('Simulador mensual de IVA')
    a,b=st.columns(2)
    with a:
        sales=st.number_input('Ventas gravadas sin IVA ($)',min_value=0.0,step=100.0)
        buys=st.number_input('Compras con crédito fiscal admisible sin IVA ($)',min_value=0.0,step=100.0)
    with b:carry=st.number_input('Remanente anterior ($)',min_value=0.0,step=10.0)
    debit=(money(sales)*Decimal('.13')).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    credit=(money(buys)*Decimal('.13')).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    net=debit-credit-money(carry)
    a,b,c=st.columns(3)
    a.metric('Débito fiscal',f'$ {debit:,.2f}');b.metric('Crédito fiscal',f'$ {credit:,.2f}');c.metric('Saldo neto estimado',f'$ {net:,.2f}')
    st.info('Saldo estimado por pagar' if net>0 else 'Remanente estimado' if net<0 else 'Saldo cero')
    rows=pd.DataFrame([{'Concepto':'Débito fiscal','USD':str(debit)},{'Concepto':'Crédito fiscal','USD':str(credit)},{'Concepto':'Remanente anterior','USD':str(money(carry))},{'Concepto':'Resultado estimado','USD':str(net)}])
    st.download_button('Descargar cálculo CSV',rows.to_csv(index=False).encode('utf-8-sig'),'rm_tax_iva.csv','text/csv')
    st.caption('Cálculo simplificado al 13 %, sin ajustes, retenciones, percepciones ni operaciones especiales. No sustituye F-07.')
elif menu=='🏢 Empresas':
    st.subheader('Directorio de empresas · Ejemplo')
    st.dataframe(pd.DataFrame([{'Empresa':'Empresa Demo A','Giro':'Comercio','Estado':'Activa'},{'Empresa':'Empresa Demo B','Giro':'Servicios','Estado':'Activa'}]),hide_index=True,use_container_width=True)
elif menu=='📅 Obligaciones':
    st.subheader('Obligaciones · Ejemplo')
    st.dataframe(pd.DataFrame([{'Empresa':'Empresa Demo A','Formulario':'F-07','Estado':'Pendiente (ejemplo)'},{'Empresa':'Empresa Demo A','Formulario':'F-14','Estado':'Presentado (ejemplo)'},{'Empresa':'Empresa Demo B','Formulario':'F-07','Estado':'En revisión (ejemplo)'}]),hide_index=True,use_container_width=True)
    st.caption('Sin fechas oficiales ni integración con Hacienda.')
elif menu=='📁 Importar CSV':
    st.subheader('Previsualizar archivo CSV ficticio')
    uploaded=st.file_uploader('Archivo CSV (máximo 2 MB)',type=['csv'])
    if uploaded:
        if uploaded.size>2*1024*1024:st.error('Archivo demasiado grande.')
        else:
            try:st.dataframe(pd.read_csv(uploaded,nrows=100).head(30),use_container_width=True)
            except Exception:st.error('No se pudo leer el archivo CSV.')
    st.caption('No cargues datos reales. La importación no valida documentos fiscales.')
else:
    st.subheader('Acerca del sistema')
    st.write('RM Tax Inteligente es un prototipo para validaciones tributarias y gestión contable futura.')
    st.write('Próximos módulos: autenticación, base de datos segura, gestión multiempresa, anexos y validaciones fiscales.')
st.divider();st.caption('© RM Consultores Financieros · Demostración 1.1')



