document.addEventListener('DOMContentLoaded', function () {
    const gridNumeros = document.getElementById('gridNumeros');
    const confirmarBtn = document.getElementById('confirmarSeleccionBtn');
    const contador = document.getElementById('contadorSeleccion');

    const numeroMin = parseInt(gridNumeros.dataset.min);
    const numeroMax = parseInt(gridNumeros.dataset.max);
    const cantidadMaxima = parseInt(gridNumeros.dataset.cantidad);
    const vendidos = JSON.parse(gridNumeros.dataset.vendidos.replace(/'/g, '"'));

    // 🧹 1. Limpiar localStorage si venimos desde el home
    if (document.referrer.includes('/home') || document.referrer === window.location.origin + '/') {
        localStorage.removeItem('numeros_seleccionados');
    }

    let seleccionados = [];

    // 🔄 2. Cargar selección previa (si existe)
    const seleccionPrevia = localStorage.getItem('numeros_seleccionados');
    if (seleccionPrevia) {
        seleccionados = seleccionPrevia.split(',').map(n => n.trim()).filter(Boolean);
    }

    // 🧩 3. Renderizar el grid de números
    for (let i = numeroMin; i <= numeroMax; i++) {
        const numero = i.toString().padStart(5, '0');
        const btn = document.createElement('button');
        btn.className = 'numero-btn';
        btn.textContent = numero;
        btn.dataset.numero = numero;

        if (vendidos.includes(i)) {
            btn.classList.add('vendido');
            btn.disabled = true;
        } else if (seleccionados.includes(numero)) {
            btn.classList.add('seleccionado');
        }

        btn.addEventListener('click', () => {
            const index = seleccionados.indexOf(numero);

            if (index > -1) {
                seleccionados.splice(index, 1);
                btn.classList.remove('seleccionado');
            } else {
                if (seleccionados.length < cantidadMaxima) {
                    seleccionados.push(numero);
                    btn.classList.add('seleccionado');
                }
            }

            actualizarContadorYBoton();
        });

        gridNumeros.appendChild(btn);
    }

    function actualizarContadorYBoton() {
        contador.textContent = `${seleccionados.length}/${cantidadMaxima} seleccionados`;
        confirmarBtn.disabled = seleccionados.length !== cantidadMaxima;
    }

    // 4. Confirmar selección y guardar en localStorage
    confirmarBtn.addEventListener('click', () => {
        localStorage.setItem('numeros_seleccionados', seleccionados.join(','));
        window.close();  // Cierra esta pestaña
    });

    // Inicial
    actualizarContadorYBoton();
});



