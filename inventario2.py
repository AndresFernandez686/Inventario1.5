import streamlit as st
import json
import os
import pandas as pd
from io import BytesIO
from datetime import date

INVENTARIO_FILE = "inventario_categorias.json"
HISTORIAL_FILE = "historial_inventario.csv"

productos_por_categoria = {
    "Impulsivo": {
        "Galletas": 0,
        "Chicles": 0,
        "Snack Salado": 0
    },
    "Por Kilos": {
        "Helado Vainilla": 0.0,
        "Helado Chocolate": 0.0,
        "Helado Fresa": 0.0
    },
    "Extras": {
        "Vasos": 0,
        "Cucharas": 0,
        "Servilletas": 0
    }
}

usuarios = {
    'empleado1': 'empleado',
    'admin1': 'administrador'
}

opciones_valde = {
    "Vacío": 0.0,
    "Casi lleno": 0.3,
    "Medio lleno": 0.5,
    "Valde lleno": 1.0
}

def cargar_inventario():
    if os.path.exists(INVENTARIO_FILE):
        with open(INVENTARIO_FILE, "r") as f:
            return json.load(f)
    else:
        return productos_por_categoria.copy()

def guardar_inventario(inventario):
    with open(INVENTARIO_FILE, "w") as f:
        json.dump(inventario, f)

def guardar_historial(fecha, usuario, categoria, producto, cantidad):
    nuevo_registro = pd.DataFrame([{
        "Fecha": fecha,
        "Usuario": usuario,
        "Categoría": categoria,
        "Producto": producto,
        "Cantidad": cantidad
    }])
    if os.path.exists(HISTORIAL_FILE):
        historial = pd.read_csv(HISTORIAL_FILE)
        historial = pd.concat([historial, nuevo_registro], ignore_index=True)
    else:
        historial = nuevo_registro
    historial.to_csv(HISTORIAL_FILE, index=False)

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        return pd.read_csv(HISTORIAL_FILE)
    return pd.DataFrame(columns=["Fecha", "Usuario", "Categoría", "Producto", "Cantidad"])

def login():
    st.sidebar.title("Inicio de sesión")
    usuario = st.sidebar.text_input("Usuario")
    if usuario in usuarios:
        st.sidebar.success(f"Hola {usuario}, rol: {usuarios[usuario]}")
        return usuario, usuarios[usuario]
    elif usuario:
        st.sidebar.error("Usuario no reconocido")
    return None, None

