document.addEventListener("DOMContentLoaded", function () {
    const inputNumeros = document.getElementById("id_numeros_favoritos");
    const cantidadURL = new URLSearchParams(window.location.search).get("cantidad");
    const cantidadMaxima = parseInt(cantidadURL || "0");
    const errorContainerId = "error-numeros-favoritos";

    if (!inputNumeros || isNaN(cantidadMaxima) || cantidadMaxima <= 0) {
        return;  // No hacer nada si no hay input o cantidad inválida
    }

    // Crear contenedor de errores si no existe
    if (!document.getElementById(errorContainerId)) {
        const errorDiv = document.createElement("div");
        errorDiv.id = errorContainerId;
        errorDiv.className = "text-danger mt-1";
        inputNumeros.insertAdjacentElement("afterend", errorDiv);
    }

    const errorDiv = document.getElementById(errorContainerId);

    inputNumeros.addEventListener("input", function () {
        const texto = inputNumeros.value;
        let numeros = texto
            .split(",")
            .map(n => n.trim())
            .filter(n => n !== "");

        // Eliminar duplicados
        numeros = [...new Set(numeros)];

        // Validar que todos tengan exactamente 6 dígitos numéricos
        const numerosInvalidos = numeros.filter(n => !/^\d{6}$/.test(n));

        // Cortar si hay más de la cantidad permitida
        if (numeros.length > cantidadMaxima) {
            numeros = numeros.slice(0, cantidadMaxima);
        }

        // Mostrar errores
        if (numerosInvalidos.length > 0) {
            errorDiv.innerText = "Solo se permiten números de 6 dígitos.";
        } else if (texto.split(",").length > cantidadMaxima) {
            errorDiv.innerText = `Solo puedes ingresar hasta ${cantidadMaxima} números.`;
        } else {
            errorDiv.innerText = "";
        }

        // Actualizar el campo con los valores válidos únicos
        inputNumeros.value = numeros.join(", ");
    });
});
