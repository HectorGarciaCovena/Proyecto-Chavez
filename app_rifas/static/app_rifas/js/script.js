// ================= SLIDER HOME =================
document.addEventListener("DOMContentLoaded", function () {
  // Solo inicializar Swiper si existe el contenedor
  const swiperContainer = document.querySelector(".mySwiper");
  if (!swiperContainer) return;

  const swiper = new Swiper(".mySwiper", {
    loop: true,
    autoplay: { delay: 3000, disableOnInteraction: false },
    pagination: { el: ".swiper-pagination", clickable: true },
    navigation: {
      nextEl: ".swiper-button-next",
      prevEl: ".swiper-button-prev",
    },
  });
});