def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def empleado_interfaz(inventario, usuario):
    st.title("Panel Empleado: Cargar productos")

    fecha_carga = st.date_input("Selecciona la fecha de carga", value=date.today())

    tabs = st.tabs(list(inventario.keys()))
    for i, categoria in enumerate(inventario.keys()):
        with tabs[i]:
            productos = inventario[categoria]
            producto_seleccionado = st.selectbox(f"Selecciona un producto de {categoria}", list(productos.keys()))

            modo_actualizacion = st.radio(
                "¿Deseas añadir a la cantidad existente o reemplazarla?",
                ("Añadir", "Reemplazar"),
                key=f"modo_{categoria}_{producto_seleccionado}"
            )

            if categoria == "Por Kilos":
                st.markdown("### Selecciona el estado de hasta 6 valdes:")

                total_kilos = 0.0

                for n in range(1, 7):
                    opcion = st.selectbox(f"Valde {n}", list(opciones_valde.keys()), key=f"{producto_seleccionado}_valde_{n}")
                    valor = opciones_valde[opcion]
                    total_kilos += valor

                if st.button(f"Actualizar stock en {categoria} para {producto_seleccionado}", key=f"{categoria}_{producto_seleccionado}_btn"):
                    if total_kilos < 0:
                        st.warning("La cantidad no puede ser negativa.")
                    else:
                        if modo_actualizacion == "Añadir":
                            productos[producto_seleccionado] += total_kilos
                        else:
                            productos[producto_seleccionado] = total_kilos
                        guardar_inventario(inventario)
                        guardar_historial(fecha_carga, usuario, categoria, producto_seleccionado, total_kilos)
                        st.success(f"Stock actualizado para {producto_seleccionado} en {categoria}. Nuevo stock: {productos[producto_seleccionado]:.2f} kilos")

                st.write(f"Inventario en categoría {categoria}:")
                for p, c in productos.items():
                    texto = f"{c:.2f} kilos" if c > 0 else "Vacío"
                    st.write(f"- {p}: {texto}")

            else:
                cantidad = st.number_input("Cantidad", min_value=0, step=1, key=f"{categoria}_cant_{producto_seleccionado}")
                if st.button(f"Actualizar stock en {categoria} para {producto_seleccionado}", key=f"{categoria}_{producto_seleccionado}_btn"):
                    if cantidad < 0:
                        st.warning("La cantidad no puede ser negativa.")
                    else:
                        if modo_actualizacion == "Añadir":
                            productos[producto_seleccionado] += cantidad
                        else:
                            productos[producto_seleccionado] = cantidad
                        guardar_inventario(inventario)
                        guardar_historial(fecha_carga, usuario, categoria, producto_seleccionado, cantidad)
                        st.success(f"Stock actualizado para {producto_seleccionado} en {categoria}. Nuevo stock: {productos[producto_seleccionado]}")

                st.write(f"Inventario en categoría {categoria}:")
                for p, c in productos.items():
                    texto = str(c) if c > 0 else "Vacío"
                    st.write(f"- {p}: {texto}")

def administrador_interfaz(inventario):
    st.title("Panel Administrador: Inventario total por categoría")

    total_general = 0
    for categoria, productos in inventario.items():
        st.subheader(f"Categoría: {categoria}")
        total_categoria = sum(productos.values())
        total_general += total_categoria
        for p, c in productos.items():
            if categoria == "Por Kilos":
                texto = f"{c:.2f} kilos" if c > 0 else "Vacío"
                st.write(f"- {p}: {texto}")
            else:
                texto = str(c) if c > 0 else "Vacío"
                st.write(f"- {p}: {texto}")
        if categoria == "Por Kilos":
            st.markdown(f"**Total en {categoria}: {total_categoria:.2f} kilos**")
        else:
            st.markdown(f"**Total en {categoria}: {total_categoria}**")

    st.markdown(f"## Total general en la heladería: {total_general:.2f}")

    st.markdown("---")
    st.subheader("Descargar inventarios por categoría")

    for categoria, productos in inventario.items():
        df = pd.DataFrame({
            "Producto": list(productos.keys()),
            "Cantidad": list(productos.values())
        })
        excel_bytes = to_excel_bytes(df)
        st.download_button(
            label=f"Descargar Excel de {categoria}",
            data=excel_bytes,
            file_name=f"inventario_{categoria.lower().replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.markdown("---")
    st.subheader("📅 Historial de cargas")
    historial = cargar_historial()
    if not historial.empty:
        año = st.number_input("Año", min_value=2000, max_value=2100, value=date.today().year)
        mes = st.number_input("Mes", min_value=1, max_value=12, value=date.today().month)
        historial["Fecha"] = pd.to_datetime(historial["Fecha"])
        filtro = historial[(historial["Fecha"].dt.year == año) & (historial["Fecha"].dt.month == mes)]
        if not filtro.empty:
            st.dataframe(filtro)
        else:
            st.warning("No hay registros para ese mes.")
    else:
        st.info("Aún no hay registros en el historial.")

def main():
    usuario, rol = login()
    if usuario and rol:
        inventario = cargar_inventario()
        if rol == 'empleado':
            empleado_interfaz(inventario, usuario)
        elif rol == 'administrador':
            administrador_interfaz(inventario)
    else:
        st.title("Por favor, ingresa un usuario válido en el panel lateral para continuar.")

if __name__ == "__main__":
    main()
