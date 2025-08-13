import streamlit as st
import json
import os
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

INVENTARIO_FILE = "inventario_categorias.json"

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

# Opciones para baldes con sus valores en kilos
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

def grafico_stock(inventario):
    # Crear gráfico barras con stock total por categoría
    categorias = []
    totales = []
    for cat, prods in inventario.items():
        total = sum(prods.values())
        categorias.append(cat)
        totales.append(total)

    fig, ax = plt.subplots()
    ax.bar(categorias, totales, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    ax.set_title("Stock total por categoría")
    ax.set_ylabel("Cantidad")
    st.pyplot(fig)

def empleado_interfaz(inventario):
    st.title("Panel Empleado: Cargar productos")

    tabs = st.tabs(list(inventario.keys()))
    for i, categoria in enumerate(inventario.keys()):
        with tabs[i]:
            productos = inventario[categoria]
            producto_seleccionado = st.selectbox(f"Selecciona un producto de {categoria}", list(productos.keys()))

            # Opción añadir o reemplazar
            modo_actualizacion = st.radio(
                "¿Deseas añadir a la cantidad existente o reemplazarla?",
                ("Añadir", "Reemplazar"),
                key=f"modo_{categoria}_{producto_seleccionado}"
            )

            if categoria == "Por Kilos":
                st.markdown("### Selecciona el estado de hasta 6 valdes:")

                total_kilos = 0.0
                valores_valdes = []

                for n in range(1, 7):
                    opcion = st.selectbox(f"Valde {n}", list(opciones_valde.keys()), key=f"{producto_seleccionado}_valde_{n}")
                    valor = opciones_valde[opcion]
                    valores_valdes.append(valor)
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

    grafico_stock(inventario)

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

def main():
    usuario, rol = login()

    if usuario and rol:
        inventario = cargar_inventario()
        if rol == 'empleado':
            empleado_interfaz(inventario)
        elif rol == 'administrador':
            administrador_interfaz(inventario)
    else:
        st.title("Por favor, ingresa un usuario válido en el panel lateral para continuar.")

if __name__ == "__main__":
    main()
