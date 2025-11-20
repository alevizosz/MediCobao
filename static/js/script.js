// Pequeñas mejoras de UX
document.addEventListener('DOMContentLoaded', () => {
  const inputs = document.querySelectorAll('.underline');
  inputs.forEach(i => {
    i.addEventListener('focus', () => i.parentElement.classList.add('focus'));
    i.addEventListener('blur', () => i.parentElement.classList.remove('focus'));
  });
});