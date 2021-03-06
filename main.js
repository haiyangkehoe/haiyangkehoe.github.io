//Execute stickyNav and scrollColor on scroll
var navbar = document.querySelector("nav")
var header = document.querySelector("header");

window.onscroll = function() {
  stickyNav(); //Sticky navbar
  scrollColor(); //Change background color
}

//Sticky navbar
function stickyNav() {
  if (window.pageYOffset >= header.offsetHeight) {
    navbar.classList.add("sticky");
  } else {
    navbar.classList.remove("sticky");
  }
}

//Change background color
function scrollColor() {
  if (window.pageYOffset >= 0.44 * header.offsetHeight) {
    document.body.classList.add("changeColor");
  } else {
    document.body.classList.remove("changeColor");
  }
}
