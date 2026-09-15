import { App } from "./App.js?v=5";

document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("app");
  const app = new App(root);
  app.init();
});
