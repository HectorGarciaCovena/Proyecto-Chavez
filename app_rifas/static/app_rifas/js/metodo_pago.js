document.addEventListener("DOMContentLoaded", function () {
    const metodoBtns = document.querySelectorAll(".metodo-btn");
    const metodoPagoInput = document.getElementById("metodo_pago");
    const form = document.querySelector("form");

    if (!metodoBtns.length || !metodoPagoInput || !form) {
        return;
    }

    // Manejo visual de selección de método
    metodoBtns.forEach((btn) => {
        btn.addEventListener("click", function () {
            // Remover activo de todos
            metodoBtns.forEach((b) => b.classList.remove("active"));
            this.classList.add("active");

            // Guardar método seleccionado
            metodoPagoInput.value = this.dataset.metodo;
        });
    });
});
