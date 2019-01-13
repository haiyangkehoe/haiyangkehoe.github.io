//Refresh on resize
window.onresize = function() {
  location.reload()
}

window.onscroll = function() {
  stickyNav(); //Sticky navbar
  scrollColor(); //Change background color
}
//Sticky navbar
var navbar = document.querySelector("nav");
var sticky = navbar.offsetTop;
function stickyNav() {
  if (window.pageYOffset >= sticky) {
    navbar.classList.add("sticky");
  } else {
    navbar.classList.remove("sticky");
  }
}
     
//Change background color
var header = document.querySelector("header");
var position = 0.4 * header.offsetHeight;
function scrollColor() {
  if (window.pageYOffset >= position) {
    document.body.classList.add("changeColor");
  } else {
    document.body.classList.remove("changeColor");
  }
}
