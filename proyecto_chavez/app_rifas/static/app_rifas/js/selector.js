document.addEventListener('DOMContentLoaded', function () {
    const botones = document.querySelectorAll('.numero-box.disponible');
    const confirmarBtn = document.getElementById('confirmarSeleccion');
    const contador = document.getElementById('contador');

    let seleccionados = [];

    function actualizarUI() {
        botones.forEach(btn => {
            const numero = btn.dataset.numero;
            if (seleccionados.includes(numero)) {
                btn.classList.add('seleccionado');
            } else {
                btn.classList.remove('seleccionado');
            }
        });

        contador.textContent = `${seleccionados.length}/${CANTIDAD_OBJETIVO} seleccionados`;
        confirmarBtn.disabled = seleccionados.length !== CANTIDAD_OBJETIVO;
    }

    botones.forEach(btn => {
        btn.addEventListener('click', () => {
            const numero = btn.dataset.numero;

            if (seleccionados.includes(numero)) {
                seleccionados = seleccionados.filter(n => n !== numero);
            } else {
                if (seleccionados.length < CANTIDAD_OBJETIVO) {
                    seleccionados.push(numero);
                }
            }

            actualizarUI();
        });
    });

    confirmarBtn.addEventListener('click', () => {
        if (seleccionados.length === CANTIDAD_OBJETIVO) {
            localStorage.setItem('numeros_seleccionados', seleccionados.join(','));
            window.close(); // Cierra la ventana/pestaña del selector
        } else {
            alert(`Debes seleccionar exactamente ${CANTIDAD_OBJETIVO} número(s).`);
        }
    });

    // Inicial
    actualizarUI();
});

