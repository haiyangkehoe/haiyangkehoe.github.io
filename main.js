//Execute stickyNav and scrollColor on scroll
var navbar = document.querySelector("nav")
var header = document.querySelector("header");
var sticky = header.offsetHeight;
var position = 0.44 * header.offsetHeight;
window.onresize = function() {
  sticky = header.offsetHeight;
  position = 0.44 * header.offsetHeight;
}
window.onscroll = function() {
  stickyNav(); //Sticky navbar
  scrollColor(); //Change background color
}
//Sticky navbar
function stickyNav() {
  if (window.pageYOffset >= sticky) {
    navbar.classList.add("sticky");
  } else {
    navbar.classList.remove("sticky");
  }
}
//Change background color
function scrollColor() {
  if (window.pageYOffset >= position) {
    document.body.classList.add("changeColor");
  } else {
    document.body.classList.remove("changeColor");
  }
}
